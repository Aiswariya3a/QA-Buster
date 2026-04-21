# Contributing to QA-Buster

Thank you for your interest in contributing to QA-Buster! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions with other contributors.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/QA-Buster.git
cd QA-Buster
```

### 2. Setup Development Environment

**On macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**On Windows:**
```powershell
setup.bat
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Code Style

- Follow PEP 8 style guide
- Use type hints for function arguments and return values
- Maximum line length: 100 characters
- Use meaningful variable names

### Example:
```python
from typing import Optional, List

def fetch_questions(limit: Optional[int] = None) -> List[dict]:
    """
    Fetch questions from database.
    
    Args:
        limit: Maximum number of questions to return
        
    Returns:
        List of question dictionaries
    """
    # Implementation
    pass
```

### Testing

Before committing, test your changes:

```bash
# Test imports
python -c "import database, ingest, llm_worker, main; print('✓ All imports successful')"

# Test syntax
python -m py_compile database.py ingest.py llm_worker.py main.py

# Run manually to verify functionality
python main.py
```

### Commit Messages

Use clear, descriptive commit messages:

```
Add rate limiting to API endpoints

- Added slowapi middleware
- Configured 100 requests per minute
- Added headers to responses
```

**Commit message conventions:**
- Feature: New functionality
- Bug: Bug fixes
- Docs: Documentation changes
- Refactor: Code refactoring
- Test: Test additions
- Perf: Performance improvements
- Config: Configuration changes

### Pull Request Process

1. **Update your branch with latest main:**
```bash
git fetch origin
git rebase origin/main
```

2. **Push to your fork:**
```bash
git push origin feature/your-feature-name
```

3. **Create Pull Request** with:
   - Clear title describing the change
   - Description of what and why
   - Reference to any related issues
   - Test confirmation

## Project Structure

```
QA-Buster/
├── database.py          # Data models & ORM setup
├── ingest.py           # CSV ingestion worker
├── llm_worker.py       # LLM processing worker
├── main.py             # FastAPI application
├── static/
│   └── index.html      # Frontend
├── requirements.txt    # Dependencies
├── .env.example       # Environment template
├── README.md          # Main documentation
├── DEPLOYMENT.md      # Production deployment guide
└── CONTRIBUTING.md    # This file
```

## Areas for Contribution

### High Priority
- [ ] Add API authentication (JWT tokens)
- [ ] Implement question search/filtering
- [ ] Add admin dashboard
- [ ] Database migration system (Alembic)
- [ ] Unit and integration tests

### Medium Priority
- [ ] Frontend dark mode
- [ ] Export Q&A to PDF
- [ ] Email notifications for new questions
- [ ] Analytics dashboard
- [ ] Question categorization/tagging

### Low Priority
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Question scheduling
- [ ] A/B testing for answer variants

## Bug Reports

Create an issue with:
1. **Description**: What's the bug?
2. **Steps to reproduce**: How do you trigger it?
3. **Expected behavior**: What should happen?
4. **Actual behavior**: What actually happened?
5. **Environment**: OS, Python version, etc.

## Feature Requests

Provide:
1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches?
4. **Examples**: Any mockups or references?

## Documentation

All new features require documentation:
- Update README.md if needed
- Add docstrings to functions
- Comment complex logic
- Update DEPLOYMENT.md for operational changes

### Docstring Format:
```python
def process_question(question_id: int) -> bool:
    """
    Process a question through moderation and answer generation.
    
    This function:
    1. Retrieves the question from the database
    2. Sends it to the LLM for moderation
    3. If appropriate, generates an answer
    4. Updates the database with results
    
    Args:
        question_id: ID of the question to process
        
    Returns:
        True if processing was successful, False otherwise
        
    Raises:
        ValueError: If question_id is invalid
        DatabaseError: If database operation fails
        
    Example:
        >>> success = await process_question(42)
        >>> print(success)
        True
    """
    pass
```

## Security

- Never commit `.env` files with real credentials
- Don't hardcode API keys or passwords
- Report security issues privately to maintainers
- Keep dependencies updated

## Checklist Before Submitting PR

- [ ] Code follows PEP 8 style guide
- [ ] All functions have docstrings
- [ ] Type hints are added
- [ ] Changes tested locally
- [ ] No debug print statements left
- [ ] `.env` and `*.db` not committed
- [ ] Commit messages are descriptive
- [ ] Documentation updated
- [ ] No merge conflicts

## Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Guide](https://docs.sqlalchemy.org/)
- [AsyncIO Tutorial](https://docs.python.org/3/library/asyncio.html)
- [PEP 8 Style Guide](https://pep8.org/)
- [Git Workflow](https://git-scm.com/book/en/v2)

## Questions?

- Open a GitHub Discussion
- Create an issue with [QUESTION] prefix
- Join our community chat

## Recognition

Contributors are acknowledged in:
- README.md contributors section
- GitHub Contributors page
- Release notes

---

Thank you for contributing to QA-Buster!
