from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SubTeam(Base):
    __tablename__ = "subteams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="subteams")
    players = relationship("Player", back_populates="subteam", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SubTeam(id={self.id}, name='{self.name}', team_id={self.team_id})>" 