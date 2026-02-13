from base import BaseSkill


class ResearcherSkill(BaseSkill):
    name = "researcher"
    _fallback_prompt = "You are an expert researcher. Analyze topics thoroughly, identify key facts, statistics, and multiple perspectives. Output a structured research brief."
