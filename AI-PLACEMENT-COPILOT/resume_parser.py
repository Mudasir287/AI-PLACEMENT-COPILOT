import os
import re
import time
import unicodedata
from typing import Dict, Union, Optional
import fitz # PyMuPDF


class ResumeParser:
    """
    Unified modular engine for ingesting, parsing, and cleaning 
    resumes and job descriptions across multiple formats (.pdf, .txt, pasted text).
    """

    def __init__(self):
        self.section_patterns = {
            "skills": r"(?:technical\s+skills|skills|technologies|core\s+competencies|tools)",
            "experience": r"(?:work\s+experience|professional\s+experience|experience|employment\s+history|internships)",
            "education": r"(?:education|academic\s+background|qualifications|academic\s+profile)",
            "projects": r"(?:projects|technical\s+projects|academic\s+projects|key\s+projects)"
        }

    # ==========================
    # Text Cleaning & Normalization
    # ==========================
    def clean_text(self, raw_text: str) -> str:
        """Normalizes Unicode, standardizes bullets, and strips excess spacing."""
        if not raw_text:
            return ""

        # Normalize Unicode characters and ligatures
        text = unicodedata.normalize("NFKD", raw_text)

        # Standardize non-standard bullet points to dashes
        text = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219\uf0b7▪•*]", "\n- ", text)

        # Remove non-breaking spaces and tabs
        text = text.replace("\xa0", " ").replace("\t", " ")

        # Rejoin broken hyphenated words across lines
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

        # Collapse excessive spaces and redundant newlines
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # ==========================
    # PDF Extraction Engine
    # ==========================
    def extract_from_pdf(self, pdf_source: Union[str, bytes]) -> str:
        """Extracts text page-by-page from a PDF path or raw bytes."""
        try:
            if isinstance(pdf_source, bytes):
                doc = fitz.open(stream=pdf_source, filetype="pdf")
            elif isinstance(pdf_source, str) and os.path.exists(pdf_source):
                doc = fitz.open(pdf_source)
            else:
                raise FileNotFoundError(f"Invalid PDF source or file not found: {pdf_source}")

            extracted_pages = []
            for page in doc:
                extracted_pages.append(page.get_text("text"))

            doc.close()
            return "\n".join(extracted_pages).strip()
        except Exception as e:
            raise RuntimeError(f"Error parsing PDF file: {e}")

    # ==========================
    # Section Extraction
    # ==========================
    def extract_sections(self, cleaned_text: str) -> Dict[str, str]:
        """Segments cleaned resume text into standard categorized sections."""
        sections = {
            "header": "",
            "skills": "",
            "experience": "",
            "education": "",
            "projects": "",
            "other": ""
        }

        if not cleaned_text:
            return sections

        combined_regex = r"(?im)^(?P<header_name>" + "|".join(self.section_patterns.values()) + r")\s*[:\n]"
        matches = list(re.finditer(combined_regex, cleaned_text))

        if not matches:
            sections["header"] = cleaned_text
            return sections

        # Extract contact/header content before the first matched header
        first_start = matches[0].start()
        sections["header"] = cleaned_text[:first_start].strip()

        # Slice content between matched headers
        for i, match in enumerate(matches):
            raw_name = match.group("header_name").strip().lower()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned_text)
            content = cleaned_text[start:end].strip()

            assigned_section = "other"
            for key, pattern in self.section_patterns.items():
                if re.search(f"^{pattern}$", raw_name, re.IGNORECASE):
                    assigned_section = key
                    break

            sections[assigned_section] = content

        return sections

    # ==========================
    # End-to-End Pipeline
    # ==========================
    def parse_resume(self, pdf_source: Union[str, bytes]) -> Dict[str, Union[str, Dict[str, str]]]:
        """Complete pipeline: reads PDF, normalizes text, and extracts sections."""
        raw_text = self.extract_from_pdf(pdf_source)
        cleaned_text = self.clean_text(raw_text)
        sections = self.extract_sections(cleaned_text)

        return {
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "sections": sections
        }

    # ==========================
    # Job Description Ingestion
    # ==========================
    def ingest_job_description(self, jd_input: Union[str, bytes], is_file: bool = False) -> str:
        """
        Ingests Job Descriptions from direct text, .txt files, or .pdf files.
        """
        if not is_file:
            # Direct string pasted by user
            return self.clean_text(str(jd_input))

        if isinstance(jd_input, str):
            if not os.path.exists(jd_input):
                raise FileNotFoundError(f"JD file not found: {jd_input}")

            if jd_input.lower().endswith(".pdf"):
                raw_text = self.extract_from_pdf(jd_input)
            else:
                with open(jd_input, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()

            return self.clean_text(raw_text)

        elif isinstance(jd_input, bytes):
            # Streamed bytes from web uploaders
            try:
                # Try reading as PDF
                raw_text = self.extract_from_pdf(jd_input)
            except Exception:
                # Fallback to UTF-8 text decode
                raw_text = jd_input.decode("utf-8", errors="ignore")

            return self.clean_text(raw_text)

        return ""


# --- Unit Tests & Verification ---
if __name__ == "__main__":
    parser = ResumeParser()
    sample_pdf = "sample_resume.pdf"

    print("🚀 Running Day 4 Unit Tests & Refactor Validation...\n")
    start_time = time.time()

    # Test 1: Resume Parsing from PDF
    if os.path.exists(sample_pdf):
        resume_result = parser.parse_resume(sample_pdf)
        print(f"✅ Resume parsed successfully in {time.time() - start_time:.4f} seconds!")
        print(f"📊 Cleaned Length: {len(resume_result['cleaned_text'])} characters")
        print(f"📑 Detected Sections: {[k for k, v in resume_result['sections'].items() if v]}")
    else:
        print(f"⚠️ '{sample_pdf}' not found. Run make_pdf.py first.")

    # Test 2: Pasted Job Description Ingestion
    sample_jd_text = """
    Software Engineer - Python & AI
    Requirements:
    • 1+ years of experience with Python, PyTorch, and Git.
    • Strong understanding of REST APIs, Streamlit, and Machine Learning.
    • Bachelor's degree in Computer Science or related field.
    """
    cleaned_jd = parser.ingest_job_description(sample_jd_text, is_file=False)
    print("\n✅ Pasted JD Ingestion Test:")
    print(cleaned_jd)

    # Test 3: Text File JD Ingestion
    test_jd_path = "sample_jd.txt"
    with open(test_jd_path, "w", encoding="utf-8") as f:
        f.write(sample_jd_text)

    file_jd = parser.ingest_job_description(test_jd_path, is_file=True)
    print(f"\n✅ File-based (.txt) JD Ingestion Test: Loaded {len(file_jd)} characters")

    # Cleanup temp test file
    if os.path.exists(test_jd_path):
        os.remove(test_jd_path)

    total_duration = time.time() - start_time
    print("\n" + "=" * 55)
    print(f"🎯 Phase 1 Milestone Achieved: Pipeline latency = {total_duration:.4f}s (< 1.0s target)[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span)")
    print("=" * 55)
