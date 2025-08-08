from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    coach_name = Column(String(100))
    logo_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subteams = relationship("SubTeam", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>" 