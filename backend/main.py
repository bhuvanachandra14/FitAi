from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import face_recognition
import numpy as np
import io
import os
import logging
from database import Base, engine, SessionLocal, Face, Message

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── DB init ───────────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://bhuvanachandra14.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB dependency ─────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_stats(height: str, weight: str, age: int):
    """
    Convert raw height/weight strings to floats (cm, kg).
    Raises ValueError with a user-friendly message on bad input.
    """
    try:
        w_str = weight.lower().replace("kg", "").replace("lbs", "").strip()
        weight_kg = float(w_str)
        if "lbs" in weight.lower():
            weight_kg *= 0.453592
    except ValueError:
        raise ValueError(
            "Could not read your weight. Please use a format like '70kg' or '154lbs'."
        )

    try:
        h_str = height.lower().strip()
        if "'" in h_str:                        # e.g. 5'9" or 5'9
            parts = h_str.split("'")
            ft = float(parts[0])
            inch = float(parts[1].replace('"', '').strip()) if len(parts) > 1 and parts[1].strip() else 0
            height_cm = (ft * 30.48) + (inch * 2.54)
        else:
            height_cm = float(h_str.replace("cm", "").strip())
    except ValueError:
        raise ValueError(
            "Could not read your height. Please use a format like '175cm' or '5\\'9\"'."
        )

    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5:
        bmi_status = "Underweight"
    elif bmi > 25:
        bmi_status = "Overweight"
    else:
        bmi_status = "Healthy"

    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    tdee = int(bmr * 1.55)

    return weight_kg, height_cm, bmi, bmi_status, tdee


# ── /register ─────────────────────────────────────────────────────────────────
@app.post("/register")
async def register_face(
    name: str = Form(...),
    age: int = Form(...),
    height: str = Form(...),
    weight: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate stats before doing any face work
    try:
        parse_stats(height, weight, age)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    contents = await file.read()
    image = face_recognition.load_image_file(io.BytesIO(contents))
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        raise HTTPException(status_code=400, detail="No face found in the image.")

    encoding = encodings[0]

    # FIX: zip faces + encodings together so index can never drift
    faces = db.query(Face).all()
    known = [(f, np.frombuffer(f.encoding, dtype=np.float64)) for f in faces]

    if known:
        known_encs = [enc for _, enc in known]
        matches = face_recognition.compare_faces(known_encs, encoding, tolerance=0.45)
        if True in matches:
            raise HTTPException(
                status_code=400,
                detail="User already exists! Please login instead.",
            )

    new_face = Face(
        name=name,
        age=age,
        height=height,
        weight=weight,
        encoding=encoding.tobytes(),
    )
    db.add(new_face)
    db.commit()
    db.refresh(new_face)
    logger.info("Registered new user: %s (id=%d)", name, new_face.id)
    return {"message": f"Face registered for {name}", "id": new_face.id}


# ── /recognize ────────────────────────────────────────────────────────────────
@app.post("/recognize")
async def recognize_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    image = face_recognition.load_image_file(io.BytesIO(contents))
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        raise HTTPException(status_code=400, detail="No face found in the image.")

    unknown_encoding = encodings[0]

    # FIX: keep faces and their encodings paired so index always matches
    faces = db.query(Face).all()
    if not faces:
        return {"name": "Unknown", "match": False}

    paired = [(f, np.frombuffer(f.encoding, dtype=np.float64)) for f in faces]
    known_encs = [enc for _, enc in paired]

    matches = face_recognition.compare_faces(known_encs, unknown_encoding, tolerance=0.45)
    distances = face_recognition.face_distance(known_encs, unknown_encoding)
    best_idx = int(np.argmin(distances))

    if matches[best_idx]:
        matched_face, _ = paired[best_idx]   # guaranteed correct face object
        logger.info("Recognized user: %s (id=%d)", matched_face.name, matched_face.id)
        return {
            "id": matched_face.id,
            "name": matched_face.name,
            "age": matched_face.age,
            "height": matched_face.height,
            "weight": matched_face.weight,
            "match": True,
        }

    return {"name": "Unknown", "match": False}


# ── /user/{face_id} ───────────────────────────────────────────────────────────
# FIX: new endpoint so /chat fetches stats server-side instead of re-asking user
@app.get("/user/{face_id}")
def get_user(face_id: int, db: Session = Depends(get_db)):
    face = db.query(Face).filter(Face.id == face_id).first()
    if not face:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "id": face.id,
        "name": face.name,
        "age": face.age,
        "height": face.height,
        "weight": face.weight,
    }


# ── Gemini setup ──────────────────────────────────────────────────────────────
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    logger.info("Gemini configured successfully.")
else:
    gemini_model = None
    logger.warning("GEMINI_API_KEY not set — AI chat will be unavailable.")


# ── /chat ─────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    face_id: int   # FIX: only need face_id — stats are fetched from DB below


@app.post("/chat")
async def chat_agent(request: ChatRequest, db: Session = Depends(get_db)):
    msg = request.message.strip()

    # FIX: fetch user from DB using face_id — no personal info re-asked
    face = db.query(Face).filter(Face.id == request.face_id).first()
    if not face:
        raise HTTPException(status_code=404, detail="User not found. Please log in again.")

    # FIX: specific exception types + proper error message returned to user
    try:
        weight_kg, height_cm, bmi, bmi_status, tdee = parse_stats(
            face.height, face.weight, face.age
        )
    except ValueError as e:
        return {"response": f"⚠️ {e}"}

    # Save user message
    try:
        db.add(Message(face_id=face.id, role="user", content=msg))
        db.commit()
    except Exception as e:
        logger.error("Failed to save user message: %s", e)

    if not gemini_model:
        return {
            "response": (
                "⚠️ **Gemini API Key Missing**\n\n"
                "Please add `GEMINI_API_KEY` to the `.env` file in the backend folder.\n\n"
                f"Your BMI is **{bmi:.1f}** ({bmi_status}), TDEE ≈ **{tdee} kcal/day**."
            )
        }

    system_context = f"""You are an expert AI Dietician and Fitness Coach.

User Context:
- Name: {face.name}
- Age: {face.age}
- Height: {face.height} (~{height_cm:.1f} cm)
- Weight: {face.weight} (~{weight_kg:.1f} kg)
- BMI: {bmi:.1f} ({bmi_status})
- Estimated TDEE: {tdee} kcal/day

Your goal is to help them achieve their fitness goals based on their stats.
- Be encouraging, professional, and specific.
- If asked for a plan, provide a detailed day plan with calories.
- Keep responses concise but formatted with Markdown (bolding, lists).
- Never ask the user for stats you already have above."""

    try:
        chat = gemini_model.start_chat(
            history=[
                {"role": "user", "parts": [system_context]},
                {
                    "role": "model",
                    "parts": [
                        f"Understood! I'm ready to be {face.name}'s personal AI coach. How can I help today?"
                    ],
                },
            ]
        )
        response = chat.send_message(msg)
        reply = response.text

        # Save AI response
        try:
            db.add(Message(face_id=face.id, role="ai", content=reply))
            db.commit()
        except Exception as e:
            logger.error("Failed to save AI message: %s", e)

        return {"response": reply}

    except Exception as e:
        logger.error("Gemini error: %s", e)
        return {"response": "I'm having trouble connecting right now. Please try again in a moment."}


# ── /chat/history/{face_id} ───────────────────────────────────────────────────
@app.get("/chat/history/{face_id}")
def get_chat_history(face_id: int, db: Session = Depends(get_db)):
    # Basic existence check
    face = db.query(Face).filter(Face.id == face_id).first()
    if not face:
        raise HTTPException(status_code=404, detail="User not found.")
    messages = (
        db.query(Message)
        .filter(Message.face_id == face_id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    return messages


# ── Static files (production build) ──────────────────────────────────────────
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

if os.path.exists("../frontend/dist"):
    app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith(("api", "docs", "openapi.json")):
            raise HTTPException(status_code=404)
        return FileResponse("../frontend/dist/index.html")
