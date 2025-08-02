"""Database models for Kruzhok Bot"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class UserHistory(Base):
    """Model to store user's kruzhok video history"""
    __tablename__ = 'user_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    file_id = Column(String(200), nullable=False)  # Telegram file_id for kruzhok
    original_media_type = Column(String(20), nullable=False)  # 'video' or 'photo'
    effect_type = Column(Integer, nullable=False)  # 1-5 effect types
    effect_name = Column(String(50), nullable=False)  # Effect name in Uzbek
    created_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    def __repr__(self):
        return f"<UserHistory(user_id={self.user_id}, effect={self.effect_name}, created_at={self.created_at})>"

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """Get database session"""
    return SessionLocal()

def save_user_history(user_id, username, first_name, file_id, original_media_type, effect_type, effect_name, file_size=None):
    """Save user's kruzhok to history"""
    session = get_db_session()
    try:
        history_entry = UserHistory(
            user_id=user_id,
            username=username,
            first_name=first_name,
            file_id=file_id,
            original_media_type=original_media_type,
            effect_type=effect_type,
            effect_name=effect_name,
            file_size=file_size
        )
        session.add(history_entry)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving history: {e}")
        return False
    finally:
        session.close()

def get_user_history(user_id, limit=10):
    """Get user's recent kruzhok history"""
    session = get_db_session()
    try:
        history = session.query(UserHistory).filter(
            UserHistory.user_id == user_id
        ).order_by(
            UserHistory.created_at.desc()
        ).limit(limit).all()
        return history
    except Exception as e:
        print(f"Error getting history: {e}")
        return []
    finally:
        session.close()

def get_total_user_kruzhoks(user_id):
    """Get total count of user's kruzhoks"""
    session = get_db_session()
    try:
        count = session.query(UserHistory).filter(
            UserHistory.user_id == user_id
        ).count()
        return count
    except Exception as e:
        print(f"Error getting count: {e}")
        return 0
    finally:
        session.close()