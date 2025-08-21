import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _get_allowed_origins() -> list[str]:
    env = os.environ.get("ALLOWED_ORIGINS", "*").strip()
    if env == "*" or not env:
        return ["*"]
    return [o.strip() for o in env.split(",") if o.strip()]


app = FastAPI(title="Obserra Backend API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"name": "Obserra Backend API", "endpoints": ["/health"]}


