from base import BaseSkill


class WriterSkill(BaseSkill):
    name = "writer"
    _fallback_prompt = "You are an expert writer. Produce polished, publish-ready content. When given reviewer feedback, revise the draft to address all points."
