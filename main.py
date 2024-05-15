from dotenv import load_dotenv
from fastapi import Request

load_dotenv()

from quipubase import create_app

app = create_app()


@app.get("/")
def root(request: Request):
    return dict(request.headers)
