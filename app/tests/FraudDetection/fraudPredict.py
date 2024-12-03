import joblib
from flask import Flask, jsonify, request
from app import app
import requests
import json

model = joblib.load(r"E:\Working\Tech-Simp-2\app\tests\FraudDetection\fraud_detection_model.joblib")

@app.route('/fraud_result', methods=['POST'])
def fraud_result():
    data = request.get_json()
    
    totalWeight = data.get('noOfPosts', 0)
    captionData = data.get('captionData', [])
    bioText = data.get('bioText', {})
    
    fraud_result = 0

    # Ensure the loop does not exceed the length of captionData
    for i in range(min(totalWeight, len(captionData))):
        currCaptionData = captionData[i]
        
        if 'Caption' in currCaptionData and currCaptionData['Caption'] is not None:
            currText = currCaptionData['Caption']
            
            # Convert to lowercase
            currText = currText.lower()
            print(currText)
            
            prediction = model.predict([currText])
            fraud_result += prediction[0]
            print(prediction[0])
    
    # Handle bioText
    if isinstance(bioText, dict) and 'Caption' in bioText and bioText['Caption'] is not None:
        bioTextContent = bioText['Caption']
        bioTextContent = bioTextContent.lower()
        prediction = model.predict([bioTextContent])
        fraud_result += prediction[0]
        print(bioTextContent)
        print(prediction[0])
    
    # Calculate fraud percentage
    fraud_percent = (fraud_result / (totalWeight + 1)) * 100 if totalWeight > 0 else 0
    
    return jsonify({'result': fraud_percent})
