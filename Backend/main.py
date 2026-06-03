# ---------- #
# Importing necessary modules

# ---- Standard Imports ---- #
import os
os.environ["PATH"] += r";C:\ffmpeg\bin"
from typing import List, Literal
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from datetime import datetime, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from Roadmap import Roadmap
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor


import uuid
import tempfile
import os
import json
import traceback
import time
import base64
import uvicorn


# ---- Custom Imports ---- #

from interview_ai import generate_question, evaluate_answer, analyze_video
from models import InterviewStart
from chatbot_service import ask_bot
from web_scraping import LinkedInScraper, NaukriScraper, SerpApiScraper
from agentic_workflow.resume_builder_agent.main import generate_resume

# ---------- #

# ---------- AUDIO TRANSCRIPTION CONFIG ---------- #
# Production-safe: do NOT import torch/transformers at startup.
# Local Whisper can still be enabled manually with USE_LOCAL_WHISPER=true,
# but keep it false on Render/free servers.

USE_LOCAL_WHISPER = os.getenv("USE_LOCAL_WHISPER", "false").lower() == "true"
asr_pipeline = None


def get_asr_pipeline():
    """
    Lazy-load local Whisper only when explicitly enabled.
    This prevents Render 512MB instances from crashing during startup.
    """
    global asr_pipeline

    if not USE_LOCAL_WHISPER:
        raise HTTPException(
            status_code=503,
            detail="Local Whisper is disabled in production. Use GROQ_API_KEY for transcription.",
        )

    if asr_pipeline is None:
        print("🚀 Loading local Whisper model...")
        try:
            from transformers import pipeline
            import torch
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Local Whisper dependencies are not installed: {str(e)}",
            )

        asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model=os.getenv("WHISPER_MODEL", "openai/whisper-tiny"),
            device=0 if torch.cuda.is_available() else -1,
        )

    return asr_pipeline


# -------- PATH CONFIG -------- #
# Keeps backend files stable even when Backend/ is moved outside client/.
BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
PROFILE_DIR = BASE_DIR / "profile_images"
RESUME_DIR = BASE_DIR / "resume"

ENV_PATH = BASE_DIR / ".env"

UPLOAD_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)
RESUME_DIR.mkdir(exist_ok=True)

# -------- INIT APP -------- #
app = FastAPI()
roadmap_engine = Roadmap()

@app.get("/")
def root():
    return {"message": "ElevateAI backend is running"}
# -------- MOUNT AFTER CREATION -------- #
app.mount("/images", StaticFiles(directory=str(PROFILE_DIR)), name="images")
app.mount("/resume-files", StaticFiles(directory=str(RESUME_DIR)), name="resume-files")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

load_dotenv(dotenv_path=ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise Exception("GOOGLE_API_KEY not set")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", api_key=GOOGLE_API_KEY, temperature=0
)


class BestJobRole(BaseModel):
    best_role: str = Field(description="Most suitable job role for the candidate")
    confidence: int = Field(description="Confidence score (0-100)")
    reasoning: str = Field(description="Why this role is suitable")


job_role_llm = llm.with_structured_output(BestJobRole)


def predict_best_job_role(skills, projects, certifications):

    message = HumanMessage(
        content=f"""
You are an expert technical recruiter.

Given the following candidate profile:

Skills: {skills}
Projects: {projects}
Certifications: {certifications}

Your task:
- Identify the SINGLE most suitable job role for this candidate
- Be realistic (entry-level vs experienced matters)
- Prefer industry-standard roles (e.g., Frontend Developer, Backend Engineer, Data Analyst)

Return:
- best_role
- confidence (0-100)
- reasoning

Rules:
- Do NOT invent skills
- Be precise (avoid vague roles like "Engineer")
- Match role to actual skill depth
"""
    )

    result = job_role_llm.invoke([message])
    return result.model_dump()


class WeakLineFeedback(BaseModel):
    weak_line: str = Field(
        description="The weakest or poorly written line from the resume"
    )
    improved_version: str = Field(
        description="AI suggested improved version of that line"
    )


class MarketReadiness(BaseModel):
    score: int = Field(description="Percentage Readiness of User")
    market_readiness: Literal[
        "Very weak resume",
        "Early stage candidate",
        "Moderate readiness",
        "Strong candidate",
        "Highly competitive candidate",
    ] = Field(description="User's Overall Job Market Readiness")
    key_strengths: List[str] = Field(description="Top professional strengths found")
    critical_gaps: List[str] = Field(description="Major missing qualifications")
    missing_keywords: List[str] = Field(description="Specific technical terms missing")
    weakest_line: WeakLineFeedback = Field(
        description="Weakest resume line along with improved AI suggestions for the target job."
    )
    skills: List[str] = Field(description="List of skills found in Resume")
    projects: List[str] = Field(description="List of projects found in resume")
    certifications: List[str] = Field(description="List certifications found in resume")


class RoadmapRequest(BaseModel):
    topic: str
    experience_level: str
    learning_style: str
    limit: int = 5
    language: str = "en"   # 🔥 ADD THIS

class ProfileUpdate(BaseModel):
    name: str
    username: str
    phone: str
    bio: str
    current_role: str
    target_role: str
    linkedin: str
    professional_links: list


structured_llm = llm.with_structured_output(MarketReadiness)


def get_db():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL not set in Backend/.env")

    # PostgreSQL only. No SQLite fallback, no users.db creation.
    if database_url.startswith("sqlite") or database_url.endswith(".db"):
        raise Exception("SQLite is disabled. Set DATABASE_URL to a PostgreSQL URL.")

    if not (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
        raise Exception("DATABASE_URL must be PostgreSQL, for example postgresql://user:password@host:5432/dbname")

    conn = psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )
    return conn


async def analyze_resume(pdf_bytes: bytes, target_role: str):

    pdf_data = base64.b64encode(pdf_bytes).decode("utf-8")

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": f"Analyze this resume against the target role: {target_role}. "
                """You are an expert resume evaluator and technical hiring advisor.

Your task is to analyze a user's resume and produce a structured evaluation of their job market readiness. Carefully read the resume content and return an analysis that matches the provided schema exactly.

Evaluation Rules:

1. Score (0–100)

* Estimate the user's overall job market readiness.
* 0–30 → Very weak resume
* 31–50 → Early stage candidate
* 51–70 → Moderate readiness
* 71–85 → Strong candidate
* 86–100 → Highly competitive candidate

2. Market Readiness Category

Return EXACTLY one of the following:

Very weak resume
Early stage candidate
Moderate readiness
Strong candidate
Highly competitive candidate

3. Key Strengths
   List the strongest aspects of the resume. These could include:

* technical skills
* notable projects
* internships or experience
* certifications
  Return 3–5 concise strengths.

4. Critical Gaps
   Identify the most important weaknesses preventing the candidate from being competitive. Examples:

* lack of real projects
* missing internships
* weak technical depth
* missing system design knowledge

Return 3–5 clear gaps.

5. Missing Keywords
   List important industry or ATS keywords that should ideally appear in the resume but are missing.

Examples:

* cloud platforms
* CI/CD
* distributed systems
* Kubernetes

Return 8–10 relevant keywords.

6. Weakest Resume Line
   Identify the single weakest or most poorly written line in the resume and provide a significantly improved version.

The improved version must:

* be more specific
* include measurable impact when possible
* sound professional and achievement-oriented
* be oriented towards the target job of the person
* change the statement to match the persons target goal

7. Skills
   Extract the skills explicitly mentioned in the resume.
   Do NOT invent skills that are not present.

8. Projects
   Extract the project titles or project descriptions mentioned in the resume.

9. Certifications
   Extract any certifications listed in the resume.

Important Constraints:

* Only use information present in the resume.
* Do NOT hallucinate experience, projects, or certifications.
* Keep lists concise and relevant.
* Ensure the output strictly matches the schema.
* The evaluation must be objective and realistic.

You will be provided with the user's resume content. Analyze it and produce the structured evaluation.
""",
            },
            {"type": "media", "mime_type": "application/pdf", "data": pdf_data},
        ]
    )

    result = structured_llm.invoke([message])
    print(f"DEBUG AI RESPONSE: {result}")
    return result.model_dump()


def translate_text(text, target_lang):
    if target_lang == "en":
        return text

    message = HumanMessage(
        content=f"""
Translate the following text into {target_lang}.

Text:
{text}

Rules:
- Keep technical meaning accurate
- Do not translate URLs
- Keep concise
"""
    )

    response = llm.invoke([message])
    return response.content


def safe_json_loads(value, default=None):
    if default is None:
        default = []
    if not value:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def row_get(row, key, default=None):
    if not row:
        return default
    try:
        return row.get(key, default)
    except AttributeError:
        return row[key] if key in row else default

# ---------------- CORS ---------------- #

origins = [
    "http://localhost:5173",
    "https://elevateai-pi.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- DATABASE ---------------- #
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        phone TEXT,
        bio TEXT,
        linkedin TEXT,
        "current_role" TEXT,
        target_role TEXT,
        best_job_role TEXT,
        professional_links TEXT,
        profile_image TEXT,
        cover_image TEXT,
        market_readiness TEXT,
        skills TEXT,
        projects TEXT,
        certifications TEXT,
        resume TEXT,
        resume_analysis TEXT,
        roadmap TEXT,
        created_at TEXT,
        last_active_date TEXT,
        learning_streak INTEGER DEFAULT 0,
        profile_views INTEGER DEFAULT 0,
        login_streak INTEGER DEFAULT 1,
        last_login_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id SERIAL PRIMARY KEY,
        user_email TEXT,
        role TEXT,
        message TEXT,
        response_time REAL,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS direct_messages (
        id SERIAL PRIMARY KEY,
        sender_id INTEGER,
        receiver_id INTEGER,
        message TEXT,
        created_at TEXT,
        deleted_for_sender INTEGER DEFAULT 0,
        deleted_for_receiver INTEGER DEFAULT 0,
        is_read INTEGER DEFAULT 0,
        file_url TEXT,
        file_type TEXT,
        file_name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feed_posts (
        id SERIAL PRIMARY KEY,
        user_email TEXT,
        content TEXT,
        type TEXT,
        tags TEXT,
        image TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS post_likes (
        id SERIAL PRIMARY KEY,
        post_id INTEGER,
        user_email TEXT,
        UNIQUE(post_id, user_email)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS post_comments (
        id SERIAL PRIMARY KEY,
        post_id INTEGER,
        user_email TEXT,
        comment TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS friend_requests (
        id SERIAL PRIMARY KEY,
        sender_id INTEGER,
        receiver_id INTEGER,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile_views_log (
        viewer_id INTEGER,
        viewed_id INTEGER,
        viewed_at TEXT
    )
    """)

    # ---------------- SAFE POSTGRES MIGRATIONS ---------------- #
    # CREATE TABLE IF NOT EXISTS does NOT add new columns to an existing table.
    # These ALTER statements keep older databases compatible after code/schema changes.
    user_columns = [
        ('name', 'TEXT'),
        ('username', 'TEXT'),
        ('email', 'TEXT'),
        ('password', 'TEXT'),
        ('phone', 'TEXT'),
        ('bio', 'TEXT'),
        ('linkedin', 'TEXT'),
        ('current_role', 'TEXT'),
        ('target_role', 'TEXT'),
        ('best_job_role', 'TEXT'),
        ('professional_links', 'TEXT'),
        ('profile_image', 'TEXT'),
        ('cover_image', 'TEXT'),
        ('market_readiness', 'TEXT'),
        ('skills', 'TEXT'),
        ('projects', 'TEXT'),
        ('certifications', 'TEXT'),
        ('resume', 'TEXT'),
        ('resume_analysis', 'TEXT'),
        ('roadmap', 'TEXT'),
        ('created_at', 'TEXT'),
        ('last_active_date', 'TEXT'),
        ('learning_streak', 'INTEGER DEFAULT 0'),
        ('profile_views', 'INTEGER DEFAULT 0'),
        ('login_streak', 'INTEGER DEFAULT 1'),
        ('last_login_date', 'TEXT'),
    ]

    for column_name, column_type in user_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    chat_message_columns = [
        ('user_email', 'TEXT'),
        ('role', 'TEXT'),
        ('message', 'TEXT'),
        ('response_time', 'REAL'),
        ('created_at', 'TEXT'),
    ]

    for column_name, column_type in chat_message_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    direct_message_columns = [
        ('sender_id', 'INTEGER'),
        ('receiver_id', 'INTEGER'),
        ('message', 'TEXT'),
        ('created_at', 'TEXT'),
        ('deleted_for_sender', 'INTEGER DEFAULT 0'),
        ('deleted_for_receiver', 'INTEGER DEFAULT 0'),
        ('is_read', 'INTEGER DEFAULT 0'),
        ('file_url', 'TEXT'),
        ('file_type', 'TEXT'),
        ('file_name', 'TEXT'),
    ]

    for column_name, column_type in direct_message_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE direct_messages ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    feed_post_columns = [
        ('user_email', 'TEXT'),
        ('content', 'TEXT'),
        ('type', 'TEXT'),
        ('tags', 'TEXT'),
        ('image', 'TEXT'),
        ('created_at', 'TEXT'),
    ]

    for column_name, column_type in feed_post_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE feed_posts ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    post_like_columns = [
        ('post_id', 'INTEGER'),
        ('user_email', 'TEXT'),
    ]

    for column_name, column_type in post_like_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE post_likes ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    post_comment_columns = [
        ('post_id', 'INTEGER'),
        ('user_email', 'TEXT'),
        ('comment', 'TEXT'),
        ('created_at', 'TEXT'),
    ]

    for column_name, column_type in post_comment_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE post_comments ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    friend_request_columns = [
        ('sender_id', 'INTEGER'),
        ('receiver_id', 'INTEGER'),
        ('status', "TEXT DEFAULT 'pending'"),
        ('created_at', 'TEXT'),
    ]

    for column_name, column_type in friend_request_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE friend_requests ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    profile_view_columns = [
        ('viewer_id', 'INTEGER'),
        ('viewed_id', 'INTEGER'),
        ('viewed_at', 'TEXT'),
    ]

    for column_name, column_type in profile_view_columns:
        safe_column = column_name.replace('"', '""')
        cursor.execute(f'ALTER TABLE profile_views_log ADD COLUMN IF NOT EXISTS "{safe_column}" {column_type}')

    cursor.execute("UPDATE users SET username = COALESCE(username, name, email, 'User') WHERE username IS NULL OR username = ''")
    cursor.execute("UPDATE users SET professional_links = '[]' WHERE professional_links IS NULL OR professional_links = ''")
    cursor.execute("UPDATE users SET skills = '[]' WHERE skills IS NULL OR skills = ''")
    cursor.execute("UPDATE users SET projects = '[]' WHERE projects IS NULL OR projects = ''")
    cursor.execute("UPDATE users SET certifications = '[]' WHERE certifications IS NULL OR certifications = ''")
    cursor.execute("UPDATE users SET roadmap = '[]' WHERE roadmap IS NULL OR roadmap = ''")
    cursor.execute("UPDATE users SET learning_streak = 0 WHERE learning_streak IS NULL")
    cursor.execute("UPDATE users SET profile_views = 0 WHERE profile_views IS NULL")
    cursor.execute("UPDATE users SET login_streak = 1 WHERE login_streak IS NULL")

    # ---------------- PERFORMANCE INDEXES ---------------- #
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_profile_views ON users(profile_views)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feed_posts_created_at ON feed_posts(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feed_posts_user_email ON feed_posts(user_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON post_likes(post_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_likes_user_email ON post_likes(user_email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON post_comments(post_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_friend_requests_sender_receiver ON friend_requests(sender_id, receiver_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_friend_requests_status ON friend_requests(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_direct_messages_sender_receiver ON direct_messages(sender_id, receiver_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_direct_messages_created_at ON direct_messages(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profile_views_log_viewer_viewed ON profile_views_log(viewer_id, viewed_id)")

    conn.commit()
    cursor.close()
    conn.close()


init_db()

# ---------------- AUTH CONFIG ---------------- #

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ---------------- REQUEST MODELS ---------------- #


class SignupRequest(BaseModel):
    name: str
    linkedin: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class JobSearchRequest(BaseModel):
    query: str
    location: str
    sources: List[str]


class ChatRequest(BaseModel):
    message: str


class SaveRoadmap(BaseModel):
    roadmap: list


class ResumeGenerateRequest(BaseModel):
    session_id: str
    resume_data: dict


# ---------------- PASSWORD UTILS ---------------- #


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)


# ---------------- JWT UTILS ---------------- #


def create_token(user_id: str):

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def transcribe_audio(file_path, language=None):
    """
    Production transcription:
    - Uses Groq Whisper API if GROQ_API_KEY is available.
    - Falls back to local Whisper only when USE_LOCAL_WHISPER=true.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")

    if groq_api_key:
        try:
            import requests
        except Exception:
            raise HTTPException(
                status_code=500,
                detail="requests package is required for Groq transcription. Add requests to requirements.txt.",
            )

        url = "https://api.groq.com/openai/v1/audio/transcriptions"

        with open(file_path, "rb") as audio_file:
            files = {
                "file": (
                    os.path.basename(file_path),
                    audio_file,
                    "audio/wav",
                )
            }

            data = {
                "model": os.getenv("GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo"),
            }

            if language and language != "auto":
                data["language"] = language

            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {groq_api_key}"},
                files=files,
                data=data,
                timeout=120,
            )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=500,
                detail=f"Groq transcription failed: {response.text}",
            )

        payload = response.json()
        return payload.get("text", "")

    # Local fallback, disabled on production unless explicitly enabled.
    pipe = get_asr_pipeline()

    generate_kwargs = {
        "task": "transcribe",
        "max_new_tokens": 200,
    }

    if language and language not in ["en", "auto"]:
        generate_kwargs["language"] = language

    result = pipe(file_path, generate_kwargs=generate_kwargs)
    return result["text"]

def translate_to_english(text):
    message = HumanMessage(
        content=f"""
Translate the following text into natural English.

Text:
{text}

Rules:
- Keep meaning accurate
- Do not add extra content
"""
    )

    response = llm.invoke([message])
    return response.content


import asyncio

@app.post("/audio/process")
async def process_audio(file: UploadFile = File(...), language: str = Form("auto")):
    """
    Speech-to-text endpoint.
    Production uses Groq Whisper API via GROQ_API_KEY.
    Local Whisper only runs when USE_LOCAL_WHISPER=true.
    """
    try:
        print("📥 Audio received")

        suffix = Path(file.filename or "audio.wav").suffix or ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()

            if not content:
                raise HTTPException(status_code=400, detail="Empty audio file")

            tmp.write(content)
            path = tmp.name

        print("🧠 Transcribing...")

        transcription = await asyncio.to_thread(transcribe_audio, path, language)

        print("✅ Done")

        try:
            os.remove(path)
        except Exception:
            pass

        return {
            "original_language": language,
            "transcription": transcription,
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        print("❌ AUDIO ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- AUTH ROUTES ---------------- #


@app.post("/signup")
def signup(data: SignupRequest):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = %s", (data.email,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(data.password)
    today = datetime.utcnow().date().isoformat()

    login_streak = 1
    last_login_date = today
    cursor.execute(
        """
        INSERT INTO users (
            name,
            username,
            linkedin,
            email,
            password,
            phone,
            bio,
            "current_role",
            target_role,
            professional_links,
            created_at,
            last_active_date,
            learning_streak,
            login_streak,
            last_login_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data.name,
            data.name,
            data.linkedin,
            data.email,
            hashed,
            "",
            "",
            "",
            "",
            json.dumps([]),
            today,
            today,
            0,
            1,
            today,
        ),
    )

    conn.commit()
    conn.close()

    return {"message": "User created"}


@app.post("/feed/like/{post_id}")
def like_post(
    post_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # 🔍 check if already liked
    cursor.execute(
        "SELECT * FROM post_likes WHERE post_id=%s AND user_email=%s", (post_id, email)
    )
    existing = cursor.fetchone()

    if existing:
        # ❌ unlike
        cursor.execute(
            "DELETE FROM post_likes WHERE post_id=%s AND user_email=%s", (post_id, email)
        )
        liked = False
    else:
        # ❤️ like
        cursor.execute(
            "INSERT INTO post_likes (post_id, user_email) VALUES (%s, %s)",
            (post_id, email),
        )
        liked = True

    # 🔢 get updated like count
    cursor.execute("SELECT COUNT(*) AS count FROM post_likes WHERE post_id=%s", (post_id,))
    likes = cursor.fetchone()["count"]

    conn.commit()
    conn.close()

    return {"liked": liked, "likes": likes}


class AddComment(BaseModel):
    comment: str


@app.post("/feed/comment/{post_id}")
def add_comment(
    post_id: int,
    data: AddComment,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO post_comments (post_id, user_email, comment, created_at)
        VALUES (%s, %s, %s, %s)
    """,
        (post_id, email, data.comment, datetime.utcnow().isoformat()),
    )

    conn.commit()
    conn.close()

    return {"message": "Comment added"}


@app.delete("/feed/comment/{comment_id}")
def delete_comment(
    comment_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # check ownership
    cursor.execute("SELECT user_email FROM post_comments WHERE id=%s", (comment_id,))
    comment = cursor.fetchone()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment["user_email"] != email:
        raise HTTPException(status_code=403, detail="Not allowed")

    cursor.execute("DELETE FROM post_comments WHERE id=%s", (comment_id,))

    conn.commit()
    conn.close()

    return {"message": "Comment deleted"}


@app.delete("/feed/post/{post_id}")
def delete_post(
    post_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # check ownership
    cursor.execute("SELECT user_email FROM feed_posts WHERE id=%s", (post_id,))
    post = cursor.fetchone()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post["user_email"] != email:
        raise HTTPException(status_code=403, detail="Not allowed")

    # delete related data first (IMPORTANT)
    cursor.execute("DELETE FROM post_likes WHERE post_id=%s", (post_id,))
    cursor.execute("DELETE FROM post_comments WHERE post_id=%s", (post_id,))

    # delete post
    cursor.execute("DELETE FROM feed_posts WHERE id=%s", (post_id,))

    conn.commit()
    conn.close()

    return {"message": "Post deleted"}


@app.post("/login")
def login(data: LoginRequest):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, username, linkedin, email, password, last_active_date, learning_streak, login_streak, last_login_date FROM users WHERE email = %s",
        (data.email,),
    )

    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = user["id"]
    name = user["name"]
    username = user["username"]
    linkedin = user["linkedin"]
    email = user["email"]
    password_hash = user["password"]

    if not verify_password(data.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    today = datetime.utcnow().date()

    login_streak = user["login_streak"] or 0
    last_login = user["last_login_date"]

    if last_login:
        last_date = datetime.strptime(last_login, "%Y-%m-%d").date()
        diff = (today - last_date).days

        if diff == 1:
            login_streak += 1
        elif diff > 1:
            login_streak = 1
    else:
        login_streak = 1

    cursor.execute(
        """
    UPDATE users
    SET last_login_date=%s, login_streak=%s
    WHERE email=%s
""",
        (today.isoformat(), login_streak, email),
    )

    conn.commit()
    conn.close()

    token = create_token(email)

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "username": username,
            "linkedin": linkedin,
            "email": email,
            "login_streak": login_streak,
        },
    }


@app.post("/roadmap/reset")
def reset_roadmap_streak(credentials: HTTPAuthorizationCredentials = Depends(security)):

    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET learning_streak=0, last_active_date=NULL
        WHERE email=%s
    """,
        (email,),
    )

    conn.commit()
    conn.close()

    return {"message": "Streak reset"}


@app.get("/dashboard")
def dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    user_id = verify_token(token)

    return {"message": "Access granted", "user": user_id}


@app.post("/roadmap")
def generate_roadmap(data: RoadmapRequest):

    try:
        roadmap = roadmap_engine.get_roadmap(
            topic=data.topic,
            experience_level=data.experience_level,
            learning_style=data.learning_style,
            upper_limit=data.limit,
        )

        # 🔥 TRANSLATE HERE
        if data.language != "en":

            all_titles = []

            for section in ["basic", "core", "advanced"]:
                for item in roadmap.get(section, []):
                    if item.get("title"):
                        all_titles.append(item["title"])

            # 🔥 single API call
            translated = translate_text("\n".join(all_titles), data.language).split("\n")

            i = 0
            for section in ["basic", "core", "advanced"]:
                for item in roadmap.get(section, []):
                    if item.get("title") and i < len(translated):
                        item["title"] = translated[i]
                        i += 1

        return roadmap

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("🔥 ROADMAP ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/me")
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    email = verify_token(token)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conn.close()

    resume_analysis = (
        safe_json_loads(user.get("resume_analysis"), None)
    )

    roadmap = safe_json_loads(user.get("roadmap"), [])
    completed_modules = 0
    total_modules = 0

    for stage in roadmap:
        for skill in stage.get("skills", []):
            total_modules += 1
            if skill.get("status") == "Completed":
                completed_modules += 1

    milestone = get_next_milestone(roadmap)

    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "username": user.get("username"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "bio": user.get("bio"),
        "linkedin": user.get("linkedin"),
        "current_role": user.get("current_role") or "",
        "target_role": user.get("target_role"),
        "profile_image": user.get("profile_image"),
        "cover_image": user.get("cover_image"),
        "resume": user.get("resume"),
        "resume_analysis": resume_analysis,
        "professional_links": (
            safe_json_loads(user.get("professional_links"), [])
        ),
        "market_readiness": user.get("market_readiness"),
        "skills": safe_json_loads(user.get("skills"), []),
        "projects": safe_json_loads(user.get("projects"), []),
        "certifications": (
            safe_json_loads(user.get("certifications"), [])
        ),
        "roadmap": roadmap,
        "next_milestone": milestone,
        "modules_completed": completed_modules,
        "modules_total": total_modules,
        "learning_streak": user.get("learning_streak"),
        "login_streak": user.get("login_streak"),
    }


@app.delete("/messages/conversation/{user_id}")
def delete_conversation(
    user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # 🔍 current user
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    current = cursor.fetchone()

    if not current:
        raise HTTPException(status_code=404, detail="User not found")

    current_user_id = current["id"]

    # 🧠 mark all messages as deleted for current user
    cursor.execute(
        """
        UPDATE direct_messages
        SET 
            deleted_for_sender = CASE 
                WHEN sender_id = %s THEN 1 ELSE deleted_for_sender 
            END,
            deleted_for_receiver = CASE 
                WHEN receiver_id = %s THEN 1 ELSE deleted_for_receiver 
            END
        WHERE 
            (sender_id=%s AND receiver_id=%s)
            OR
            (sender_id=%s AND receiver_id=%s)
    """,
        (
            current_user_id,
            current_user_id,
            current_user_id,
            user_id,
            user_id,
            current_user_id,
        ),
    )

    conn.commit()
    conn.close()

    return {"message": "Conversation deleted"}


@app.post("/profile/update")
def update_profile(
    data: ProfileUpdate, credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials
    email = verify_token(token)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
    UPDATE users
    SET name=%s,
        username=%s,
        phone=%s,
        bio=%s,
        "current_role"=%s,
        target_role=%s,
        linkedin=%s,
        professional_links=%s
    WHERE email=%s
""",
        (
            data.name,
            data.username,
            data.phone,
            data.bio,
            data.current_role,
            data.target_role,
            data.linkedin,
            json.dumps(data.professional_links),
            email,
        ),
    )
    conn.commit()
    conn.close()

    return {"message": "Profile updated"}


@app.post("/profile/upload-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):

    token = credentials.credentials
    email = verify_token(token)

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = PROFILE_DIR / filename

    contents = await file.read()

    with open(path, "wb") as f:
        f.write(contents)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET profile_image=%s WHERE email=%s", (f"/images/{filename}", email)
    )

    conn.commit()
    conn.close()

    return {"profile_image": f"/images/{filename}"}


@app.post("/profile/upload-cover")
async def upload_cover_image(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):

    token = credentials.credentials
    email = verify_token(token)

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = PROFILE_DIR / filename

    contents = await file.read()

    with open(path, "wb") as f:
        f.write(contents)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET cover_image=%s WHERE email=%s", (f"/images/{filename}", email)
    )

    conn.commit()
    conn.close()

    return {"cover_image": f"/images/{filename}"}


# ---------------- FILE UPLOAD ---------------- #


@app.get("/roadmap/user")
def get_user_roadmap(credentials: HTTPAuthorizationCredentials = Depends(security)):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT roadmap FROM users WHERE email=%s", (email,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    roadmap = json.loads(row["roadmap"]) if row["roadmap"] else []

    return {"roadmap": roadmap}


@app.post("/upload-resume")
async def analyze_uploaded_resume(
    file: UploadFile = File(...),
    target_job: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = credentials.credentials
        email = verify_token(token)

        file_ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / unique_name

        contents = await file.read()

        with open(file_path, "wb") as f:
            f.write(contents)

        report = await analyze_resume(contents, target_job)
        best_job = predict_best_job_role(
            report["skills"], report["projects"], report["certifications"]
        )

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
UPDATE users
SET market_readiness = %s,
    skills = %s,
    projects = %s,
    certifications = %s,
    target_role = %s,
    resume_analysis = %s,
    best_job_role = %s
WHERE email = %s
""",
            (
                report["market_readiness"],
                json.dumps(report["skills"]),
                json.dumps(report["projects"]),
                json.dumps(report["certifications"]),
                target_job,
                json.dumps(report),
                best_job["best_role"],  # 🔥 NEW
                email,
            ),
        )

        conn.commit()
        conn.close()

        return {
            "filename": unique_name,
            "file_path": f"/uploads/{unique_name}",
            "ats_score": report["score"],
            "market_readiness": report["market_readiness"],
            "strengths": report["key_strengths"],
            "weaknesses": report["critical_gaps"],
            "missing_keywords": report["missing_keywords"],
            "suggestions": report["weakest_line"]["improved_version"],
            "weak_line": report["weakest_line"]["weak_line"],
            # 🔥 NEW
            "recommended_job": best_job["best_role"],
            "job_confidence": best_job["confidence"],
            "job_reasoning": best_job["reasoning"],
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- JOB SEARCH ---------------- #


@app.get("/user/best-job")
def get_best_job(credentials: HTTPAuthorizationCredentials = Depends(security)):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT best_job_role FROM users WHERE email=%s", (email,))
    row = cursor.fetchone()

    conn.close()

    return {"best_job_role": row["best_job_role"] if row else None}


@app.post("/jobs/search")
def search_jobs(data: JobSearchRequest):

    results = []

    try:

        if "linkedin" in data.sources:
            linkedin = LinkedInScraper()
            linkedin_jobs = linkedin.fetch_jobs(data.query, data.location)

            if isinstance(linkedin_jobs, list):
                for j in linkedin_jobs:
                    j["source"] = "LinkedIn"
                    results.append(j)

        if "naukri" in data.sources:
            naukri = NaukriScraper()
            naukri_jobs = naukri.fetch_jobs(data.query, data.location)
            
            if isinstance(naukri_jobs, dict) and "error" in naukri_jobs:
                print(f"NAUKRI ERROR: {naukri_jobs['error']}") # Look for this in terminal
            elif isinstance(naukri_jobs, list):
                for j in naukri_jobs:
                    j["source"] = "Naukri"
                    results.append(j)

        if "web" in data.sources:
            serp = SerpApiScraper()
            web_jobs = serp.fetch_jobs(data.query, data.location)

            if isinstance(web_jobs, list):
                for j in web_jobs:
                    j["source"] = "Web"
                    results.append(j)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"jobs": results}


@app.get("/jobs")
def get_jobs():
    # raise RuntimeError

    #     linkedin = LinkedInScraper()
    #     naukri = NaukriScraper()
    #     web = SerpApiScraper()

    #     jobs = []

    #     try:
    #         linkedin_jobs = linkedin.fetch_jobs("", "India")
    #         if isinstance(linkedin_jobs, list):
    #             for j in linkedin_jobs:
    #                 j["source"] = "LinkedIn"
    #                 jobs.append(j)

    #         naukri_jobs = naukri.fetch_jobs("", "India")
    #         if isinstance(naukri_jobs, list):
    #             for j in naukri_jobs:
    #                 j["source"] = "Naukri"
    #                 jobs.append(j)

    #         web_jobs = web.fetch_jobs("", "India")
    #         if isinstance(web_jobs, list):
    #             for j in web_jobs:
    #                 j["source"] = "Web"
    #                 jobs.append(j)

    #     except Exception as e:
    #         print("Job fetch error:", e)

    return {"jobs": []}


import time


@app.post("/ai/chat")
def chat_ai(
    data: ChatRequest, credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials
    email = verify_token(token)

    start = time.time()

    response = ask_bot(email, data.message)

    response_time = round(time.time() - start, 2)

    conn = get_db()
    cursor = conn.cursor()

    # store user message
    cursor.execute(
        "INSERT INTO chat_messages (user_email, role, message, created_at) VALUES (%s, %s, %s, %s)",
        (email, "user", data.message, datetime.utcnow().isoformat()),
    )

    # store AI response
    cursor.execute(
        "INSERT INTO chat_messages (user_email, role, message, response_time, created_at) VALUES (%s, %s, %s, %s, %s)",
        (email, "ai", response, response_time, datetime.utcnow().isoformat()),
    )

    conn.commit()
    conn.close()

    return {"reply": response, "response_time": response_time}


INTERVIEW_SESSIONS = {}


@app.post("/interview/start")
def start_interview(data: InterviewStart):

    session_id = str(uuid.uuid4())

    question = generate_question(role=data.role, difficulty=data.difficulty)

    INTERVIEW_SESSIONS[session_id] = {
        "role": data.role,
        "difficulty": data.difficulty,
        "question_number": 1,
        "questions": [question],
        "answers": [],
    }

    return {
        "session_id": session_id,
        "question": question,
        "difficulty": data.difficulty,
        "question_number": 1,
    }


@app.get("/ai/history")
def get_chat_history(credentials: HTTPAuthorizationCredentials = Depends(security)):

    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, message, response_time FROM chat_messages WHERE user_email=%s ORDER BY id",
        (email,),
    )

    rows = cursor.fetchall()
    conn.close()

    messages = [
        {"role": r["role"], "content": r["message"], "responseTime": r["response_time"]}
        for r in rows
    ]

    return {"messages": messages}


@app.post("/roadmap/save")
def save_roadmap(
    data: SaveRoadmap, credentials: HTTPAuthorizationCredentials = Depends(security)
):

    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET roadmap=%s WHERE email=%s", (json.dumps(data.roadmap), email)
    )

    conn.commit()
    conn.close()

    return {"message": "Roadmap saved"}


def get_next_milestone(roadmap):

    if not roadmap:
        return None

    for stage in roadmap:
        for skill in stage.get("skills", []):
            if skill.get("status") != "Completed":
                return {"stage": stage.get("title"), "skill": skill.get("name")}

    return None


@app.post("/resume/generate")
def generate_resume_api(
    data: ResumeGenerateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        verify_token(credentials.credentials)

        html_resume = generate_resume(
            session_id=data.session_id, resume_data=data.resume_data
        )

        return {"html": html_resume}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profile/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):

    token = credentials.credentials
    email = verify_token(token)

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = RESUME_DIR / filename

    contents = await file.read()

    with open(path, "wb") as f:
        f.write(contents)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET resume=%s WHERE email=%s", (f"/resume-files/{filename}", email)
    )

    conn.commit()
    conn.close()

    return {"resume": f"/resume-files/{filename}"}


@app.get("/api/leaderboard")
def leaderboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                name,
                username,
                email,
                COALESCE("current_role", target_role, best_job_role, 'Developer') AS current_role,
                profile_image
            FROM users
            WHERE email=%s
            """,
            (email,),
        )
        current_user = cursor.fetchone()

        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        current_user_id = current_user["id"]

        cursor.execute("SELECT COUNT(*) AS count FROM users")
        total_users = cursor.fetchone()["count"]

        cursor.execute(
            """
            SELECT
                id,
                name,
                username,
                email,
                COALESCE("current_role", target_role, best_job_role, 'Developer') AS current_role,
                skills,
                projects,
                roadmap,
                profile_image,
                COALESCE(profile_views, 0) AS profile_views
            FROM users
            ORDER BY
                (COALESCE(profile_views, 0) + id) DESC,
                id ASC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cursor.fetchall()

        # Always include logged-in user even if pagination/sorting would hide them.
        if not any(r.get("id") == current_user_id for r in rows):
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    username,
                    email,
                    COALESCE("current_role", target_role, best_job_role, 'Developer') AS current_role,
                    skills,
                    projects,
                    roadmap,
                    profile_image,
                    COALESCE(profile_views, 0) AS profile_views
                FROM users
                WHERE id=%s
                """,
                (current_user_id,),
            )
            me_row = cursor.fetchone()
            if me_row:
                rows.insert(0, me_row)

        cursor.execute(
            """
            SELECT sender_id, receiver_id
            FROM friend_requests
            WHERE status='accepted'
              AND (sender_id=%s OR receiver_id=%s)
            """,
            (current_user_id, current_user_id),
        )
        friendships = cursor.fetchall()

        cursor.execute(
            """
            SELECT skills
            FROM users
            WHERE skills IS NOT NULL AND skills != '' AND skills != '[]'
            LIMIT 1000
            """
        )
        skill_rows = cursor.fetchall()

    finally:
        conn.close()

    friend_set = set()
    for f in friendships:
        if f.get("sender_id") == current_user_id:
            friend_set.add(f.get("receiver_id"))
        if f.get("receiver_id") == current_user_id:
            friend_set.add(f.get("sender_id"))

    skill_counter = {}
    for sr in skill_rows:
        for skill in safe_json_loads(sr.get("skills"), []):
            if skill:
                skill_counter[skill] = skill_counter.get(skill, 0) + 1

    users = []
    seen_ids = set()

    for r in rows:
        user_id = r.get("id")
        if user_id in seen_ids:
            continue
        seen_ids.add(user_id)

        skills = safe_json_loads(r.get("skills"), [])
        projects = safe_json_loads(r.get("projects"), [])
        roadmap = safe_json_loads(r.get("roadmap"), [])

        modules_completed = sum(
            1
            for stage in roadmap
            for item in stage.get("skills", [])
            if item.get("status") == "Completed"
        )

        users.append(
            {
                "id": user_id,
                "name": r.get("name") or r.get("username") or "User",
                "email": r.get("email"),
                "role": r.get("current_role") or "Developer",
                "location": "Global",
                "profile_image": r.get("profile_image") or "",
                "projectsBuilt": len(projects),
                "modulesCompleted": modules_completed,
                "skillsMastered": len(skills),
                "profileViews": r.get("profile_views") or 0,
                "badges": ["Verified"],
                "isFriend": user_id in friend_set,
                "isSelf": user_id == current_user_id,
            }
        )

    trending_skill = max(skill_counter, key=skill_counter.get) if skill_counter else ""

    return {
        "totalUsers": total_users,
        "trendingSkill": trending_skill,
        "currentUser": {
            "id": current_user.get("id"),
            "name": current_user.get("name") or current_user.get("username") or "User",
            "email": current_user.get("email"),
            "role": current_user.get("current_role") or "Developer",
            "profile_image": current_user.get("profile_image") or "",
        },
        "users": users,
        "limit": limit,
        "offset": offset,
    }


@app.get("/user/{user_id}")
def get_user_profile(
    user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # 🔍 get current user id
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    current = cursor.fetchone()

    if not current:
        raise HTTPException(status_code=404, detail="User not found")

    current_user_id = current["id"]

    # 🔍 fetch target user
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 👀 PROFILE VIEW LOGIC (ANTI-SPAM)
    if current_user_id != user_id:

        cursor.execute(
            """
            SELECT viewed_at FROM profile_views_log
            WHERE viewer_id=%s AND viewed_id=%s
            ORDER BY viewed_at DESC LIMIT 1
        """,
            (current_user_id, user_id),
        )

        last = cursor.fetchone()
        allow = True

        if last:
            last_time = datetime.fromisoformat(last["viewed_at"])
            if (datetime.utcnow() - last_time).total_seconds() < 600:
                allow = False

        if allow:
            # 🔥 increment view
            cursor.execute(
                """
                UPDATE users 
                SET profile_views = COALESCE(profile_views, 0) + 1 
                WHERE id=%s
            """,
                (user_id,),
            )

            # 🧾 log view
            cursor.execute(
                """
                INSERT INTO profile_views_log (viewer_id, viewed_id, viewed_at)
                VALUES (%s, %s, %s)
            """,
                (current_user_id, user_id, datetime.utcnow().isoformat()),
            )

            conn.commit()

    conn.close()

    user = dict(user)

    # JSON parsing
    user["skills"] = safe_json_loads(user.get("skills"), [])
    user["projects"] = safe_json_loads(user.get("projects"), [])
    user["certifications"] = safe_json_loads(user.get("certifications"), [])
    user["professional_links"] = safe_json_loads(user.get("professional_links"), [])

    return user


class SendMessage(BaseModel):
    receiver_id: int
    message: str


@app.post("/messages/send")
async def send_message(
    receiver_id: int = Form(...),
    message: str = Form(""),
    file: UploadFile = File(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # 🔍 Get sender
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    sender = cursor.fetchone()

    if not sender:
        raise HTTPException(status_code=404, detail="User not found")

    sender_id = sender["id"]

    # 🔍 Check receiver exists
    cursor.execute("SELECT id FROM users WHERE id=%s", (receiver_id,))
    receiver = cursor.fetchone()

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # 🚫 Prevent self messaging
    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="You cannot message yourself")

    # 🔒 ONLY ALLOW FRIENDS
    cursor.execute(
        """
        SELECT * FROM friend_requests 
        WHERE 
        status='accepted' AND
        (
            (sender_id=%s AND receiver_id=%s)
            OR
            (sender_id=%s AND receiver_id=%s)
        )
        """,
        (sender_id, receiver_id, receiver_id, sender_id),
    )

    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="You can only message friends")

    # 🚫 Prevent empty message + no file
    if not message and not file:
        raise HTTPException(status_code=400, detail="Message or file required")

    file_url = None
    file_type = None
    file_name = None

    # 📎 HANDLE FILE
    if file:
        contents = await file.read()
        file_name = file.filename

        # 📏 File size limit
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        allowed_types = [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "application/pdf",
            "video/mp4",
            "audio/mpeg",
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        SAFE_EXTENSIONS = ["png", "jpg", "jpeg", "pdf", "mp4", "mp3"]
        ext = file.filename.split(".")[-1].lower()

        if ext not in SAFE_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file extension")

        filename = f"{uuid.uuid4()}.{ext}"
        path = UPLOAD_DIR / filename

        with open(path, "wb") as f:
            f.write(contents)

        file_url = f"/uploads/{filename}"
        file_type = file.content_type

    # 💬 SAVE MESSAGE (🔥 FIX HERE)
    cursor.execute(
        """
        INSERT INTO direct_messages 
        (sender_id, receiver_id, message, file_url, file_type, file_name, created_at, is_read)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
        """,
        (
            sender_id,
            receiver_id,
            message,
            file_url,
            file_type,
            file_name,
            datetime.utcnow().isoformat(),
        ),
    )

    conn.commit()
    conn.close()

    return {
        "message": "sent successfully",
        "data": {
            "receiver_id": receiver_id,
            "text": message,
            "file": file_url,
        },
    }

@app.post("/friends/request/{receiver_id}")
def send_request(
    receiver_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    sender = cursor.fetchone()

    if not sender:
        raise HTTPException(status_code=404, detail="User not found")

    sender_id = sender["id"]

    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself")

    cursor.execute(
        """
SELECT * FROM friend_requests 
WHERE 
(
    (sender_id=%s AND receiver_id=%s)
    OR
    (sender_id=%s AND receiver_id=%s)
)
AND status IN ('pending', 'accepted')
""",
        (sender_id, receiver_id, receiver_id, sender_id),
    )

    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Request already sent")

    cursor.execute(
        """
        INSERT INTO friend_requests (sender_id, receiver_id, created_at)
        VALUES (%s, %s, %s)
    """,
        (sender_id, receiver_id, datetime.utcnow().isoformat()),
    )

    conn.commit()
    conn.close()

    return {"message": "Request sent"}


@app.get("/friends/requests")
def get_requests(credentials: HTTPAuthorizationCredentials = Depends(security)):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user["id"]

    cursor.execute(
        """
        SELECT fr.id, u.id as sender_id, u.name, u.profile_image
        FROM friend_requests fr
        JOIN users u ON fr.sender_id = u.id
        WHERE fr.receiver_id=%s AND fr.status='pending'
    """,
        (user_id,),
    )

    requests = cursor.fetchall()
    conn.close()

    return [dict(r) for r in requests]


@app.post("/friends/respond/{request_id}")
def respond_request(
    request_id: int,
    action: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # 🔍 get current user
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user["id"]

    # 🔍 get request
    cursor.execute(
        """
        SELECT receiver_id FROM friend_requests WHERE id=%s
    """,
        (request_id,),
    )
    req = cursor.fetchone()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # 🚫 ensure only receiver can act
    if req["receiver_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    status = "accepted" if action == "accept" else "rejected"

    cursor.execute(
        """
        UPDATE friend_requests 
        SET status=%s 
        WHERE id=%s
    """,
        (status, request_id),
    )

    conn.commit()
    conn.close()

    return {"message": f"Request {status}"}


@app.get("/stats")
def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS count FROM users")
    total_users = cursor.fetchone()["count"]

    cursor.execute("SELECT projects, skills FROM users")
    rows = cursor.fetchall()

    total_projects = 0
    total_skills = 0

    for r in rows:
        try:
            projects = json.loads(r["projects"]) if r["projects"] else []
            total_projects += len(projects)
        except:
            pass  # 🛡️ skip broken data safely

        try:
            skills = json.loads(r["skills"]) if r["skills"] else []
            total_skills += len(skills)
        except:
            pass

    conn.close()

    return {
        "totalUsers": total_users,
        "totalProjects": total_projects,
        "totalSkills": total_skills,
    }


@app.get("/friends")
def get_friends(credentials: HTTPAuthorizationCredentials = Depends(security)):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    user_id = user["id"]

    cursor.execute(
        """
        SELECT u.id, u.name, u.profile_image
        FROM friend_requests fr
        JOIN users u 
        ON (u.id = fr.sender_id OR u.id = fr.receiver_id)
        WHERE 
            fr.status='accepted'
            AND (fr.sender_id=%s OR fr.receiver_id=%s)
            AND u.id != %s
    """,
        (user_id, user_id, user_id),
    )

    friends = cursor.fetchall()
    conn.close()

    return [dict(f) for f in friends]


@app.post("/feed/create")
async def create_post(
    content: str = Form(""),
    tags: str = Form("[]"),
    file: UploadFile = File(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    image_path = None

    # 📸 HANDLE IMAGE
    if file:
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = UPLOAD_DIR / filename

        contents = await file.read()
        with open(path, "wb") as f:
            f.write(contents)

        image_path = f"/uploads/{filename}"

    # 💾 SAVE POST
    cursor.execute(
        """
        INSERT INTO feed_posts (user_email, content, type, tags, image, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """,
        (email, content, "POST", tags, image_path, datetime.utcnow().isoformat()),
    )

    conn.commit()
    conn.close()

    return {"message": "Post created"}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@app.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    new_hashed = hash_password(data.new_password)

    cursor.execute("UPDATE users SET password=%s WHERE email=%s", (new_hashed, email))

    conn.commit()
    conn.close()

    return {"message": "Password updated successfully"}


@app.post("/streak/update")
def update_streak(credentials: HTTPAuthorizationCredentials = Depends(security)):

    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT learning_streak, last_active_date
        FROM users WHERE email=%s
    """,
        (email,),
    )

    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    streak = user["learning_streak"] or 0
    last_active = user["last_active_date"]

    today = datetime.utcnow().date()

    if not last_active:
        streak = 1

    else:
        last_date = datetime.strptime(last_active, "%Y-%m-%d").date()
        diff = (today - last_date).days

        if diff == 0:
            conn.close()
            return {"streak": streak}

        elif diff == 1:
            streak += 1

        else:
            streak = 1

    cursor.execute(
        """
        UPDATE users
        SET learning_streak=%s, last_active_date=%s
        WHERE email=%s
    """,
        (streak, today.isoformat(), email),
    )

    conn.commit()
    conn.close()

    return {"streak": streak}


@app.delete("/friends/remove/{user_id}")
def remove_friend(
    user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    current = cursor.fetchone()

    if not current:
        raise HTTPException(status_code=404, detail="User not found")

    current_user_id = current["id"]

    cursor.execute(
        """
        DELETE FROM friend_requests
        WHERE 
            status='accepted' AND
            (
                (sender_id=%s AND receiver_id=%s)
                OR
                (sender_id=%s AND receiver_id=%s)
            )
    """,
        (current_user_id, user_id, user_id, current_user_id),
    )

    conn.commit()
    conn.close()

    return {"message": "Friend removed"}


@app.get("/feed")
def get_feed(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                f.id,
                f.user_email,
                f.content,
                f.type,
                f.tags,
                f.image,
                f.created_at,
                u.name,
                u.profile_image,
                COALESCE(l.like_count, 0) AS likes,
                COALESCE(c.comment_count, 0) AS comments,
                CASE WHEN ul.user_email IS NULL THEN FALSE ELSE TRUE END AS liked
            FROM feed_posts f
            JOIN users u ON f.user_email = u.email
            LEFT JOIN (
                SELECT post_id, COUNT(*) AS like_count
                FROM post_likes
                GROUP BY post_id
            ) l ON l.post_id = f.id
            LEFT JOIN (
                SELECT post_id, COUNT(*) AS comment_count
                FROM post_comments
                GROUP BY post_id
            ) c ON c.post_id = f.id
            LEFT JOIN post_likes ul
                ON ul.post_id = f.id AND ul.user_email = %s
            ORDER BY f.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (email, limit, offset),
        )
        posts = cursor.fetchall()
    finally:
        conn.close()

    result = []
    for p in posts:
        result.append(
            {
                "id": p.get("id"),
                "content": p.get("content") or "",
                "image": p.get("image"),
                "type": p.get("type") or "POST",
                "tags": safe_json_loads(p.get("tags"), []),
                "created_at": p.get("created_at"),
                "likes": p.get("likes") or 0,
                "liked": bool(p.get("liked")),
                "comments": p.get("comments") or 0,
                "author": {
                    "name": p.get("name") or "User",
                    "avatar": p.get("profile_image") or "👤",
                    "email": p.get("user_email"),
                },
            }
        )

    return {"posts": result, "limit": limit, "offset": offset, "hasMore": len(result) == limit}


@app.get("/messages/inbox")
def get_inbox(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user["id"]

        cursor.execute(
            """
            WITH visible_messages AS (
                SELECT
                    dm.*,
                    CASE
                        WHEN dm.sender_id = %s THEN dm.receiver_id
                        ELSE dm.sender_id
                    END AS other_user_id
                FROM direct_messages dm
                WHERE
                    (
                        dm.sender_id = %s
                        AND COALESCE(dm.deleted_for_sender, 0) = 0
                    )
                    OR
                    (
                        dm.receiver_id = %s
                        AND COALESCE(dm.deleted_for_receiver, 0) = 0
                    )
            ),
            ranked_messages AS (
                SELECT
                    vm.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY vm.other_user_id
                        ORDER BY vm.created_at DESC, vm.id DESC
                    ) AS rn
                FROM visible_messages vm
            ),
            unread_counts AS (
                SELECT sender_id AS other_user_id, COUNT(*) AS unread_count
                FROM direct_messages
                WHERE receiver_id = %s AND COALESCE(is_read, 0) = 0
                GROUP BY sender_id
            )
            SELECT
                u.id AS user_id,
                u.name,
                u.profile_image,
                rm.sender_id AS last_sender_id,
                rm.message,
                rm.file_type,
                rm.created_at AS last_time,
                COALESCE(uc.unread_count, 0) AS unread_count
            FROM ranked_messages rm
            JOIN users u ON u.id = rm.other_user_id
            LEFT JOIN unread_counts uc ON uc.other_user_id = rm.other_user_id
            WHERE rm.rn = 1
            ORDER BY rm.created_at DESC, rm.id DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, user_id, user_id, user_id, limit, offset),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    conversations = []
    for r in rows:
        conversations.append(
            {
                "user_id": r.get("user_id"),
                "name": r.get("name") or "User",
                "profile_image": r.get("profile_image") or "",
                "last_message": r.get("message") or f"📎 {r.get('file_type') or 'File'}",
                "last_sender_id": r.get("last_sender_id"),
                "unread_count": r.get("unread_count") or 0,
                "last_time": r.get("last_time"),
            }
        )

    return conversations


@app.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    delete_for_everyone: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    # 🔍 get user id
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user["id"]

    # 🔍 get message + file
    cursor.execute(
        """
        SELECT sender_id, receiver_id, file_url 
        FROM direct_messages 
        WHERE id=%s
    """,
        (message_id,),
    )
    msg = cursor.fetchone()

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    sender_id = msg["sender_id"]
    receiver_id = msg["receiver_id"]
    file_url = msg["file_url"]

    # 🔥 DELETE FOR EVERYONE (only sender allowed)
    if delete_for_everyone and user_id == sender_id:
        cursor.execute(
            """
            UPDATE direct_messages
            SET deleted_for_sender=1, deleted_for_receiver=1
            WHERE id=%s
        """,
            (message_id,),
        )

        # 🧹 delete file from storage
        if file_url:
            try:
                file_path = UPLOAD_DIR / file_url.replace("/uploads/", "")
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print("File delete error:", e)

    # 🧠 DELETE FOR ME
    else:
        if user_id == sender_id:
            cursor.execute(
                """
                UPDATE direct_messages
                SET deleted_for_sender=1
                WHERE id=%s
            """,
                (message_id,),
            )
        elif user_id == receiver_id:
            cursor.execute(
                """
                UPDATE direct_messages
                SET deleted_for_receiver=1
                WHERE id=%s
            """,
                (message_id,),
            )
        else:
            raise HTTPException(status_code=403, detail="Not allowed")

    conn.commit()
    conn.close()

    return {"message": "deleted"}


@app.get("/messages/{user_id}")
def get_messages(
    user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):

    email = verify_token(credentials.credentials)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    current = cursor.fetchone()
    current_user_id = current["id"]

    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Invalid conversation")

    # 🔥 MARK AS READ
    cursor.execute(
        """
        UPDATE direct_messages
        SET is_read = 1
        WHERE sender_id=%s AND receiver_id=%s
        """,
        (user_id, current_user_id),
    )

    # 💬 fetch messages
    cursor.execute(
        """
        SELECT 
            dm.*,
            u.profile_image,
            u.name as sender_name
        FROM direct_messages dm
        JOIN users u ON dm.sender_id = u.id
        WHERE 
        (
            dm.sender_id=%s AND dm.receiver_id=%s AND dm.deleted_for_sender=0
        )
        OR
        (
            dm.sender_id=%s AND dm.receiver_id=%s AND dm.deleted_for_receiver=0
        )
        ORDER BY dm.created_at ASC
        """,
        (current_user_id, user_id, user_id, current_user_id),
    )

    messages = cursor.fetchall()

    conn.commit()
    conn.close()

    return [dict(m) for m in messages]

@app.get("/feed/comments/{post_id}")
def get_comments(post_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT c.*, u.name, u.profile_image
        FROM post_comments c
        JOIN users u ON c.user_email = u.email
        WHERE c.post_id=%s
        ORDER BY c.created_at DESC
    """,
        (post_id,),
    )

    comments = cursor.fetchall()
    conn.close()

    return {"comments": [dict(c) for c in comments]}


@app.post("/interview/submit")
async def submit_answer(
    session_id: str = Form(...), answer: str = Form(...), video: UploadFile = File(None)
):

    if session_id not in INTERVIEW_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    session = INTERVIEW_SESSIONS[session_id]

    question = session["questions"][-1]

    # ---------------- AI evaluation ----------------
    result = evaluate_answer(question, answer)

    analysis = result["analysis"]
    score = result["score"]

    difficulty = session["difficulty"]

    current_difficulty = session["difficulty"]

    # calculate difficulty for NEXT question
    next_difficulty = current_difficulty

    if score > 80:
        next_difficulty = "Hard"
    elif score < 40:
        next_difficulty = "Easy"
    else:
        next_difficulty = "Medium"
    # ---------------- Video Analysis ----------------
    video_feedback = None

    if video:
        contents = await video.read()

        video_feedback = analyze_video(contents)

    # store answer
    session["answers"].append(answer)

    # ---------------- Next Question ----------------

    next_question = generate_question(role=session["role"], difficulty=next_difficulty)
    session["difficulty"] = next_difficulty
    session["questions"].append(next_question)
    session["question_number"] += 1

    return {
        "analysis": analysis,
        "video_feedback": video_feedback,
        "next_question": next_question,
        "difficulty": next_difficulty,
        "question_number": session["question_number"],
    }


@app.get("/db/status")
def db_status():
    database_url = os.getenv("DATABASE_URL", "")
    safe_url = database_url
    if "@" in safe_url:
        safe_url = "postgresql://***:***@" + safe_url.split("@", 1)[1]

    return {
        "database": "postgresql",
        "sqlite_disabled": True,
        "users_db_created_by_backend": False,
        "database_url_set": bool(database_url),
        "database_url_preview": safe_url,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
