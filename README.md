# QA-Buster

A scalable backend system for ingesting, moderating, and answering first-year engineering student questions using local LLM models.

## Overview

QA-Buster is a three-tier asynchronous application:

1. **Ingest Worker** - Continuously fetches new questions from a public Google Sheet CSV
2. **LLM Worker** - Processes questions through moderation and generates encouraging answers
3. **FastAPI Backend** - Serves a clean REST API and static frontend

The system automatically handles duplicate detection, content moderation, and answer generation with zero manual intervention.

## Architecture

```
┌─────────────────────────────────────┐
│      Google Sheet (CSV)             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      Ingest Worker (ingest.py)      │
│   - Fetch CSV every 5 seconds       │
│   - Detect duplicates               │
│   - Insert new questions            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    SQLite Database (qa_buster.db)   │
│  StudentQuestion table              │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
    ┌───────────┐  ┌───────────────┐
    │ LLM Worker│  │ FastAPI App   │
    │(llm_...)  │  │  (main.py)    │
    │           │  │               │
    │-Moderate  │  ├─/status       │
    │-Generate  │  ├─/questions    │
    │-Update DB │  └─/static/*     │
    └─────┬─────┘  └────────┬──────┘
          │                 │
          └────────┬────────┘
                   │
                   ▼
         ┌──────────────────┐
         │  Frontend (HTML) │
         │ - Poll /status   │
         │ - Display Q&A    │
         └──────────────────┘
```

## Prerequisites

- Python 3.8+
- SQLite (included with Python)
- [LM Studio](https://lmstudio.ai) running locally (optional for local LLM)
- A public Google Sheet with a "Question" column

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
- `CSV_URL` - Your Google Sheet export URL
- `DATABASE_URL` - SQLite database path
- `LLM_BASE_URL` - LM Studio server address
- `FASTAPI_HOST` - Server host
- `FASTAPI_PORT` - Server port

### 3. Start LM Studio (Optional)

1. Download [LM Studio](https://lmstudio.ai)
2. Load your preferred model
3. Start the local server on the configured port

### 4. Run the Application

```bash
python main.py
```

The system will:
- Initialize the database
- Start FastAPI on `http://localhost:8000`
- Launch ingest worker (CSV polling)
- Launch LLM worker (question processing)
- Serve frontend at `/`

### 5. Access the Frontend

Open your browser to `http://localhost:8000`

## Project Structure

```
QA-Buster/
├── database.py          # SQLAlchemy models & database config
├── ingest.py           # CSV ingestion worker
├── llm_worker.py       # LLM moderation & answer generation
├── main.py             # FastAPI application
├── static/
│   └── index.html      # Frontend UI
├── requirements.txt    # Python dependencies
├── .env               # Environment configuration (gitignored)
├── .env.example       # Environment template
├── README.md          # This file
└── qa_buster.db       # SQLite database (auto-created)
```

## Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=sqlite:///./qa_buster.db

# CSV Ingestion
CSV_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv
INGEST_INTERVAL=5

# LLM Configuration
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=local-model
LLM_WORKER_INTERVAL=10

# FastAPI Server
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
DEBUG=False

# CORS Settings
CORS_ORIGINS=*
```

## API Endpoints

### GET `/status`
Returns count of approved questions.

**Response:**
```json
{
  "count": 42
}
```

### GET `/questions`
Returns all approved questions with answers.

**Response:**
```json
[
  {
    "id": 1,
    "raw_question": "Why is thermodynamics so hard?",
    "ai_answer": "Great question! Thermodynamics can feel overwhelming..."
  },
  ...
]
```

### GET `/` (Static Files)
Serves the frontend HTML, CSS, and JavaScript.

## Data Flow

### Ingest Process
1. Fetch CSV from Google Sheet every 5 seconds
2. Parse rows with "Question" column
3. Check database for duplicates
4. Insert new questions with `is_processed=False`

### LLM Processing
1. Query unprocessed questions every 10 seconds
2. **Step 1: Moderation** - Check for profanity/gibberish
   - If inappropriate → mark `is_approved=False`
   - If appropriate → proceed to Step 2
3. **Step 2: Answer Generation** - Generate encouraging response as AI mythbuster
   - Store answer and mark `is_processed=True`, `is_approved=True`

### Frontend Flow
1. **Lobby State** - Poll `/status` every 2 seconds, show question count
2. **Question State** - Fetch `/questions`, display first question
3. **Answer State** - Slide in AI answer, navigate through Q&A pairs

## Database Schema

### StudentQuestion Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| raw_question | String | Original question text |
| is_processed | Boolean | Processing complete |
| is_approved | Boolean | Passed moderation |
| ai_answer | String | Generated answer (nullable) |

## Moderation Prompts

### Step 1: Moderation Prompt
```
You are a strict content moderator. Analyze the following question and reply with ONLY TRUE or FALSE.

TRUE = The question contains profanity, gibberish, or is inappropriate
FALSE = The question is appropriate and coherent

Question: {question}

Reply with only TRUE or FALSE:
```

### Step 2: Answer Generation Prompt
```
You are an encouraging AI mythbuster helping first-year engineering students.
Your job is to answer questions in a fun, reassuring, and accessible way.
Keep answers concise but insightful. Make the topic feel exciting and demystify concerns.

Student Question: {question}

Provide a helpful, fun, and encouraging answer:
```

## Development

### Adding Custom Moderation Rules

Edit `llm_worker.py` in the `moderate_question()` function to add additional validation before LLM calls.

### Changing CSV Source

Update `CSV_URL` in `.env` to point to a different Google Sheet.

### Customizing Answer Tone

Modify the `answer_prompt` in `llm_worker.py` to change the AI's personality.

### Adjusting Polling Intervals

Change `INGEST_INTERVAL` and `LLM_WORKER_INTERVAL` in `.env`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No questions appearing | Check CSV_URL is correct and public; wait for ingest cycle |
| LLM errors | Ensure LM Studio is running on configured port |
| Database locked | Delete `qa_buster.db` and restart |
| CORS errors | Verify CORS_ORIGINS in .env |
| Slow performance | Increase polling intervals in .env |

## Monitoring

Monitor logs in console output:
- `[ingest.py]` - CSV fetch and insert operations
- `[llm_worker.py]` - Moderation and answer generation
- `[main.py]` - FastAPI startup and API requests

## Production Deployment

### For Production:

1. Use PostgreSQL instead of SQLite:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/qa_buster
   ```

2. Use a production ASGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

3. Configure proper CORS origins:
   ```env
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. Set DEBUG to False:
   ```env
   DEBUG=False
   ```

5. Use environment-specific secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)

6. Add monitoring and logging:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

## License

MIT License - feel free to use this for your engineering student community!

## Contributing

Pull requests welcome! Please follow the existing code style and add tests for new features.

## Support

For issues or questions, open a GitHub issue or contact the development team.

---

**Built with ❤️ for first-year engineering students**
