from base import BaseSkill


class ReviewerSkill(BaseSkill):
    name = "reviewer"
    _fallback_prompt = "You are an expert content reviewer. Evaluate content for quality, accuracy, and clarity. Return a score and APPROVED or NEEDS_REVISION verdict."
