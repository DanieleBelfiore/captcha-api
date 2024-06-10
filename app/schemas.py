from pydantic import BaseModel


class CaptchaResponse(BaseModel):
    id: int
    image: str


class CaptchaValidation(BaseModel):
    id: int
    text: str
