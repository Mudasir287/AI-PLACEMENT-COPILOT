from pydantic import BaseModel, Field
from typing import List, Optional


class STARBulletPoint(BaseModel):
    """Structured STAR-format resume bullet point."""
    original_point: str = Field(description="The candidate's original resume bullet point")
    situation_task: str = Field(description="Context and challenge/responsibility faced")
    action_taken: str = Field(description="Action taken, including relevant tools/technologies")
    result_metric: str = Field(description="Quantifiable business/technical result or impact")
    optimized_bullet: str = Field(description="Final polished STAR bullet point ready for resume")


class SkillGapReport(BaseModel):
    """Detailed candidate skill gap diagnostic."""
    overall_assessment: str = Field(description="Brief assessment of candidate fit for the job")
    matched_skills: List[str] = Field(description="Skills present in both resume and job description")
    missing_critical_skills: List[str] = Field(description="High-priority missing technologies")
    missing_nice_to_have: List[str] = Field(description="Bonus/secondary missing tools")
    recommended_improvements: List[str] = Field(description="Actionable steps to bridge the gap")


class InterviewQuestion(BaseModel):
    """Targeted technical interview question."""
    question_id: int = Field(description="Question sequence index")
    targeted_skill: str = Field(description="The detected skill gap this question evaluates")
    difficulty: str = Field(description="Easy, Medium, or Hard")
    question_text: str = Field(description="The technical or behavioral interview question")
    ideal_answer_points: List[str] = Field(description="Key talking points an interviewer looks for")


class AnswerEvaluation(BaseModel):
    """Evaluation score and actionable feedback for candidate's interview answer."""
    score_out_of_10: float = Field(description="Technical accuracy score from 1.0 to 10.0")
    strengths: List[str] = Field(description="What the candidate explained well")
    missing_concepts: List[str] = Field(description="Key technical concepts left out")
    improved_sample_answer: str = Field(description="An exemplar response to the question")

