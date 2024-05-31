from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from quipubase import create_app

app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
