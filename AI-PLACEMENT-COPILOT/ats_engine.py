import re
from typing import Dict, List, Set, Any
from resume_parser import ResumeParser
from vector_matcher import VectorMatcher


class ATSEngine:
    """
    Hybrid ATS scoring engine combining dense vector semantic similarity
    with exact technical keyword intersection.
    """

    # Curated technical skill dictionary for exact keyword extraction
    SKILL_DATABASE: Set[str] = {
        # Languages
        "python", "java", "c++", "c", "c#", "javascript", "typescript", "html", "css", "sql", "r", "go", "rust",
        # Frameworks & Libraries
        "react", "angular", "vue", "django", "flask", "fastapi", "streamlit", "spring", "spring boot",
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "opencv",
        # Databases & Clouds
        "mysql", "postgresql", "mongodb", "sqlite", "redis", "aws", "azure", "gcp", "docker", "kubernetes",
        # Tools & Concepts
        "git", "github", "rest api", "graphql", "ci/cd", "linux", "data structures", "algorithms",
        "machine learning", "deep learning", "nlp", "llm", "oop", "agile", "jira", "figma", "ui/ux"
    }

    def __init__(self):
        self.parser = ResumeParser()
        self.matcher = VectorMatcher()

    def extract_keywords(self, text: str) -> Set[str]:
        """
        Extracts recognized technical keywords and tools from raw text 
        using exact matching and token boundaries.
        """
        if not text:
            return set()

        text_lower = text.lower()
        found_skills = set()

        for skill in self.SKILL_DATABASE:
            # Match exact phrase or boundary word (handles special characters like c++ and ci/cd)
            escaped_skill = re.escape(skill)
            pattern = rf"(?<!\w){escaped_skill}(?!\w)"
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        return found_skills

    def compute_keyword_match(self, resume_skills: Set[str], jd_skills: Set[str]) -> Dict[str, Any]:
        """
        Calculates exact intersection of skills, missing requirements, 
        and the keyword overlap percentage.
        """
        if not jd_skills:
            return {
                "matched_skills": sorted(list(resume_skills)),
                "missing_skills": [],
                "keyword_score": 100.0
            }

        matched = resume_skills.intersection(jd_skills)
        missing = jd_skills.difference(resume_skills)
        overlap_score = (len(matched) / len(jd_skills)) * 100.0

        return {
            "matched_skills": sorted(list(matched)),
            "missing_skills": sorted(list(missing)),
            "keyword_score": round(overlap_score, 2)
        }

    def evaluate(self, resume_source: str, job_description_text: str) -> Dict[str, Any]:
        """
        Runs the full hybrid ATS evaluation pipeline.
        Formula: ATS Score = (0.70 * Vector Similarity) + (0.30 * Keyword Overlap)
        """
        # 1. Ingest & Parse
        resume_data = self.parser.parse_resume(resume_source)
        cleaned_resume = resume_data["cleaned_text"]
        sections = resume_data["sections"]
        cleaned_jd = self.parser.ingest_job_description(job_description_text)

        # 2. Vector Semantic Similarity (70% Weight)
        vector_sim = self.matcher.calculate_similarity(cleaned_resume, cleaned_jd)

        # 3. Keyword Extraction & Overlap (30% Weight)
        resume_keywords = self.extract_keywords(cleaned_resume)
        jd_keywords = self.extract_keywords(cleaned_jd)
        keyword_result = self.compute_keyword_match(resume_keywords, jd_keywords)
        keyword_score = keyword_result["keyword_score"]

        # 4. Calibrated Hybrid Score
        final_ats_score = round((0.70 * vector_sim) + (0.30 * keyword_score), 2)

        # 5. Section Sub-Scores
        section_vector_scores = self.matcher.compute_section_scores(sections, cleaned_jd)
        
        # Technical Alignment Sub-score (Average of Skills vector score & keyword match)
        skills_vec = section_vector_scores.get("skills_score", 0.0)
        technical_alignment = round((skills_vec * 0.50) + (keyword_score * 0.50), 2)

        # Experience Alignment Sub-score
        experience_alignment = section_vector_scores.get("experience_score", 0.0)

        return {
            "overall_ats_score": final_ats_score,
            "vector_similarity": vector_sim,
            "keyword_score": keyword_score,
            "matched_skills": keyword_result["matched_skills"],
            "missing_skills": keyword_result["missing_skills"],
            "sub_scores": {
                "technical_alignment": technical_alignment,
                "experience_alignment": experience_alignment,
                "projects_alignment": section_vector_scores.get("projects_score", 0.0)
            }
        }


# --- Day 6 Verification Pipeline ---
if __name__ == "__main__":
    import os

    engine = ATSEngine()
    test_pdf = "sample_resume.pdf"
    
    test_jd = """
    Software Engineer - Python / AI
    Required Technical Stack:
    - Strong proficiency in Python, SQL, REST API, Git, and Streamlit.
    - Hands-on experience with PyTorch, Machine Learning, and Data Structures.
    - Familiarity with Docker, PostgreSQL, and AWS is a huge plus.
    """

    if os.path.exists(test_pdf):
        print("🚀 Running Hybrid ATS Scoring Evaluation...\n")
        report = engine.evaluate(test_pdf, test_jd)

        print("=" * 55)
        print("🎯 DAY 6: CALIBRATED HYBRID ATS SCORECARD")
        print("=" * 55)
        print(f"🏆 OVERALL ATS MATCH SCORE: {report['overall_ats_score']}%")
        print("-" * 55)
        print(f" • Semantic Vector Alignment (70%): {report['vector_similarity']}%")
        print(f" • Keyword Overlap Score (30%): {report['keyword_score']}%")
        print("-" * 55)
        print(f"✅ Matched Skills ({len(report['matched_skills'])}): {', '.join(report['matched_skills'])}")
        print(f"❌ Missing Skills ({len(report['missing_skills'])}): {', '.join(report['missing_skills'])}")
        print("-" * 55)
        print("📑 Section Sub-Scores:")
        for sub, score in report["sub_scores"].items():
            print(f" • {sub.replace('_', ' ').title()}: {score}%")
        print("=" * 55)
    else:
        print(f"⚠️ '{test_pdf}' not found. Run make_pdf.py first.")