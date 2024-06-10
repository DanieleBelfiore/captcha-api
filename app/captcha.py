import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
from pytest import Session
from app.models import Captcha


def generate_random_text(length: int = 6) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def generate_captcha_image(text: str) -> str:
    image = Image.new("RGB", (200, 60), color=(255, 255, 255))
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), text, font=font, fill=(0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_captcha(db: Session) -> tuple:
    text = generate_random_text()
    image = generate_captcha_image(text)
    captcha = Captcha(text=text)
    db.add(captcha)
    db.commit()
    db.refresh(captcha)
    return captcha.id, image


def get_captcha_text(db: Session, id: int) -> str:
    captcha = db.query(Captcha).filter(Captcha.id == id).first()
    if captcha:
        return captcha.text
    else:
        return None


def validate_captcha_text(db: Session, id: int, text: str) -> bool:
    return get_captcha_text(db, id) == text
