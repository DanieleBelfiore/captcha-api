from sqlalchemy import Column, Integer, String
from app.database import Base, engine


class Captcha(Base):
    __tablename__ = "captchas"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)


Base.metadata.create_all(bind=engine)
