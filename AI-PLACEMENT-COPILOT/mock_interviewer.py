"""
mock_interviewer.py
Randomized, role-adaptive LLM interview generator and dynamic answer evaluator.
"""

import json
import os
import random
import re
import time
from typing import Any, List
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


class InterviewQuestion(BaseModel):
    question_text: str = Field(description="The interview question text.")
    targeted_skill: str = Field(description="The primary technical skill or competency tested.")
    difficulty: str = Field(default="Mid-Level", description="Difficulty level.")
    ideal_answer_points: List[str] = Field(default_factory=list, description="Key points expected in a strong answer.")


class AnswerEvaluation(BaseModel):
    score_out_of_10: float = Field(description="Score between 0.0 and 10.0.")
    strengths: List[str] = Field(description="Specific strengths demonstrated in candidate's response.")
    missing_concepts: List[str] = Field(description="Key concepts or trade-offs missed.")
    improved_sample_answer: str = Field(description="High-impact exemplar answer.")


class MockInterviewer:
    def __init__(self, model_name: str = "gemini-3.5-flash"):
        self.model_name = model_name

    def generate_questions(self, *args, **kwargs) -> List[InterviewQuestion]:
        # Extract parameters flexibly
        role = "Software Engineer"
        skills = []
        count = 3

        if len(args) >= 1 and isinstance(args[0], str):
            role = args[0]
        if len(args) >= 2:
            if isinstance(args[1], (list, tuple, set)):
                skills = list(args[1])
            elif isinstance(args[1], str):
                skills = [s.strip() for s in args[1].split(",") if s.strip()]
        if len(args) >= 3 and isinstance(args[2], int):
            count = args[2]

        if "role" in kwargs and isinstance(kwargs["role"], str):
            role = kwargs["role"]
        if "target_role" in kwargs and isinstance(kwargs["target_role"], str):
            role = kwargs["target_role"]
        if "skills" in kwargs:
            val = kwargs["skills"]
            if isinstance(val, (list, tuple, set)):
                skills = list(val)
            elif isinstance(val, str):
                skills = [s.strip() for s in val.split(",") if s.strip()]
        if "question_count" in kwargs and isinstance(kwargs["question_count"], int):
            count = kwargs["question_count"]

        safe_skills = [str(s) for s in skills if s]
        skills_str = ", ".join(safe_skills) if safe_skills else f"Core Architecture & Workflow for {role}"

        # Inject dynamic entropy and question style directives
        question_styles = [
            "Practical real-world debugging / incident post-mortem scenario",
            "System architecture design trade-off & scalability challenge",
            "Tooling / workflow optimization & performance tuning",
            "Cross-functional edge-case resolution under constraints",
            "Deep architectural deep-dive into internal mechanics"
        ]
        random.shuffle(question_styles)
        selected_style = question_styles[0]
        session_seed = int(time.time() * 1000) % 100000

        prompt = f"""
You are a Staff Hiring Committee Lead conducting an advanced, highly tailored technical interview.
Target Role: {role}
Target Skill Areas: {skills_str}
Question Style Angle: {selected_style}
Session Entropy Seed: {session_seed}

INSTRUCTIONS:
1. Generate exactly {count} distinct, challenging, completely randomized scenario questions.
2. DO NOT use generic questions (e.g. avoid 'What is X?' or 'Walk me through a project'). Instead, pose concrete real-world dilemmas, architectural trade-offs, and technical edge cases.
3. Each question must target a different specific aspect of '{skills_str}'.
4. Return strictly a JSON object matching this schema:
{{
  "questions": [
    {{
      "question_text": "Detailed situational scenario question...",
      "targeted_skill": "Specific skill name",
      "difficulty": "Mid-Level",
      "ideal_answer_points": [
        "Concrete technical expectation 1",
        "Concrete technical expectation 2",
        "Concrete trade-off or metric 3"
      ]
    }}
  ]
}}
"""
        try:
            model = genai.GenerativeModel(self.model_name)
            resp = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.85,
                    "top_p": 0.95
                }
            )
            data = json.loads(resp.text)
            qs = [InterviewQuestion(**q) for q in data.get("questions", [])]
            if len(qs) >= count:
                return qs[:count]
        except Exception as e:
            print(f"[Gemini API Question Generation Warning]: {e}")

        # Dynamic randomized fallback templates
        pool_skills = safe_skills if safe_skills else ["Core Architecture", "Performance", "Workflow", "Testing"]
        templates = [
            ("How do you architect and enforce {skill} standards across a distributed multi-team codebase when dealing with rapid sprint delivery?", "Junior-to-Mid"),
            ("Suppose a critical production bottleneck occurs in your {skill} pipeline under 5x normal peak load. Walk me through your diagnostic and mitigation strategy.", "Mid-Level"),
            ("What trade-offs do you evaluate when choosing between standard industry patterns versus customized implementations in {skill}?", "Senior"),
            ("How do you design an automated validation and regression suite specifically around {skill} to prevent regressions during CI/CD?", "Mid-Level"),
            ("Describe a concrete scenario where technical constraints forced you to compromise on {skill} fidelity, and how you communicated that to stakeholders.", "Senior")
        ]
        random.shuffle(templates)

        fallbacks = []
        for i in range(count):
            skill_focus = pool_skills[i % len(pool_skills)]
            tpl, diff = templates[i % len(templates)]
            fallbacks.append(
                InterviewQuestion(
                    question_text=tpl.format(skill=skill_focus),
                    targeted_skill=skill_focus,
                    difficulty=diff,
                    ideal_answer_points=[
                        f"Demonstrated domain depth in {skill_focus}",
                        "Structured problem-solving & isolation of root cause",
                        "Quantifiable metrics and business impact consideration"
                    ]
                )
            )
        return fallbacks[:count]

    def evaluate_candidate_answer(self, *args, **kwargs) -> AnswerEvaluation:
        question = args[0] if len(args) > 0 else kwargs.get("question", "")
        targeted_skill = args[1] if len(args) > 1 else kwargs.get("targeted_skill", "")
        candidate_answer = args[2] if len(args) > 2 else kwargs.get("candidate_answer", "")
        ideal_points = args[3] if len(args) > 3 else kwargs.get("ideal_points", ["Technical depth", "Clarity"])

        clean_ans = candidate_answer.strip()
        words = clean_ans.split()

        # Low-effort and gibberish detection
        gibberish_patterns = [r"^(.)\1{3,}$", r"^[a-zA-Z]{1,3}$"]
        is_repetitive = any(re.match(p, clean_ans) for p in gibberish_patterns)

        if len(words) < 4 or len(clean_ans) < 12 or is_repetitive:
            return AnswerEvaluation(
                score_out_of_10=1.0,
                strengths=["Submitted an answer input"],
                missing_concepts=[
                    f"Response does not address the question on {targeted_skill}.",
                    "Missing domain concepts, architecture explanation, or methodologies.",
                    "Lacks sufficient technical depth for evaluation."
                ],
                improved_sample_answer=f"A strong answer for {targeted_skill} should detail the specific tools used, step-by-step workflow, and measurable outcomes."
            )

        prompt = f"""
You are an expert Technical Interview Evaluator.
Interview Question: "{question}"
Focus Skill: "{targeted_skill}"
Expected Core Concepts: {ideal_points}

Candidate Response: "{candidate_answer}"

EVALUATION CRITERIA:
1. Score strictly between 1.0 and 10.0 based solely on how accurately and deeply the candidate addressed the specific question.
2. If the candidate gives vague, generic, or off-topic statements, penalize the score accordingly (3.0 - 5.0).
3. If the candidate provides technical terminology, concrete steps, trade-offs, and methodologies, reward with 7.5 - 9.5.
4. List 2-3 genuine strengths based directly on what they wrote.
5. List 2-3 specific technical concepts they missed or failed to elaborate on.
6. Provide an articulate exemplar answer.

Return strictly a JSON object matching this schema:
{{
  "score_out_of_10": 7.0,
  "strengths": ["Strength 1...", "Strength 2..."],
  "missing_concepts": ["Missed concept 1...", "Missed concept 2..."],
  "improved_sample_answer": "Complete exemplar answer..."
}}
"""
        try:
            model = genai.GenerativeModel(self.model_name)
            resp = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3
                }
            )
            data = json.loads(resp.text)
            return AnswerEvaluation(**data)
        except Exception as e:
            print(f"[Gemini API Evaluation Warning]: {e}")
            # Dynamic heuristic evaluation fallback
            has_keywords = any(kw.lower() in clean_ans.lower() for kw in targeted_skill.split())
            heuristic_score = 6.5 if has_keywords and len(words) > 15 else 4.0

            return AnswerEvaluation(
                score_out_of_10=heuristic_score,
                strengths=[
                    f"Mentioned core elements related to {targeted_skill}",
                    "Structured communication format"
                ] if heuristic_score >= 6.0 else ["Attempted initial response"],
                missing_concepts=[
                    f"Could provide concrete real-world metrics when applying {targeted_skill}",
                    "Did not discuss performance trade-offs or edge-case handling"
                ],
                improved_sample_answer=f"When executing {targeted_skill}, I start with requirements discovery, implement modular components, and measure effectiveness using clear KPIs."
            )
