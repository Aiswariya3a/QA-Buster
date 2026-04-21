import asyncio
import os
from contextlib import asynccontextmanager
from typing import List
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import SessionLocal, StudentQuestion, init_db
from ingest import run_ingestion_loop
from llm_worker import run_llm_worker_loop

load_dotenv()

# Load configuration from environment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"


# Pydantic models for responses
class QuestionResponse(BaseModel):
    id: int
    raw_question: str
    ai_answer: str | None

    class Config:
        from_attributes = True


class StatusResponse(BaseModel):
    count: int


# Background tasks
background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup event: Launch background worker loops for ingestion and LLM processing.
    Frontend loads immediately, workers start in background.
    """
    # Initialize database (quick operation)
    init_db()
    print("✅ Database initialized")
    
    # Create tasks for background workers (non-blocking)
    print("🚀 Starting QA-Buster Backend...")
    ingest_task = asyncio.create_task(run_ingestion_loop())
    llm_worker_task = asyncio.create_task(run_llm_worker_loop())
    
    background_tasks.append(ingest_task)
    background_tasks.append(llm_worker_task)
    
    print("✅ Backend ready! Frontend is available now.")
    print("   - Question ingestion starts in 2 seconds")
    print("   - LLM processing starts in 3 seconds")
    
    yield
    
    # Shutdown event: Cancel background tasks
    print("Shutting down background workers...")
    for task in background_tasks:
        task.cancel()


# Initialize FastAPI app with lifespan
app = FastAPI(title="QA-Buster Backend", lifespan=lifespan)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount QR codes folder
app.mount("/qr", StaticFiles(directory="qr"), name="qr")


@app.get("/")
async def root():
    """
    Serve the frontend index.html
    """
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """
    Health check endpoint - returns quickly to verify backend is responding.
    """
    return {
        "status": "ok",
        "message": "Backend is running and responding"
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get the count of approved questions.
    """
    db = SessionLocal()
    try:
        count = db.query(StudentQuestion).filter(
            StudentQuestion.is_approved == True
        ).count()
        return StatusResponse(count=count)
    finally:
        db.close()


@app.get("/questions", response_model=List[QuestionResponse])
async def get_questions():
    """
    Get all approved questions with their answers.
    """
    db = SessionLocal()
    try:
        questions = db.query(StudentQuestion).filter(
            StudentQuestion.is_approved == True
        ).all()
        print(f"✓ API /questions: Returning {len(questions)} approved questions")
        for q in questions:
            print(f"  - Q{q.id}: {q.raw_question[:40]}... (answer: {len(q.ai_answer or '')} chars)")
        return questions
    except Exception as e:
        print(f"ERROR in /questions endpoint: {e}")
        raise
    finally:
        db.close()


@app.get("/debug/all-questions")
async def debug_all_questions():
    """
    Debug endpoint: Show all questions regardless of status
    """
    db = SessionLocal()
    try:
        all_questions = db.query(StudentQuestion).all()
        result = []
        for q in all_questions:
            result.append({
                "id": q.id,
                "question": q.raw_question[:50] if q.raw_question else "N/A",
                "is_processed": q.is_processed,
                "is_approved": q.is_approved,
                "has_answer": q.ai_answer is not None,
                "answer_preview": (q.ai_answer[:50] + "...") if q.ai_answer else None
            })
        print(f"DEBUG: Total questions in DB: {len(all_questions)}")
        print(f"DEBUG: Approved questions: {sum(1 for q in all_questions if q.is_approved)}")
        for r in result:
            print(f"  - {r}")
        return {"total": len(all_questions), "questions": result}
    finally:
        db.close()


@app.post("/debug/add-test-question")
async def add_test_question():
    """
    Debug endpoint: Add a test question that's already approved
    """
    db = SessionLocal()
    try:
        test_question = StudentQuestion(
            raw_question="Why is engineering awesome? (TEST)",
            is_processed=True,
            is_approved=True,
            ai_answer="Because engineering shapes the world! 🚀"
        )
        db.add(test_question)
        db.commit()
        print(f"✓ Test question added (ID: {test_question.id})")
        return {"success": True, "id": test_question.id, "message": "Test question added and approved"}
    except Exception as e:
        print(f"ERROR adding test question: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    if DEBUG:
        # Use string import for reload mode
        uvicorn.run("main:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=True)
    else:
        # Use app object for production
        uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT, reload=False)
