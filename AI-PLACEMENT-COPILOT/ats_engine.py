import re
from typing import Dict, List, Any, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Dynamic safe imports
try:
    from text_cleaner import TextCleaner
except ImportError:
    TextCleaner = None

try:
    from vector_matcher import VectorMatcher
except ImportError:
    VectorMatcher = None


class ATSEngine:
    """
    Robust Hybrid ATS scoring engine combining Dense Semantic Embeddings,
    TF-IDF Vector Matching, and Domain Skill Keyword Extraction.
    """

    def __init__(self):
        # Initialize text cleaner with fallback
        if TextCleaner is not None:
            try:
                self.cleaner = TextCleaner()
            except Exception:
                self.cleaner = None
        else:
            self.cleaner = None

        # Initialize vector matcher with fallback
        if VectorMatcher is not None:
            try:
                self.matcher = VectorMatcher()
            except Exception:
                self.matcher = None
        else:
            self.matcher = None

        # Comprehensive skill vocabulary across Engineering, AI, Cloud, and UX/UI
        self.skill_vocabulary = {
            # Programming & Web Development
            "python", "javascript", "typescript", "java", "c++", "c#", "html", "html5",
            "css", "css3", "sql", "nosql", "fastapi", "flask", "django", "react",
            "angular", "vue", "node.js", "nodejs", "next.js", "rest", "rest api", "graphql",

            # Data Science, AI & ML
            "machine learning", "deep learning", "nlp", "computer vision", "pytorch",
            "tensorflow", "scikit-learn", "spacy", "pandas", "numpy", "transformers",
            "langchain", "vector embeddings", "hugging face", "llm", "llms",

            # Cloud, DevOps & Databases
            "docker", "kubernetes", "aws", "gcp", "azure", "git", "github", "gitlab",
            "ci/cd", "linux", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",

            # UI/UX, Product & Design
            "figma", "sketch", "invision", "balsamiq", "adobe suite", "photoshop",
            "illustrator", "wireframes", "prototyping", "user research", "usability testing",
            "a/b testing", "design systems", "wcag", "interaction design", "hci",
            "agile", "scrum"
        }

    def _clean_text(self, text: str) -> str:
        """Cleans input text using TextCleaner or regular expressions."""
        if self.cleaner:
            for method_name in ["clean", "clean_text", "preprocess", "normalize"]:
                if hasattr(self.cleaner, method_name):
                    try:
                        return getattr(self.cleaner, method_name)(text)
                    except Exception:
                        pass
        # Built-in regex fallback
        lowered = text.lower()
        cleaned = re.sub(r"[^a-zA-Z0-9\s\+\#\.\-]", " ", lowered)
        return " ".join(cleaned.split())

    def _compute_semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        """Computes dense similarity via VectorMatcher with TF-IDF fallback."""
        if self.matcher:
            for method_name in ["calculate_similarity", "compute_similarity", "get_similarity", "match"]:
                if hasattr(self.matcher, method_name):
                    try:
                        sim = getattr(self.matcher, method_name)(resume_text, jd_text)
                        if isinstance(sim, (int, float)):
                            return float(sim)
                    except Exception:
                        pass

        # Fallback to TF-IDF Cosine Similarity
        try:
            clean_res = self._clean_text(resume_text)
            clean_jd = self._clean_text(jd_text)
            if not clean_res or not clean_jd:
                return 0.0

            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            matrix = vectorizer.fit_transform([clean_res, clean_jd])
            score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return float(score)
        except Exception:
            return 0.50

    def extract_skills_from_text(self, text: str) -> Set[str]:
        """Extracts recognized technical skills using regex word-boundary lookup."""
        normalized_text = f" {text.lower()} "
        clean_text = re.sub(r"[^\w\s\+\#\.\-]", " ", normalized_text)

        found_skills = set()
        for skill in self.skill_vocabulary:
            pattern = rf"(?:\b|\s){re.escape(skill)}(?:\b|\s)"
            if re.search(pattern, clean_text):
                display_name = skill.title() if len(skill) > 4 else skill.upper()
                found_skills.add(display_name)
        return found_skills

    def calculate_ats_score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Computes calibrated hybrid ATS score, skills overlap, and fit level.
        """
        # 1. Semantic Match Calculation
        raw_similarity = self._compute_semantic_similarity(resume_text, jd_text)
        dense_score = max(0.0, min(100.0, float(raw_similarity * 100.0)))

        # 2. Skill Extraction & Overlap Analysis
        resume_skills = self.extract_skills_from_text(resume_text)
        jd_skills = self.extract_skills_from_text(jd_text)

        matched_skills = sorted(list(resume_skills.intersection(jd_skills)))
        missing_skills = sorted(list(jd_skills.difference(resume_skills)))

        # 3. Keyword / Skill Overlap Percentage
        if jd_skills:
            sparse_score = (len(matched_skills) / len(jd_skills)) * 100.0
        else:
            res_words = set(self._clean_text(resume_text).split())
            jd_words = set(self._clean_text(jd_text).split())
            union = res_words.union(jd_words)
            sparse_score = (len(res_words.intersection(jd_words)) / len(union) * 100.0) if union else 0.0

        # 4. Hybrid Weighted Score: 60% Dense Semantic + 40% Exact Skill Overlap
        overall_score = round((0.60 * dense_score) + (0.40 * sparse_score), 1)
        overall_score = max(0.0, min(100.0, overall_score))

        # 5. Fit Level Categorization
        if overall_score >= 75.0:
            fit_level = "Strong Match"
        elif overall_score >= 50.0:
            fit_level = "Moderate Match"
        else:
            fit_level = "Low Match / Needs Tailoring"

        return {
            "overall_ats_score": overall_score,
            "cosine_similarity": round(dense_score, 1),
            "jaccard_keyword_match": round(sparse_score, 1),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "fit_level": fit_level
        }


# --- Verification Pipeline ---
if __name__ == "__main__":
    engine = ATSEngine()
    sample_res = "UX Designer experienced in HTML, CSS, JavaScript, Sketch, InVision, Wireframes, Prototyping."
    sample_jd = "Senior UX Designer with Figma, Design Systems, HTML5, CSS3, Usability Testing, Agile."
    
    scorecard = engine.calculate_ats_score(sample_res, sample_jd)
    print("✅ ATSEngine test scan successful:")
    print(scorecard)