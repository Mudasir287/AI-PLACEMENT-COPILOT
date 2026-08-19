import os
from typing import List, Dict, Any, Optional
from llm_client import LLMClient
from schemas import STARBulletPoint
from docx_exporter import DocxResumeExporter


class ResumeGenerator:
    """
    Transforms weak resume statements into metric-driven STAR bullet points
    and seamlessly integrates target job keywords without keyword-stuffing.
    """

    def __init__(self):
        self.llm = LLMClient()
        self.exporter = DocxResumeExporter()

    def rewrite_to_star(
        self,
        weak_bullet: str,
        target_role: str,
        missing_keywords: Optional[List[str]] = None
    ) -> STARBulletPoint:
        """
        Rewrites a single weak bullet point into STAR format, naturally embedding
        missing keywords if provided.
        """
        keywords_instruction = ""
        if missing_keywords:
            keywords_instruction = (
                f"Naturally incorporate 1 or 2 of these missing technical keywords if relevant: "
                f"{', '.join(missing_keywords)}. Do NOT keyword-stuff."
            )

        prompt = f"""
You are an expert ATS Resume Strategist and Technical Recruiter.
Transform this weak resume bullet into a high-impact Situation-Task-Action-Result (STAR) bullet point.

Target Role: {target_role}
Original Bullet: "{weak_bullet}"
{keywords_instruction}

Requirements:
1. Start with a strong action verb.
2. Clearly highlight the technical action and tools used.
3. Include realistic, quantifiable metrics/results (% improved, latency reduced, scale handled).
4. Strictly follow the STAR structure schema.
"""
        return self.llm.generate_structured_output(prompt, STARBulletPoint)

    def optimize_experience_list(
        self,
        bullet_list: List[str],
        target_role: str,
        missing_keywords: Optional[List[str]] = None
    ) -> List[STARBulletPoint]:
        """
        Rewrites a collection of resume bullet points.
        """
        results = []
        for bullet in bullet_list:
            if bullet.strip():
                optimized = self.rewrite_to_star(bullet, target_role, missing_keywords)
                results.append(optimized)
        return results

    def generate_and_export_tailored_resume(
        self,
        candidate_name: str,
        contact_info: str,
        summary: str,
        skills: List[str],
        weak_experience_bullets: List[str],
        target_role: str,
        missing_keywords: List[str],
        education_items: List[str],
        output_filename: str = "tailored_resume.docx"
    ) -> Dict[str, Any]:
        """
        End-to-end pipeline: Rewrites all experience bullets to STAR format with missing skills,
        then compiles and exports the tailored .docx resume.
        """
        print(f"⚙️ Optimizing {len(weak_experience_bullets)} bullets to STAR format for '{target_role}'...")
        star_bullets = self.optimize_experience_list(weak_experience_bullets, target_role, missing_keywords)

        # Merge matched skills with target keywords for a full skill inventory
        updated_skills = sorted(list(set(skills + missing_keywords[:4])))

        optimized_bullet_texts = [b.optimized_bullet for b in star_bullets]

        experience_payload = [
            {
                "role": target_role,
                "company": "Professional Experience",
                "bullets": optimized_bullet_texts
            }
        ]

        file_path = self.exporter.create_resume_document(
            candidate_name=candidate_name,
            contact_info=contact_info,
            summary=summary,
            skills=updated_skills,
            experience_items=experience_payload,
            education_items=education_items,
            output_filepath=output_filename
        )

        return {
            "file_path": file_path,
            "star_breakdown": star_bullets,
            "updated_skills": updated_skills
        }


# --- Day 8 Verification Pipeline ---
if __name__ == "__main__":
    generator = ResumeGenerator()

    sample_weak_bullets = [
        "Worked on backend API endpoints and wrote SQL queries.",
        "Helped make the machine learning model run faster."
    ]

    target_job = "Senior Python AI Engineer"
    missing_skills = ["Docker", "FastAPI", "PyTorch", "AWS"]

    print("\n🚀 DAY 8: TESTING STAR BULLET GENERATION & DOCX EXPORT...")
    print("=" * 60)

    result = generator.generate_and_export_tailored_resume(
        candidate_name="Mudasir Ahmed",
        contact_info="Bengaluru, KA • mudasir@example.com • github.com/mudasir",
        summary="Software Engineer specializing in Python, AI systems, and cloud infrastructure.",
        skills=["Python", "SQL", "Git", "Machine Learning"],
        weak_experience_bullets=sample_weak_bullets,
        target_role=target_job,
        missing_keywords=missing_skills,
        education_items=["B.Tech in Computer Science & Engineering (2020 - 2024)"],
        output_filename="Day8_Tailored_Resume.docx"
    )

    print("\n🎯 GENERATED STAR BULLET POINTS:")
    for idx, star in enumerate(result["star_breakdown"], 1):
        print(f"\n[{idx}] Original: {star.original_point}")
        print(f" Action: {star.action_taken}")
        print(f" Result: {star.result_metric}")
        print(f" ✨ STAR: {star.optimized_bullet}")

    print("\n" + "=" * 60)
    print(f"📄 Tailored Word Document Generated Successfully:")
    print(f"📁 Path: {result['file_path']}")
    print("=" * 60)