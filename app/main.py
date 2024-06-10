from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.routes import router

app = FastAPI(
    title="Captcha API",
    summary="API to manage the captchas.",
    version="1.0.0",
    docs_url="/swagger",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def swagger():
    return RedirectResponse(url="/swagger")


app.include_router(router)
