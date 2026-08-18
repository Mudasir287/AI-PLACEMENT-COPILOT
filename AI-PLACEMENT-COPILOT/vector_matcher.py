import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict


class VectorMatcher:
    """
    Computes 384-dimensional dense vector embeddings and semantic cosine similarity 
    between resumes and target job descriptions.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initializes the lightweight all-MiniLM-L6-v2 sentence transformer model."""
        print(f"🔄 Initializing dense embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("✅ Vector model ready.\n")

    def get_embedding(self, text: str) -> np.ndarray:
        """Generates a 384-dimensional dense vector representation of input text."""
        if not text or not text.strip():
            return np.zeros((384,), dtype=np.float32)
        return self.model.encode(text, convert_to_numpy=True)

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculates cosine similarity between two text strings.
        Outputs a calibrated semantic alignment score scaled from 0.0% to 100.0%.
        """
        if not text_a.strip() or not text_b.strip():
            return 0.0

        vec_a = self.get_embedding(text_a).reshape(1, -1)
        vec_b = self.get_embedding(text_b).reshape(1, -1)

        raw_score = float(cosine_similarity(vec_a, vec_b)[0][0])
        match_percentage = max(0.0, raw_score) * 100.0
        return round(match_percentage, 2)

    def compute_section_scores(self, sections: Dict[str, str], job_description: str) -> Dict[str, float]:
        """Calculates semantic match percentages for individual resume sections."""
        section_scores = {}
        for section_name in ["skills", "experience", "projects"]:
            content = sections.get(section_name, "")
            if content:
                section_scores[f"{section_name}_score"] = self.calculate_similarity(content, job_description)
            else:
                section_scores[f"{section_name}_score"] = 0.0

        return section_scores


# --- Day 5 Verification Pipeline ---
if __name__ == "__main__":
    import os
    from resume_parser import ResumeParser

    parser = ResumeParser()
    matcher = VectorMatcher()

    test_pdf = "sample_resume.pdf"
    test_job_description = """
    We are looking for a Python Developer with experience in:
    - Building REST APIs and Streamlit web applications.
    - Git version control and writing clean, modular Python scripts.
    - Basic understanding of PyTorch, Machine Learning, and Data Structures.
    """

    if os.path.exists(test_pdf):
        # Ingest Resume & Job Description
        parsed_resume = parser.parse_resume(test_pdf)
        cleaned_resume = parsed_resume["cleaned_text"]
        resume_sections = parsed_resume["sections"]
        cleaned_jd = parser.ingest_job_description(test_job_description)

        # Compute Semantic Embeddings & Scores
        overall_match = matcher.calculate_similarity(cleaned_resume, cleaned_jd)
        section_breakdown = matcher.compute_section_scores(resume_sections, cleaned_jd)

        print("=" * 50)
        print("🎯 DAY 5: SEMANTIC SIMILARITY RESULTS")
        print("=" * 50)
        print(f"📊 Overall Semantic Match: {overall_match}%")
        print("\n📑 Section Match Breakdown:")
        for section, score in section_breakdown.items():
            print(f" • {section.replace('_', ' ').title()}: {score}%")
        print("=" * 50)
    else:
        print(f"⚠️ '{test_pdf}' not found. Run make_pdf.py first.")
