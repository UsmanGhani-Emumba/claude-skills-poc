import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "2ff01e7f802c8041bb7bf826722f02da")
    ARIZE_SPACE_KEY = os.getenv("ARIZE_SPACE_KEY")
    ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")

    @staticmethod
    def validate():
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing")
        if not Config.NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY is missing")
