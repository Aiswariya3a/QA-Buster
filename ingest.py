import asyncio
import csv
import io
import os
import requests
from dotenv import load_dotenv
from database import SessionLocal, StudentQuestion

load_dotenv()
CSV_URL = os.getenv("CSV_URL", "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv")
INGEST_INTERVAL = int(os.getenv("INGEST_INTERVAL", "5"))


async def fetch_and_ingest_questions():
    """
    Background worker that fetches questions from a public Google Sheet CSV,
    checks for duplicates in the database, and inserts new questions.
    """
    try:
        # Download CSV from URL with timeout
        response = requests.get(CSV_URL, timeout=5)
        response.raise_for_status()
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(response.text))
        
        if csv_reader.fieldnames is None or "Question" not in csv_reader.fieldnames:
            print("Error: CSV does not have 'Question' column")
            return
        
        # Get database session
        db = SessionLocal()
        new_questions_count = 0
        
        try:
            for row in csv_reader:
                question_text = row["Question"].strip()
                
                if not question_text:
                    continue
                
                # Check if question already exists
                existing_question = db.query(StudentQuestion).filter(
                    StudentQuestion.raw_question == question_text
                ).first()
                
                if existing_question is None:
                    # Insert new question
                    new_question = StudentQuestion(
                        raw_question=question_text,
                        is_processed=False,
                        is_approved=False
                    )
                    db.add(new_question)
                    new_questions_count += 1
            
            # Commit all new questions
            if new_questions_count > 0:
                db.commit()
                print(f"Successfully ingested {new_questions_count} new question(s)")
            else:
                print("No new questions found")
        
        finally:
            db.close()
    
    except requests.RequestException as e:
        print(f"Error downloading CSV: {e}")
    except Exception as e:
        print(f"Error during ingestion: {e}")


async def run_ingestion_loop():
    """
    Runs the question ingestion function at the configured interval.
    Starts with a delay to allow frontend to initialize first.
    Never blocks - always keeps running.
    """
    print("Question Ingestion scheduled to start in 2 seconds (allowing frontend to initialize)...")
    
    # Wait 2 seconds to let frontend load first
    await asyncio.sleep(2)
    
    print("Starting Question Ingestion loop...")
    
    retry_count = 0
    while True:
        try:
            await fetch_and_ingest_questions()
            retry_count = 0  # Reset on success
        except requests.exceptions.Timeout:
            retry_count += 1
            print(f"⚠️ Ingestion timeout (attempt {retry_count}): Google Sheets unavailable. Will retry...")
        except Exception as e:
            retry_count += 1
            print(f"⚠️ Ingestion error (attempt {retry_count}): {e}")
        
        await asyncio.sleep(INGEST_INTERVAL)


if __name__ == "__main__":
    print("Starting QA-Buster question ingestion worker...")
    asyncio.run(run_ingestion_loop())
