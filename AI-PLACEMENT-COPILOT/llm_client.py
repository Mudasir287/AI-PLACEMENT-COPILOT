import os
import warnings
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import Type, TypeVar
from pydantic import BaseModel

from schemas import (
    STARBulletPoint,
    SkillGapReport,
    InterviewQuestion,
    AnswerEvaluation
)

# Suppress cosmetic SDK function-calling notice for clean terminal output
warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

load_dotenv()

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    Google GenAI client wrapper guaranteeing structured JSON outputs
    validated against Pydantic schemas.
    """

    def __init__(self, model_name: str = "gemini-3.6-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name

        if not api_key or "your_actual" in api_key:
            print("⚠️ GEMINI_API_KEY not configured in .env. Using mock fallback.")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=api_key)
                print(f"✅ Gemini API client active (using: {self.model_name}).")
            except Exception as e:
                print(f"⚠️ Initialization error: {e}")
                self.client = None

    def generate_structured_output(self, prompt: str, schema_class: Type[T]) -> T:
        """Sends prompt to Gemini with native Pydantic schema enforcement."""
        if not self.client:
            return self._mock_fallback(schema_class)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema_class,
                ),
            )
            if hasattr(response, "parsed") and response.parsed:
                return response.parsed
            return schema_class.model_validate_json(response.text)
        except Exception as e:
            print(f"⚠️ Live API call error: {e}. Using fallback data.")
            return self._mock_fallback(schema_class)

    def _mock_fallback(self, schema_class: Type[T]) -> T:
        """Offline fallback data."""
        if schema_class == STARBulletPoint:
            return STARBulletPoint(
                original_point="Worked on Python backend and APIs.",
                situation_task="Needed to build scalable ATS matching backend.",
                action_taken="Developed asynchronous REST endpoints using Python, PyMuPDF, and FastAPI.",
                result_metric="Reduced resume parsing latency to <0.05 seconds with 98% accuracy.",
                optimized_bullet="Architected high-throughput Python REST backend with PyMuPDF, reducing document parsing latency to 0.05s."
            )
        elif schema_class == SkillGapReport:
            return SkillGapReport(
                overall_assessment="Strong foundation in Python; needs cloud deployment exposure.",
                matched_skills=["Python", "Git", "REST APIs", "Streamlit"],
                missing_critical_skills=["Docker", "AWS", "PostgreSQL"],
                missing_nice_to_have=["Redis", "CI/CD"],
                recommended_improvements=["Containerize application using Docker", "Deploy to AWS EC2"]
            )
        raise ValueError(f"No mock defined for schema: {schema_class}")


# --- Day 7 Verification Pipeline ---
if __name__ == "__main__":
    client = LLMClient()

    print("\n🚀 Testing Structured STAR Bullet Point Generator Schema...")
    test_prompt = "Rewrite this resume bullet using the STAR method for a Python Developer: 'Made a resume scanner script.'"
    star_result = client.generate_structured_output(test_prompt, STARBulletPoint)

    print("=" * 55)
    print("🎯 DAY 7: VALIDATED STAR BULLET POINT SCHEMA OUTPUT")
    print("=" * 55)
    print(f"📝 Original: {star_result.original_point}")
    print(f"✨ Optimized: {star_result.optimized_bullet}")
    print(f"📊 Result: {star_result.result_metric}")
    print("=" * 55)

