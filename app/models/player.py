from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    date_of_birth = Column(DateTime)
    height = Column(Float)  # in cm
    weight = Column(Float)  # in kg
    position = Column(String(50))
    jersey_number = Column(Integer)
    is_active = Column(Boolean, default=True)
    
    # Face recognition fields
    face_image_url = Column(String(255))
    face_encoding = Column(Text)  # JSON string of face encoding
    
    # Foreign key
    subteam_id = Column(Integer, ForeignKey("subteams.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subteam = relationship("SubTeam", back_populates="players")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.full_name}', subteam_id={self.subteam_id})>" 