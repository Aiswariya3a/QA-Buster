import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
import httpx
from database import SessionLocal, StudentQuestion

load_dotenv()

http_client = httpx.Client(timeout=90.0)  # Increased for reasoning models with more tokens
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"),
    api_key=os.getenv("LLM_API_KEY", "lm-studio"),
    http_client=http_client
)

MODEL = os.getenv("LLM_MODEL", "local-model")
LLM_WORKER_INTERVAL = int(os.getenv("LLM_WORKER_INTERVAL", "10"))


async def moderate_question(question: str) -> bool:
    """
    Step 1: Quick moderation check.
    Returns True if inappropriate, False if appropriate.
    """
    try:
        # Clear prompt that asks model to respond with ONLY "APPROPRIATE" or "INAPPROPRIATE"
        moderation_prompt = f"""Check if this student question is appropriate for an engineering Q&A forum. Flag only if it contains: profanity, abuse, spam, or complete nonsense.

Question: {question}

Response (ONLY answer "APPROPRIATE" or "INAPPROPRIATE"):"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": moderation_prompt}
            ],
            temperature=0.0,  # No randomness
            max_tokens=20  # Very limited - we only need one word
        )
        
        message = response.choices[0].message
        result = (message.content or "").strip().upper()
        
        # Debug: print full response
        print(f"    [DEBUG] Raw moderation response: '{result}'")
        
        # If empty, try reasoning_content
        if not result and hasattr(message, 'reasoning_content') and message.reasoning_content:
            reasoning = message.reasoning_content.upper()
            if "INAPPROPRIATE" in reasoning:
                result = "INAPPROPRIATE"
            elif "APPROPRIATE" in reasoning:
                result = "APPROPRIATE"
        
        # Default to appropriate if confused
        is_inappropriate = "INAPPROPRIATE" in result
        status = "❌ REJECT" if is_inappropriate else "✅ ACCEPT"
        print(f"  Moderation: {status}")
        return is_inappropriate
    
    except Exception as e:
        print(f"Error during moderation: {e}")
        return False


async def generate_answer(question: str) -> str:
    """
    Step 2: Generate a fun, roast-filled answer with facts.
    Persona: Sarcastic 4th-year senior who's protective and knowledgeable.
    """
    try:
        system_prompt = """You are a sarcastic, highly caffeinated 4th-year college senior majoring in AI & Data Science. You are talking to a room full of terrified first-year students (freshers) on their very first day. They are submitting anonymous questions about AI to a projector screen.

Your job is to answer them with a fun, friendly "roast" before giving them the actual facts.

RULES for your persona:
1. The Vibe: You are chill, slightly teasing, and use casual college slang. Do not sound like a corporate AI, a textbook, or a boring professor.
2. The Roast: Laugh at their sci-fi movie fears (Terminator, Matrix, robots stealing jobs). Tease them gently for not knowing things, but KEEP IT FRIENDLY. Do not be genuinely mean or discouraging.
3. The Explanation: Explain the reality of AI using simple, college-life analogies (e.g., comparing machine learning to cramming the night before an exam, or comparing AI to a smart but lazy roommate).
4. The Format: Keep it punchy. You are on a projector screen, so limit yourself to 3-4 short sentences maximum. Use markdown for clarity if needed.
5. IMPORTANT - Use SIMPLE ENGLISH: Use short sentences, simple words, avoid technical jargon. Think you're explaining to a 10-year-old, not a PhD. If you must use technical terms, explain them immediately in simple words."""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Student Question: {question}"}
            ],
            temperature=0.8,  # Higher for personality and humor
            max_tokens=600  # Enough for thinking + full answer
        )
        
        message = response.choices[0].message
        
        # Get content first
        answer = (message.content or "").strip()
        
        # If content is empty but we have reasoning, extract from reasoning
        if not answer and hasattr(message, 'reasoning_content') and message.reasoning_content:
            reasoning = message.reasoning_content
            
            # Strategy 1: Look for complete sentences or paragraphs in reasoning
            # Usually the model writes the answer at the END of reasoning
            lines = reasoning.split('\n')
            
            # Find the longest meaningful section (usually the answer)
            best_section = ""
            current_section = ""
            
            for line in lines:
                line = line.strip()
                # Skip thinking markers and short lines
                if any(x in line.lower() for x in ["thinking", "hmm", "wait", "let me", "first"]):
                    if current_section:
                        best_section = current_section
                    current_section = ""
                elif line and not line.startswith("*"):
                    current_section += line + " "
            
            # Use the last/longest section as answer
            if current_section:
                best_section = current_section
            
            answer = best_section.strip()
            
            # If still empty, just take the last part of reasoning
            if not answer:
                answer = reasoning[-500:].strip()
        
        # Clean up answer
        answer = answer.replace("```", "").strip()
        
        # Remove common instruction artifacts
        answer = answer.replace("Answer:", "").replace("answer:", "").strip()
        
        # DON'T TRUNCATE - Return the FULL answer
        # Let the frontend handle display/scrolling
        return answer if answer and len(answer) > 20 else ""
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        import traceback
        traceback.print_exc()
        return ""


async def process_question(question_id: int, raw_question: str):
    """
    Process a single question through moderation and answer generation.
    """
    db = SessionLocal()
    
    try:
        question_record = db.query(StudentQuestion).filter(
            StudentQuestion.id == question_id
        ).first()
        
        if question_record is None:
            print(f"❌ Question {question_id} not found in database")
            return
        
        print(f"\n🔄 Processing Q#{question_id}: '{raw_question[:60]}...'")
        
        # Step 1: Moderation
        is_inappropriate = await moderate_question(raw_question)
        
        if is_inappropriate:
            print(f"  ❌ Flagged as inappropriate")
            question_record.is_processed = True
            question_record.is_approved = False
            db.flush()
            db.commit()
            print(f"  ✓ Saved (rejected)")
        else:
            # Step 2: Generate answer
            print(f"  ✅ Appropriate, generating answer...")
            answer = await generate_answer(raw_question)
            
            if answer:
                question_record.ai_answer = answer
                question_record.is_processed = True
                question_record.is_approved = True
                db.flush()
                db.commit()
                print(f"  ✓ Saved (approved)")
                print(f"  📝 Answer: {answer[:80]}...")
            else:
                print(f"  ⚠️ Failed to generate answer, marking as rejected")
                question_record.is_processed = True
                question_record.is_approved = False
                db.flush()
                db.commit()
                print(f"  ✓ Saved (no answer)")
    
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        db.rollback()
    
    finally:
        db.close()


async def process_unprocessed_questions():
    """
    Query database for unprocessed questions and process each one.
    """
    db = SessionLocal()
    
    try:
        unprocessed = db.query(StudentQuestion).filter(
            StudentQuestion.is_processed == False
        ).all()
        
        if not unprocessed:
            # Silent - no new questions to process
            return
        
        print(f"Found {len(unprocessed)} unprocessed question(s)")
        
        for question in unprocessed:
            try:
                await process_question(question.id, question.raw_question)
            except Exception as q_error:
                print(f"  Error processing Q#{question.id}: {q_error}")
                # Continue with next question instead of crashing
                continue
    
    except Exception as e:
        print(f"⚠️ Error querying unprocessed questions: {e}")
    
    finally:
        try:
            db.close()
        except:
            pass


async def run_llm_worker_loop():
    """
    Main asyncio loop that continuously processes unprocessed questions.
    Starts with a delay to allow frontend to initialize first.
    """
    print("LLM Worker scheduled to start in 3 seconds (allowing frontend to initialize)...")
    
    # Wait 3 seconds to let frontend load first
    await asyncio.sleep(3)
    
    print("Starting LLM Worker...")
    
    # Keep trying even if initial connections fail
    retry_count = 0
    while True:
        try:
            await process_unprocessed_questions()
            retry_count = 0  # Reset on success
        except Exception as e:
            retry_count += 1
            print(f"⚠️ LLM Worker error (attempt {retry_count}): {e}")
            if retry_count >= 5:
                print(f"⚠️ LLM Worker has failed 5 times. Make sure LM Studio is running on localhost:1234")
                retry_count = 0  # Reset counter
        
        await asyncio.sleep(LLM_WORKER_INTERVAL)


if __name__ == "__main__":
    print("LLM Worker starting - Make sure LM Studio is running on localhost:1234")
    asyncio.run(run_llm_worker_loop())
