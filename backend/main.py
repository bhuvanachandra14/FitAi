from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import face_recognition
import numpy as np
import shutil
import io
from database import Base, engine, SessionLocal, Face

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
async def register_face(
    name: str = Form(...),
    age: int = Form(...),
    height: str = Form(...),
    weight: str = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Read image file
    contents = await file.read()
    file_bytes = np.frombuffer(contents, np.uint8)
    
    # We need to decode the image for face_recognition
    # face_recognition.load_image_file accepts a file path or a file-like object
    # Let's try passing the bytes directly to a cv2 decode or similar if needed, 
    # but face_recognition uses PIL or similar. 
    # Actually face_recognition.load_image_file takes a filename or file object.
    
    image = face_recognition.load_image_file(io.BytesIO(contents))
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        raise HTTPException(status_code=400, detail="No face found in the image")

    # Taking the first face found
    encoding = encodings[0]
    
    # Check if face already exists
    faces = db.query(Face).all()
    known_encodings = []
    
    for face in faces:
        known_encodings.append(np.frombuffer(face.encoding, dtype=np.float64))

    if known_encodings:
        matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.45)
        if True in matches:
             raise HTTPException(status_code=400, detail="User already exists! Please login instead.")

    new_face = Face(name=name, age=age, height=height, weight=weight, encoding=encoding.tobytes())
    db.add(new_face)
    db.commit()
    db.refresh(new_face)
    
    return {"message": f"Face registered for {name}", "id": new_face.id}

@app.post("/recognize")
async def recognize_face(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    image = face_recognition.load_image_file(io.BytesIO(contents))
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        raise HTTPException(status_code=400, detail="No face found in the image")
    
    # Get unknown face encoding
    unknown_encoding = encodings[0]

    # Load all known faces
    faces = db.query(Face).all()
    known_encodings = []
    known_names = []
    
    for face in faces:
        known_encodings.append(np.frombuffer(face.encoding, dtype=np.float64))
        known_names.append(face.name)
    
    if not known_encodings:
         return {"name": "Unknown", "match": False, "emotion": None}

    # Compare with stricter tolerance (default is 0.6, lower is stricter)
    # 0.45 is a good baseline for higher accuracy
    matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.45)
    face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    
    best_match_index = np.argmin(face_distances)
    if matches[best_match_index]:
        # name = known_names[best_match_index]  <-- This approach with parallel lists is harder for extra attributes
        # Let's find the matching Face object directly from the index
        matched_face = faces[best_match_index]
        return {
            "id": matched_face.id,
            "name": matched_face.name, 
            "age": matched_face.age,
            "height": matched_face.height,
            "weight": matched_face.weight,
            "match": True
        }
    
    return {"name": "Unknown", "match": False}

import google.generativeai as genai
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from database import Message

load_dotenv()

# Configure Gemini
# NOTE: User needs to create a .env file with GEMINI_API_KEY=...
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    model = None

class ChatRequest(BaseModel):
    message: str
    age: int
    height: str
    weight: str
    name: str
    face_id: int = None

@app.post("/chat")
async def chat_agent(request: ChatRequest, db: Session = Depends(get_db)):
    msg = request.message.strip()
    print(f"DEBUG: Received chat request. Message: {msg}, FaceID: {request.face_id}")
    
    # Save User Message
    if request.face_id:
        try:
            user_msg_db = Message(face_id=request.face_id, role="user", content=msg)
            db.add(user_msg_db)
            db.commit()
        except Exception as e:
            print(f"Error saving user message: {e}")

    # 1. Parse Stats (Keep existing logic for robust fallback or context)
    try:
        # Standardize weight to kg
        w_str = request.weight.lower().replace("kg", "").replace("lbs", "").strip()
        weight_kg = float(w_str)
        if "lbs" in request.weight.lower():
             weight_kg = weight_kg * 0.453592

        # Standardize height to cm
        h_str = request.height.lower()
        if "'" in h_str: # feet inches
             parts = h_str.split("'")
             ft = float(parts[0])
             inch = float(parts[1].replace('"', '')) if len(parts) > 1 and parts[1] else 0
             height_cm = (ft * 30.48) + (inch * 2.54)
        else:
             height_cm = float(h_str.replace("cm", "").strip())
        
        age = request.age
        
        # Calculate derived metrics for context
        bmi = weight_kg / ((height_cm/100) ** 2)
        bmi_status = "Healthy"
        if bmi < 18.5: bmi_status = "Underweight"
        elif bmi > 25: bmi_status = "Overweight"
        
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        tdee = int(bmr * 1.55)

    except:
        return {"response": "Please update your profile stats so I can help you better!"}

    # 2. Use Gemini if available
    if model:
        try:
            # Construct a rich system prompt with user context
            system_context = f"""
            You are an expert AI Dietician and Fitness Coach. 
            User Context:
            - Name: {request.name}
            - Age: {request.age}
            - Height: {request.height} (~{height_cm:.1f} cm)
            - Weight: {request.weight} (~{weight_kg:.1f} kg)
            - BMI: {bmi:.1f} ({bmi_status})
            - Estimated TDEE: {tdee} kcal/day

            Your goal is to help them achieve their fitness goals (loss, gain, maintenance) based on their stats.
            - Be encouraging, professional, and specific.
            - If asked for a plan, provide a detailed day plan with calories.
            - If asked a question, answer efficiently based on their stats.
            - Keep responses concise but formatted with Markdown (bolding, lists).
            """
            
            chat = model.start_chat(history=[
                {"role": "user", "parts": [system_context]},
                {"role": "model", "parts": ["Understood. I am ready to act as your personal AI Dietician. How can I help you today?"]}
            ])
            
            response = chat.send_message(msg)
            
            # Save AI Response
            if request.face_id:
                try:
                    ai_msg_db = Message(face_id=request.face_id, role="ai", content=response.text)
                    db.add(ai_msg_db)
                    db.commit()
                except Exception as e:
                    print(f"Error saving AI message: {e}")
            
            return {"response": response.text}
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return {"response": "I'm having trouble connecting to my brain right now. Please check your API key."}

    # 3. Fallback (Static Logic) if no API key
    return {"response": "⚠️ **Gemini API Key Missing**\n\nTo enable the smart AI, please add your `GEMINI_API_KEY` to the `.env` file in the backend folder.\n\nFor now, I can only calculate that your BMI is **{:.1f}**.".format(bmi)}

@app.get("/chat/history/{face_id}")
def get_chat_history(face_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.face_id == face_id).order_by(Message.timestamp.asc()).all()
    return messages
