import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def clean_data():
    """Clean and merge student data from multiple CSV files"""
    dataset_path = "uploads"
    
    # Define expected files
    required_files = {
        'students': 'students.csv',
        'attendance': 'attendance.csv',
        'homework': 'homework.csv',
        'performance': 'performance.csv'
    }
    
    # Check if files exist
    for file_name in required_files.values():
        file_path = os.path.join(dataset_path, file_name)
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Warning: {file_name} not found in {dataset_path}")
    
    try:
        # Load data
        students = pd.read_csv(os.path.join(dataset_path, required_files['students']))
        attendance = pd.read_csv(os.path.join(dataset_path, required_files['attendance']))
        homework = pd.read_csv(os.path.join(dataset_path, required_files['homework']))
        performance = pd.read_csv(os.path.join(dataset_path, required_files['performance']))
        
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
        
        logger.info("✅ Attendance data cleaned")
        
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
        
        logger.info("✅ Homework data cleaned")
        
        # =========================
        # CLEAN PERFORMANCE
        # =========================
        performance["Exam_Score"] = pd.to_numeric(
            performance["Exam_Score"], errors="coerce"
        )
        
        performance_clean = performance[["student_id", "Exam_Score"]]
        
        logger.info("✅ Performance data cleaned")
        
        # =========================
        # MERGE CLEAN DATA
        # =========================
        df = students.merge(attendance_clean, on="student_id", how="left")
        df = df.merge(homework_clean, on="student_id", how="left")
        df = df.merge(performance_clean, on="student_id", how="left")
        
        logger.info("✅ Data merged successfully")
        
        # =========================
        # HANDLE MISSING VALUES
        # =========================
        df["Attendance_Score"] = df["Attendance_Score"].fillna(df["Attendance_Score"].mean())
        df["Homework_Score"] = df["Homework_Score"].fillna(df["Homework_Score"].mean())
        df["Exam_Score"] = df["Exam_Score"].fillna(df["Exam_Score"].mean())
        
        logger.info("✅ Missing values handled")
        
        # Create output directory if needed
        os.makedirs("dataset", exist_ok=True)
        
        # =========================
        # SAVE CLEAN DATASET
        # =========================
        df.to_csv("dataset/cleaned_students.csv", index=False)
        
        logger.info("✅ Dataset cleaned and saved successfully!")
        logger.info("📁 Saved as: dataset/cleaned_students.csv")
        return True
        
    except FileNotFoundError as fe:
        logger.error(f"❌ File not found: {str(fe)}")
        return False
    except Exception as e:
        logger.error(f"❌ Error cleaning data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False