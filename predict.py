import pandas as pd
import pickle
import os
import logging

logger = logging.getLogger(__name__)

def load_model():
    """Load trained model and scaler"""
    try:
        model = pickle.load(open("models/model.pkl", "rb"))
        scaler = pickle.load(open("models/scaler.pkl", "rb"))
        logger.info("✅ Model and scaler loaded successfully")
        return model, scaler
    except FileNotFoundError:
        logger.error("❌ Model files not found. Train the model first.")
        return None, None


def predict_student(data):
    """
    Predict student performance
    
    Args:
        data: DataFrame with columns: Attendance_Score, Homework_Score, Exam_Score
    
    Returns:
        predictions: Array of predictions (Good, Average, At Risk)
    """
    model, scaler = load_model()
    
    if model is None or scaler is None:
        return None
    
    try:
        # Select same columns used during training
        X = data[["Attendance_Score", "Homework_Score", "Exam_Score"]]
        
        # Scale
        X_scaled = scaler.transform(X)
        
        # Predict
        prediction = model.predict(X_scaled)
        
        logger.info(f"✅ Predictions made for {len(prediction)} students")
        return prediction
        
    except Exception as e:
        logger.error(f"❌ Prediction error: {str(e)}")
        return None


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    test_data = pd.DataFrame({
        "Attendance_Score": [75, 85, 50],
        "Homework_Score": [80, 70, 40],
        "Exam_Score": [70, 75, 30]
    })
    
    results = predict_student(test_data)
    if results is not None:
        print("Predictions:", results)