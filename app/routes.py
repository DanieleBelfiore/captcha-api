from fastapi import APIRouter, Depends
from pytest import Session
from app.database import get_db
from app.schemas import CaptchaResponse, CaptchaValidation
from app.captcha import generate_captcha, validate_captcha_text

router = APIRouter(prefix="/captcha", tags=["Captcha"])


@router.get(
    "",
    response_model=CaptchaResponse,
    summary="Generate a new captcha",
    description="This endpoint generates a new captcha and returns the captcha ID and image.",
)
def get_captcha(db: Session = Depends(get_db)):
    id, image = generate_captcha(db)
    return {"id": id, "image": image}


@router.post(
    "/validate",
    response_model=bool,
    summary="Validate a captcha",
    description="This endpoint validates the provided captcha text against the captcha ID.",
)
def validate_captcha(input: CaptchaValidation, db: Session = Depends(get_db)):
    return validate_captcha_text(db, input.id, input.text)
