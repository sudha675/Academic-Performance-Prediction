from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Student Performance System")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("dataset", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# ==========================================
# EMAIL FUNCTION
# ==========================================

def send_email(to_email: str, subject: str, message: str) -> bool:
    """Send email alert"""
    sender = "sudharaju6143@gmail.com"  # Change this
    password = "oqjdslcxveqyilwz"  # Change this to your App Password
    
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"📧 Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Email failed for {to_email}: {str(e)}")
        return False


# ==========================================
# DATA CLEANING FUNCTION
# ==========================================

def clean_data():
    """Clean and merge student data from multiple CSV files"""
    dataset_path = UPLOAD_FOLDER
    
    try:
        logger.info("Starting data cleaning...")
        
        # Load data
        students = pd.read_csv(os.path.join(dataset_path, "students.csv"))
        attendance = pd.read_csv(os.path.join(dataset_path, "attendance.csv"))
        homework = pd.read_csv(os.path.join(dataset_path, "homework.csv"))
        performance = pd.read_csv(os.path.join(dataset_path, "performance.csv"))
        
        logger.info("✅ All CSV files loaded successfully")
        
        # =========================
        # RENAME ID COLUMN
        # =========================
        students.rename(columns={"Student_ID": "student_id"}, inplace=True)
        attendance.rename(columns={"Student_ID": "student_id"}, inplace=True)
        homework.rename(columns={"Student_ID": "student_id"}, inplace=True)
        performance.rename(columns={"Student_ID": "student_id"}, inplace=True)
        
        # =========================
        # CLEAN ATTENDANCE
        # =========================
        attendance["Attendance_Score"] = attendance["Attendance_Status"].astype(str).str.lower().map(
            {"present": 1, "absent": 0}
        )
        
        attendance_clean = (
            attendance.groupby("student_id")["Attendance_Score"]
            .mean()
            .reset_index()
        )
        
        # =========================
        # CLEAN HOMEWORK
        # =========================
        homework["Homework_Score"] = homework["Status"].astype(str).str.lower().map(
            {"submitted": 1, "completed": 1, "not submitted": 0}
        )
        
        homework_clean = (
            homework.groupby("student_id")["Homework_Score"]
            .mean()
            .reset_index()
        )
        
        # =========================
        # CLEAN PERFORMANCE
        # =========================
        performance["Exam_Score"] = pd.to_numeric(
            performance["Exam_Score"], errors="coerce"
        )
        
        performance_clean = performance[["student_id", "Exam_Score"]]
        
        # =========================
        # MERGE CLEAN DATA
        # =========================
        df = students.merge(attendance_clean, on="student_id", how="left")
        df = df.merge(homework_clean, on="student_id", how="left")
        df = df.merge(performance_clean, on="student_id", how="left")
        
        # =========================
        # HANDLE MISSING VALUES
        # =========================
        df["Attendance_Score"] = df["Attendance_Score"].fillna(df["Attendance_Score"].mean())
        df["Homework_Score"] = df["Homework_Score"].fillna(df["Homework_Score"].mean())
        df["Exam_Score"] = df["Exam_Score"].fillna(df["Exam_Score"].mean())
        
        # =========================
        # SAVE CLEAN DATASET
        # =========================
        df.to_csv("dataset/cleaned_students.csv", index=False)
        
        logger.info("✅ Dataset cleaned and saved successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cleaning data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# PERFORMANCE PROCESSING FUNCTION
# ==========================================

def process_performance():
    """Main processing function to send alerts to students and teachers"""
    try:
        logger.info("Starting performance processing...")
        
        # =====================================
        # LOAD DATA
        # =====================================
        dataset_path = UPLOAD_FOLDER
        
        students = pd.read_csv(os.path.join(dataset_path, "students.csv"))
        attendance = pd.read_csv(os.path.join(dataset_path, "attendance.csv"))
        homework = pd.read_csv(os.path.join(dataset_path, "homework.csv"))
        performance = pd.read_csv(os.path.join(dataset_path, "performance.csv"))
        
        try:
            teachers = pd.read_csv(os.path.join(dataset_path, "subject_teacher.csv"), encoding="latin1")
        except FileNotFoundError:
            logger.warning("subject_teacher.csv not found. Skipping teacher emails.")
            teachers = None
        
        # =====================================
        # FIX COLUMN NAMES
        # =====================================
        students.rename(columns={"Student_ID": "student_id"}, inplace=True)
        attendance.rename(columns={"Student_ID": "student_id"}, inplace=True)
        homework.rename(columns={"Student_ID": "student_id"}, inplace=True)
        performance.rename(columns={"Student_ID": "student_id"}, inplace=True)
        
        if teachers is not None:
            teachers.columns = teachers.columns.str.strip()
            teachers.rename(columns={
                "Teacher_name": "Teacher_name",
                "Suject_Teaching": "Subject",
                "Email_id": "Email_id"
            }, inplace=True)
        
        # =====================================
        # ATTENDANCE SCORE
        # =====================================
        attendance["Attendance_Score"] = attendance["Attendance_Status"].astype(str).str.lower().map(
            {"present": 1, "absent": 0}
        )
        
        attendance = attendance.groupby(
            ["student_id", "Subject"]
        )["Attendance_Score"].mean().reset_index()
        
        # =====================================
        # HOMEWORK SCORE
        # =====================================
        homework["Homework_Score"] = homework["Status"].astype(str).str.lower().map(
            {"submitted": 1, "completed": 1, "not submitted": 0}
        )
        
        homework = homework.groupby(
            ["student_id", "Subject"]
        )["Homework_Score"].mean().reset_index()
        
        # =====================================
        # MERGE ALL DATA
        # =====================================
        df = attendance.merge(homework, on=["student_id", "Subject"], how="inner")
        df = df.merge(performance, on=["student_id", "Subject"], how="inner")
        df = df.merge(students, on="student_id", how="inner")
        
        if teachers is not None:
            df = df.merge(teachers, on="Subject", how="left")
        
        # =====================================
        # FINAL SCORE CALCULATION
        # =====================================
        df["Final_Score"] = (
            0.3 * df["Attendance_Score"] +
            0.3 * df["Homework_Score"] +
            0.4 * df["Exam_Score"]
        )
        
        # =====================================
        # CLASSIFICATION
        # =====================================
        def classify(score):
            if score >= 75:
                return "Good"
            elif score >= 33:
                return "Average"
            else:
                return "Weak"
        
        df["Status"] = df["Final_Score"].apply(classify)
        
        # =====================================
        # SEND EMAIL TO WEAK STUDENTS
        # =====================================
        weak_students = df[df["Status"] == "Weak"]
        
        if len(weak_students) > 0:
            logger.info(f"Sending emails to {len(weak_students)} weak students...")
            for _, row in weak_students.iterrows():
                student_email = row.get("email_id") or row.get("Email_id")
                student_name = row.get("Full_Name") or row.get("Student_Name") or "Student"
                
                student_msg = f"""
Dear {student_name},

You are weak in the subject: {row['Subject']}

Attendance : {row['Attendance_Score']:.2f}
Homework   : {row['Homework_Score']:.2f}
Exam Score : {row['Exam_Score']:.2f}
Final Score: {row['Final_Score']:.2f}

Please improve your performance.

Regards,
Academic Performance Monitoring System
"""
                
                if student_email:
                    send_email(
                        to_email=student_email,
                        subject=f"Performance Alert – {row['Subject']}",
                        message=student_msg
                    )
        
        # =====================================
        # SEND ONE EMAIL PER TEACHER
        # =====================================
        if teachers is not None and len(weak_students) > 0:
            logger.info(f"Sending emails to teachers...")
            grouped = weak_students.groupby("Subject")
            
            for subject, group in grouped:
                if "Email_id" in group.columns:
                    teacher_emails = group["Email_id"]
                    teacher_names = group.get("Teacher_name", None)
                    
                    if len(teacher_emails) > 0:
                        teacher_email = teacher_emails.iloc[0]
                        teacher_name = teacher_names.iloc[0] if teacher_names is not None else "Teacher"
                        
                        message = f"""
Dear {teacher_name},

The following students are weak in your subject: {subject}

----------------------------------------
"""
                        
                        for _, row in group.iterrows():
                            message += f"""
Student Name : {row.get('Full_Name') or row.get('Student_Name') or 'N/A'}
Student ID   : {row['student_id']}
Final Score  : {row['Final_Score']:.2f}
----------------------------------------
"""
                        
                        message += """
Please take necessary academic action.

Regards,
Academic Performance Monitoring System
"""
                        
                        send_email(
                            to_email=teacher_email,
                            subject=f"Weak Students Report – {subject}",
                            message=message
                        )
        
        logger.info("✅ Student & Teacher emails sent successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in performance processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# FASTAPI ROUTES
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the upload page"""
    try:
        # FIX: Add encoding='utf-8' to handle special characters
        with open("templates/upload.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("upload.html not found, serving fallback HTML")
        return """
        <html>
            <head>
                <title>Student Performance Upload</title>
                <style>
                    body { font-family: Arial; margin: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }
                    h1 { color: #667eea; text-align: center; }
                    form { background: #f5f5f5; padding: 20px; border-radius: 8px; }
                    input, button { padding: 10px; margin: 10px 0; width: 100%; }
                    button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; cursor: pointer; border-radius: 4px; font-weight: bold; }
                    button:hover { opacity: 0.9; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 Student Performance System</h1>
                    <form action="/upload" method="post" enctype="multipart/form-data">
                        <label><strong>Upload CSV Files:</strong></label><br>
                        <input type="file" name="files" multiple accept=".csv" required>
                        <button type="submit">Upload & Process</button>
                    </form>
                </div>
            </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error reading HTML file: {str(e)}")
        return f"<h1>Error: {str(e)}</h1>"


@app.post("/upload")
async def upload(files: list[UploadFile] = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """Upload CSV files and trigger processing"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        logger.info(f"Received {len(files)} files for upload")
        
        # Save uploaded files
        for file in files:
            if not file.filename.endswith('.csv'):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Only CSV files allowed. Got: {file.filename}"
                )
            
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            contents = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            logger.info(f"Saved file: {file.filename}")
        
        # Add background task to process data and send emails
        background_tasks.add_task(process_data_and_emails)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "✅ Files uploaded successfully. Processing in background...",
                "files_count": len(files)
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Student Performance System"}


@app.get("/status")
async def get_status():
    """Get current processing status"""
    try:
        cleaned_file = "dataset/cleaned_students.csv"
        if os.path.exists(cleaned_file):
            return {
                "status": "processed",
                "cleaned_data": cleaned_file,
                "file_size": os.path.getsize(cleaned_file)
            }
        else:
            return {"status": "no_data_yet"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# BACKGROUND TASK
# ==========================================

def process_data_and_emails():
    """Background task to clean data and process performance"""
    try:
        logger.info("Starting background processing...")
        
        # Clean data first
        if clean_data():
            logger.info("Data cleaned successfully")
            
            # Process performance and send emails
            if process_performance():
                logger.info("Performance processing completed")
            else:
                logger.error("Performance processing failed")
        else:
            logger.error("Data cleaning failed")
            
    except Exception as e:
        logger.error(f"Background task error: {str(e)}")
        import traceback
        traceback.print_exc()


# ==========================================
# STARTUP & SHUTDOWN EVENTS
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Student Performance System started")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Dataset folder: dataset")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Student Performance System shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)