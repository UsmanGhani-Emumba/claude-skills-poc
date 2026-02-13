import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-opus-4-6")
MAX_TOKENS = 16384
CONTEXT_WINDOW = 200_000

# Cost per 1K tokens (update with actual Opus 4.6 pricing)
INPUT_COST_PER_1K = 0.015
OUTPUT_COST_PER_1K = 0.075
