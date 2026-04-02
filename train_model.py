import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import pickle
import os
import logging

logger = logging.getLogger(__name__)

def train_model():
    """Train ML model for student performance classification"""
    try:
        dataset_path = "uploads"
        
        # Load data
        students = pd.read_csv(os.path.join(dataset_path, "students.csv"))
        attendance = pd.read_csv(os.path.join(dataset_path, "attendance.csv"))
        homework = pd.read_csv(os.path.join(dataset_path, "homework.csv"))
        performance = pd.read_csv(os.path.join(dataset_path, "performance.csv"))
        
        logger.info("✅ Data loaded for model training")
        
        # Rename ID column
        students.rename(columns={"Student_ID": "student_id"}, inplace=True)
        attendance.rename(columns={"Student_ID": "student_id"}, inplace=True)
        homework.rename(columns={"Student_ID": "student_id"}, inplace=True)
        performance.rename(columns={"Student_ID": "student_id"}, inplace=True)
        
        # Create models directory
        os.makedirs("models", exist_ok=True)
        
        # -------------------------------
        # PROCESS ATTENDANCE
        # -------------------------------
        attendance["Attendance_Score"] = attendance["Attendance_Status"].apply(
            lambda x: 1 if str(x).lower() == "present" else 0
        )
        
        attendance_summary = attendance.groupby("student_id")["Attendance_Score"].mean() * 100
        attendance_summary = attendance_summary.reset_index()
        attendance_summary.columns = ["student_id", "Attendance_Score"]
        
        # -------------------------------
        # PROCESS HOMEWORK
        # -------------------------------
        homework["Homework_Score"] = homework["Status"].apply(
            lambda x: 1 if str(x).lower() in ["submitted", "completed"] else 0
        )
        
        homework_summary = homework.groupby("student_id")["Homework_Score"].mean() * 100
        homework_summary = homework_summary.reset_index()
        homework_summary.columns = ["student_id", "Homework_Score"]
        
        # -------------------------------
        # PERFORMANCE
        # -------------------------------
        performance_summary = performance[["student_id", "Exam_Score"]].copy()
        performance_summary["Exam_Score"] = pd.to_numeric(
            performance_summary["Exam_Score"], errors="coerce"
        )
        
        # -------------------------------
        # MERGE ALL
        # -------------------------------
        df = students.merge(attendance_summary, on="student_id", how="left")
        df = df.merge(homework_summary, on="student_id", how="left")
        df = df.merge(performance_summary, on="student_id", how="left")
        
        # Fill missing values
        df["Attendance_Score"] = df["Attendance_Score"].fillna(df["Attendance_Score"].mean())
        df["Homework_Score"] = df["Homework_Score"].fillna(df["Homework_Score"].mean())
        df["Exam_Score"] = df["Exam_Score"].fillna(df["Exam_Score"].mean())
        
        logger.info("✅ Data preprocessed")
        
        # -------------------------------
        # FINAL SCORE
        # -------------------------------
        df["final_score"] = (
            0.3 * df["Attendance_Score"] +
            0.3 * df["Homework_Score"] +
            0.4 * df["Exam_Score"]
        )
        
        def label(score):
            if score >= 75:
                return "Good"
            elif score >= 50:
                return "Average"
            else:
                return "At Risk"
        
        df["result"] = df["final_score"].apply(label)
        
        # Remove rows with NaN values
        df_clean = df.dropna(subset=["Attendance_Score", "Homework_Score", "Exam_Score"])
        
        if len(df_clean) == 0:
            logger.error("❌ No valid data for training")
            return False
        
        logger.info(f"✅ {len(df_clean)} records available for training")
        
        # -------------------------------
        # ML MODEL
        # -------------------------------
        X = df_clean[["Attendance_Score", "Homework_Score", "Exam_Score"]]
        y = df_clean["result"]
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = SVC(kernel="linear", random_state=42)
        model.fit(X_scaled, y)
        
        logger.info("✅ Model trained successfully")
        
        # Save model
        pickle.dump(model, open("models/model.pkl", "wb"))
        pickle.dump(scaler, open("models/scaler.pkl", "wb"))
        
        logger.info("✅ Model saved to models/model.pkl and models/scaler.pkl")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error training model: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    train_model()