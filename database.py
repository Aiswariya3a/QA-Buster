import os
from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./qa_buster.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class StudentQuestion(Base):
    __tablename__ = "student_questions"

    id = Column(Integer, primary_key=True, index=True)
    raw_question = Column(String, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    ai_answer = Column(String, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)
