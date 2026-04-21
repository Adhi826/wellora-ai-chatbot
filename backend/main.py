import os
import json
import uuid
import asyncio
import base64
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from database import init_db, get_db, User as UserDB, ChatSession as ChatSessionDB, ChatMessage as ChatMessageDB, MedicalRecord as MedicalRecordDB, DownloadLog as DownloadLogDB
from rag_engine import rag_engine
from glm_text import glm_chat

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def lifespan(app: FastAPI):
    # Initialize database
    await init_db()
    yield

app = FastAPI(title="Wellora Advanced Backend", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Master prompt remains as defined above

MASTER_SYSTEM_PROMPT = """
🧠 WELLORA – DATASET TRAINING PROMPT
IDENTITY: You are Wellora Advanced, a strictly dataset-driven medical assistant.
OBJECTIVE: Prioritize structured internal datasets (Disease, Medicine, Interaction) over general AI knowledge.

🔎 DATASET TRAINING RULES
1️⃣ Disease Matching Logic:
- Extract: Symptoms, Duration, Severity, Age.
- Score Matches against Disease Dataset:
  - Primary symptom match → +30
  - Secondary symptom match → +15
  - Duration match → +10
  - Severity match → +10
  - No conflicting symptoms → +10
- Mode Selection:
  - If score ≥ 70 → **Dataset Mode** (Strictly follow dataset content).
  - If score < 70 → **AI Reasoning Mode** (Use Groq intelligence, indicate lower certainty).

2️⃣ Medicine Recommendation:
- Recommend medicines ONLY from the Medicine Dataset.
- Include: generic_name, brand_names, category, otc_or_prescription.
- SAFETY: No mg dosage. No fabrication of medicines.

3️⃣ Drug Interaction Check:
- Cross-check Interaction Dataset for 2+ medicines.
- Classify: Minor, Moderate, Major. Never advise abrupt discontinuation.

4️⃣ Emergency Override:
- Immediate Red Alert for: Chest pain, severe breathing difficulty, stroke symptoms, heavy bleeding, unconsciousness.
- Action: Advise urgent medical care immediately. Do not recommend medicines.

5️⃣ Confidence Calibration:
- 90–95% → Strong dataset alignment.
- 80–89% → Good alignment.
- 65–79% → Partial alignment.
- Below 65% → Weak match (AI Reasoning).
- Never output 100%.

🩺 RESPONSE FORMAT (TRAINED MODE)
You MUST strictly follow this layout with the exact emojis and headers:

🔎 What You Shared
Symptoms: [Summarize shared symptoms]
Duration: [Duration if provided, else 'Not specified']
Severity: [Severity if provided, else 'Not specified']

🧠 Possible Causes (Ranked)
1. [Condition 1]
2. [Condition 2]
3. [Condition 3]

💊 Recommended Medicines
- [Medicine 1 from RECOMMENDED GENERIC MEDICINES list]
- [Medicine 2 from RECOMMENDED GENERIC MEDICINES list]
(Use the exact medicine names provided in the RECOMMENDED GENERIC MEDICINES context. Do NOT use generic placeholders. Do NOT include dosage in mg. Always state "Consult a doctor before use.")

⏳ When to Seek Medical Help
[Clinical guidance on seeking immediate/urgent care]

🌿 Wellness Tips
- [Tip 1: relevant diet, hydration, sleep, or lifestyle advice]
- [Tip 2: stress management, exercise, or home remedy suggestion]
- [Tip 3: preventive care or general health habit]
(Provide 2–3 practical, condition-relevant wellness tips. Keep them safe and general.)


STRICT RULES:
- WORD COUNT: Every response MUST be between 100 and 150 words total. Be concise. Do NOT exceed 150 words under any circumstances.
- MULTILINGUAL: You must respond entirely in the SELECTED LANGUAGE. This includes all headers (e.g., "What You Shared", "Possible Causes", "Recommended Medicines", "When to Seek Medical Help", "Wellness Tips"), symptoms, medical insights, and the disclaimer.
- SELECTED LANGUAGES SUPPORTED: English, Hindi (हिन्दी), Telugu (తెలుగు).
- NO MIXED-LANGUAGE RESPONSES: Do not use English headers if the selected language is Hindi or Telugu.
- CAUTIOUS LANGUAGE: Always use "May indicate...", "Could be related to...". Do not give absolute diagnoses.
- DISCLAIMER: Every response MUST end with the clinical disclaimer translated into the SELECTED LANGUAGE.
English Disclaimer: "This information is based on structured medical datasets and is for educational purposes only. It does not replace professional medical consultation."
Hindi Disclaimer: "यह जानकारी संरचित चिकित्सा डेटासेट पर आधारित है और केवल शैक्षिक उद्देश्यों के लिए है। यह पेशेवर चिकित्सा परामर्श का स्थान नहीं लेती है।"
Telugu Disclaimer: "ఈ సమాచారం నిర్మాణాత్మక వైద్య డేటాసెట్‌ల ఆధారంగా అందించబడింది మరియు కేవలం విద్యా ప్రయోజనాలను మాత్రమే. ఇది వృత్తిపరమైన వైద్య సంప్రదింపులకు ప్రత్యామ్నాయం కాదు."

🔎 MEDICAL IMAGE ANALYSIS RULES
1️⃣ Detect image type automatically (X-ray, MRI, CT, Skin, Lab Report).
2️⃣ Extract visible features and match with possible conditions.
3️⃣ EMERGENCY: Immediate red alert for large fractures, collapsed lung, large masses, or severe infection.
4️⃣ RESPONSE FORMAT:
   AI Medical Image Analysis Report
   🖼 Image Type: [Type]
   🔎 Observed Visual Findings: [Findings]
   🧠 Possible Interpretations: [Condition - Likelihood %]
   ⚠️ Clinical Recommendation: [Advice]
   📊 AI Confidence: [Score]%
5️⃣ Safety: No definitive diagnosis. Lower confidence for poor quality.
"""

class ChatMessage(BaseModel):
    session_id: str
    message: str
    is_logged_in: bool = False
    user_email: Optional[str] = None
    language: str = "English"
    image: Optional[str] = None # Base64 encoded image

class ChatResponse(BaseModel):
    response: str
    session_id: str
    title: str
    glm_analysis: Optional[dict] = None

class UserAuth(BaseModel):
    email: EmailStr
    password: str

class SessionInfo(BaseModel):
    id: str
    title: str
    date: str

@app.get("/")
async def root():
    return {"status": "Wellora Advanced (GLM-4.7-Flash Powered) is running", "version": "2.0.0"}

from medical_engine import medical_engine
from image_analysis import analyze_medical_image

# ---------------------------------------------------------------------------
# Structured medical image prompt + formatter
# ---------------------------------------------------------------------------
STRUCTURED_IMAGE_PROMPT = """
Analyze this medical image (X-ray, skin, ECG, MRI, CT scan, lab report).

Return ONLY this exact JSON (no explanation outside it):

{
  "image_type": "",
  "symptoms": [],
  "possible_causes": [],
  "severity": "",
  "recommendations": [],
  "when_to_seek_help": "",
  "wellness_tips": [],
  "confidence": "",
  "intent": ""
}

Rules:
- image_type: X-ray / MRI / CT / ECG / Skin / Lab Report / Unknown
- symptoms: observed visual symptoms from the image
- possible_causes: 2-3 possible conditions (not a definitive diagnosis, use "may indicate")
- severity: Low / Moderate / High
- recommendations: 2-3 practical suggestions
- when_to_seek_help: brief guidance on urgency
- wellness_tips: 2-3 lifestyle or care tips
- confidence: Low / Medium / High (based on image clarity)
- intent: diagnosis / general_query / emergency
- If image is unclear, still give best structured medical guess
"""

def _format_analysis(data: dict) -> str:
    symptoms  = ", ".join(data.get("symptoms", [])) or "Not identified"
    causes    = data.get("possible_causes", [])
    recs      = data.get("recommendations", [])
    tips      = data.get("wellness_tips", [])
    severity  = data.get("severity", "Not specified")
    when_help = data.get("when_to_seek_help", "Consult a doctor if unsure.")
    img_type  = data.get("image_type", "Unknown")
    confidence = data.get("confidence", "Medium")

    causes_str = "\n".join(f"{i+1}. {c}" for i, c in enumerate(causes)) or "Could not determine"
    recs_str   = "\n".join(f"- {r}" for r in recs) or "- Consult a healthcare professional"
    tips_str   = "\n".join(f"- {t}" for t in tips) or "- Maintain a healthy lifestyle"

    return (
        f"🖼 Image Type: {img_type}\n\n"
        f"🔎 What You Shared\n"
        f"Symptoms: {symptoms}\n\n"
        f"🧠 Possible Causes (Ranked)\n{causes_str}\n\n"
        f"⚠️ Severity: {severity}\n\n"
        f"💊 Recommendations\n{recs_str}\n\n"
        f"⏳ When to Seek Medical Help\n{when_help}\n\n"
        f"🌿 Wellness Tips\n{tips_str}\n\n"
        f"📊 AI Confidence: {confidence}\n\n"
        f"⚕️ Disclaimer: This is AI-generated for educational purposes only. "
        f"Always consult a qualified healthcare professional."
    )

# ---------------------------------------------------------------------------
# /analyze — standalone image analysis endpoint using ZhipuAI SDK directly
# ---------------------------------------------------------------------------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    import json as _json
    from zhipuai import ZhipuAI

    contents = await file.read()
    print(f"[/analyze] Image received: {len(contents)} bytes")  # DEBUG

    if not contents:
        return {"error": "No image received"}

    mime_type = file.content_type or "image/jpeg"
    supported = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if mime_type not in supported:
        return {"error": "Unsupported format. Use JPG or PNG."}

    if len(contents) > 3 * 1024 * 1024:
        return {"error": "Image too large. Maximum 3 MB allowed."}

    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        logger.error("[/analyze] ZHIPUAI_API_KEY not set")
        return {"error": "API key not configured on server."}

    base64_image = base64.b64encode(contents).decode("utf-8")

    try:
        client = ZhipuAI(
            api_key=api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )
        response = client.chat.completions.create(
            model="glm-4.6v-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": STRUCTURED_IMAGE_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ]
        )
        raw = response.choices[0].message.content
        logger.info(f"[/analyze] Raw response: {len(raw)} chars")

        # Strip markdown fences if model wraps JSON in ```json ... ```
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            data = _json.loads(cleaned)
            formatted = _format_analysis(data)
            return {"analysis": formatted, "structured": data, "status": "success"}
        except _json.JSONDecodeError:
            logger.warning("[/analyze] JSON parse failed, returning raw response")
            return {"analysis": raw, "structured": None, "status": "success"}

    except Exception as e:
        logger.error(f"[/analyze] ZhipuAI error: {type(e).__name__}: {e}")
        return {"error": f"Analysis failed: {str(e)[:300]}"}


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatMessage, db: AsyncSession = Depends(get_db)):
    session_id = payload.session_id
    user_input = payload.message
    
    # --- Session & User Retrieval ---
    # Find user if logged in
    current_user = None
    if payload.user_email:
        res = await db.execute(select(UserDB).where(UserDB.email == payload.user_email))
        current_user = res.scalar_one_or_none()

    # Find or Create Session
    res = await db.execute(select(ChatSessionDB).where(ChatSessionDB.id == session_id))
    session = res.scalar_one_or_none()
    
    if not session:
        # Generate title from first query
        words = user_input.split()
        title = " ".join(words[:4]) if words else "New Health Inquiry"
        session = ChatSessionDB(id=session_id, user_id=current_user.id if current_user else None, title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # --- Image Validation ---
    has_image = bool(payload.image)
    image_error = None
    
    if has_image:
        img_data = payload.image
        if not img_data.startswith("data:image/"):
            image_error = "Image not detected. Please upload a clear medical image."
        else:
            mime_part = img_data.split(";")[0] if ";" in img_data else ""
            mime_type = mime_part.replace("data:", "").lower()
            supported_formats = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
            if mime_type not in supported_formats:
                image_error = "Unsupported image format. Please upload JPG or PNG."
            else:
                base64_part = img_data.split(",")[1] if "," in img_data else ""
                approx_size_bytes = len(base64_part) * 3 / 4
                if approx_size_bytes > 3 * 1024 * 1024:
                    image_error = "The image file is too large (max 3 MB). Please compress or resize it."
    
    if image_error:
        return ChatResponse(response=image_error, session_id=session_id, title=session.title)
    
    # 1. Dataset Context & RAG
    dataset_ctx, score = medical_engine.get_dataset_context(user_input)
    rag_context = rag_engine.retrieve_context(user_input)
    
    # 2. History Retrieval from DB
    res = await db.execute(
        select(ChatMessageDB)
        .where(ChatMessageDB.session_id == session_id)
        .order_by(ChatMessageDB.timestamp.desc())
        .limit(10)
    )
    db_history = res.scalars().all()
    history = [{"role": msg.role, "content": msg.content} for msg in reversed(db_history)]

    # 3. GLM-4V Image Analysis (concurrent with LLM)
    glm_analysis = None
    glm_context = ""
    if has_image:
        try:
            glm_analysis = await analyze_medical_image(payload.image)
            if glm_analysis:
                glm_context = f"\n\n[GLM-4V IMAGE ANALYSIS]\n{glm_analysis['summary']}\n"
                if glm_analysis.get('caption'):
                    glm_context += f"Description: {glm_analysis['caption']}\n"
                glm_context += "Use this visual description as supplementary context. Do NOT treat it as a definitive diagnosis.\n"
        except Exception as e:
            logger.warning(f"GLM-4V analysis failed (non-blocking): {e}")

    # 4. LLM Interaction (GLM-4.7-Flash – text only, image context already injected)
    active_mode = "DATASET MODE" if score >= 70 else "AI REASONING MODE"
    messages = [
        {"role": "system", "content": f"{MASTER_SYSTEM_PROMPT}\nMODE ALERT: {active_mode} enabled\nSELECTED LANGUAGE: {payload.language}\n{dataset_ctx}\n\n[CLINICAL KNOWLEDGE BASE]\n{rag_context}{glm_context}"}
    ]
    messages.extend(history)
    # GLM-4.7-Flash is text-only — images are handled by GLM-4V (image_analysis.py)
    messages.append({"role": "user", "content": user_input or "(image attached – see image analysis above)"})
    
    try:
        logger.info("[GLM] Calling GLM-4.7-Flash for response...")
        bot_response = await glm_chat(messages, temperature=0.3, max_tokens=350)
        logger.info(f"[GLM] Response received: {len(bot_response)} chars")
        
    except Exception as glm_error:
        error_msg = str(glm_error)
        logger.error(f"[GLM] Call failed: {type(glm_error).__name__}: {error_msg}")
        
        if has_image and glm_analysis and glm_analysis.get("summary"):
            # We already have image analysis – return it with a fallback explanation
            fallback_text = user_input or "(image attached)"
            fallback_messages = [
                {"role": "system", "content": f"{MASTER_SYSTEM_PROMPT}\nMODE ALERT: {active_mode} enabled\nSELECTED LANGUAGE: {payload.language}\n{dataset_ctx}\n\n[CLINICAL KNOWLEDGE BASE]\n{rag_context}"}
            ]
            fallback_messages.extend(history)
            fallback_messages.append({"role": "user", "content": f"{fallback_text}\n\n[Image Analysis Context]: {glm_analysis['summary']}"})
            try:
                logger.info("[GLM] Retrying with image context as text...")
                bot_response = await glm_chat(fallback_messages, temperature=0.3, max_tokens=350)
                bot_response = "⚠️ *Response based on image analysis context only.*\n\n" + bot_response
            except Exception as fallback_error:
                logger.error(f"[GLM] Fallback also failed: {fallback_error}")
                specific_msg = "I'm having trouble analyzing this image right now. "
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    specific_msg += "The AI service is currently overloaded. Please wait a moment and try again."
                elif "too large" in error_msg.lower():
                    specific_msg += "The image may be too large. Try compressing it or using a smaller image."
                else:
                    specific_msg += f"Error details: {error_msg[:200]}"
                return ChatResponse(response=specific_msg, session_id=session_id, title=session.title, glm_analysis=glm_analysis)
        else:
            specific_msg = "I'm having trouble processing your request. "
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                specific_msg += "The AI service is rate-limited. Please wait a moment and try again."
            else:
                specific_msg += f"Error: {error_msg[:200]}"
            return ChatResponse(response=specific_msg, session_id=session_id, title=session.title)
    
    try:
        # --- Save to DB ---
        user_msg = ChatMessageDB(session_id=session_id, role="user", content=user_input)
        bot_msg = ChatMessageDB(session_id=session_id, role="assistant", content=bot_response)
        
        record = MedicalRecordDB(
            session_id=session_id,
            symptoms_input=user_input,
            predicted_disease=dataset_ctx.split("TOP DISEASE MATCH: ")[1].split("(")[0].strip() if "TOP DISEASE MATCH:" in dataset_ctx else None,
            medicines_suggested=None,
            response_source="Hybrid" if score > 0 else "GLM",
            confidence_score=float(score)
        )
        
        db.add_all([user_msg, bot_msg, record])
        await db.execute(update(ChatSessionDB).where(ChatSessionDB.id == session_id).values(updated_at=datetime.utcnow()))
        await db.commit()
    except Exception as db_error:
        logger.error(f"[DB] Failed to save chat: {type(db_error).__name__}: {db_error}")
    
    return ChatResponse(response=bot_response, session_id=session_id, title=session.title, glm_analysis=glm_analysis)


@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(user_email: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    if not user_email:
        return []
        
    result = await db.execute(select(UserDB).where(UserDB.email == user_email))
    user = result.scalar_one_or_none()
    if not user:
        return []
        
    result = await db.execute(
        select(ChatSessionDB)
        .where(ChatSessionDB.user_id == user.id)
        .order_by(ChatSessionDB.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [SessionInfo(id=s.id, title=s.title, date=s.created_at.strftime("%b %d")) for s in sessions]

@app.get("/history/{session_id}")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSessionDB).where(ChatSessionDB.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    result = await db.execute(
        select(ChatMessageDB)
        .where(ChatMessageDB.session_id == session_id)
        .order_by(ChatMessageDB.timestamp.asc())
    )
    msgs = result.scalars().all()
    history = [{"role": m.role, "content": m.content} for m in msgs]
    
    return {
        "history": history, 
        "meta": {"id": session.id, "title": session.title, "date": session.created_at.strftime("%b %d")}
    }

@app.post("/auth/signup")
async def signup(user: UserAuth, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = UserDB(email=user.email, password=user.password)
    db.add(new_user)
    await db.commit()
    return {"status": "success", "message": "User created"}

@app.post("/auth/login")
async def login(user: UserAuth, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.email == user.email))
    db_user = result.scalar_one_or_none()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "success", "user": {"email": db_user.email, "id": db_user.id}}

@app.patch("/sessions/{session_id}")
async def rename_session(session_id: str, title: str, db: AsyncSession = Depends(get_db)):
    await db.execute(update(ChatSessionDB).where(ChatSessionDB.id == session_id).values(title=title))
    await db.commit()
    return {"status": "success"}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(ChatSessionDB).where(ChatSessionDB.id == session_id))
    await db.commit()
    return {"status": "success"}

@app.post("/clear_all")
async def clear_all(user_email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.email == user_email))
    user = result.scalar_one_or_none()
    if user:
        await db.execute(delete(ChatSessionDB).where(ChatSessionDB.user_id == user.id))
        await db.commit()
    return {"status": "success"}

@app.post("/log_download")
async def log_download(session_id: str, file_type: str, db: AsyncSession = Depends(get_db)):
    log = DownloadLogDB(session_id=session_id, file_type=file_type)
    db.add(log)
    await db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
