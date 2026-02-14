import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PARENT_ID = os.getenv("NOTION_PARENT_ID")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5-20250929")
MAX_TOKENS = 16384
CONTEXT_WINDOW = 200_000

# Cost per 1K tokens (Sonnet 4.5 pricing)
INPUT_COST_PER_1K = 0.003
OUTPUT_COST_PER_1K = 0.015
