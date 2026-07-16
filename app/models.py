from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base, engine


class Captcha(Base):
    __tablename__ = "captchas"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)
