from dotenv import load_dotenv

load_dotenv()

from quipubase import create_app

app = create_app()
