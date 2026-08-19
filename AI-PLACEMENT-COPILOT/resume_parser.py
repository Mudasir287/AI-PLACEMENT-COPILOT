import os
import re
import fitz # PyMuPDF
from typing import Dict, List, Any, Optional


class ResumeParser:
    """
    Robust resume parsing engine powered by PyMuPDF (fitz) and regex-based
    structural section segmenters.
    """

    def __init__(self):
        self.section_headers = {
            "summary": [
                r"professional\s+summary",
                r"profile",
                r"summary",
                r"about\s+me",
                r"executive\s+summary",
            ],
            "skills": [
                r"technical\s+skills",
                r"core\s+competencies",
                r"skills\s+&\s+technologies",
                r"skills",
                r"technologies",
                r"expertise",
            ],
            "experience": [
                r"work\s+experience",
                r"professional\s+experience",
                r"employment\s+history",
                r"experience",
                r"work\s+history",
                r"internships",
            ],
            "education": [
                r"education",
                r"academic\s+background",
                r"qualifications",
                r"academics",
                r"degrees",
            ],
            "projects": [
                r"projects",
                r"technical\s+projects",
                r"academic\s+projects",
                r"personal\s+projects",
            ],
        }

    def extract_text(self, pdf_path: str) -> str:
        """Extracts and normalizes text from all pages of a PDF document."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        extracted_pages = []
        doc = fitz.open(pdf_path)
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if text.strip():
                    extracted_pages.append(text.strip())
        finally:
            doc.close()

        full_text = "\n\n".join(extracted_pages)
        # Normalize whitespace and carriage returns
        full_text = re.sub(r"\r\n", "\n", full_text)
        return full_text.strip()

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extracts standard contact information using regular expressions."""
        # Email matching pattern
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        email_match = re.search(email_pattern, text)

        # Phone matching pattern (standard international & domestic formats)
        phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        phone_match = re.search(phone_pattern, text)

        # LinkedIn & GitHub handle patterns
        linkedin_pattern = r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+"
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)

        github_pattern = r"(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_-]+"
        github_match = re.search(github_pattern, text, re.IGNORECASE)

        return {
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0) if phone_match else None,
            "linkedin": linkedin_match.group(0) if linkedin_match else None,
            "github": github_match.group(0) if github_match else None,
        }

    def segment_sections(self, text: str) -> Dict[str, str]:
        """Segments raw text into standard resume sections."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        sections: Dict[str, List[str]] = {
            "header": [],
            "summary": [],
            "skills": [],
            "experience": [],
            "education": [],
            "projects": [],
            "other": [],
        }

        current_section = "header"

        for line in lines:
            normalized_line = line.lower().strip()
            detected_header = None

            # Detect section header matches
            for section_name, patterns in self.section_headers.items():
                for pattern in patterns:
                    regex = rf"^(?:[\d\.\-\*\•\s]*)\b{pattern}\b(?:\s*[:\-])?$"
                    if re.match(regex, normalized_line, re.IGNORECASE):
                        detected_header = section_name
                        break
                if detected_header:
                    break

            if detected_header:
                current_section = detected_header
            else:
                sections[current_section].append(line)

        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        Unified parser method returning raw text, contact details,
        segmented sections, and structural metrics.
        """
        raw_text = self.extract_text(pdf_path)
        contact_info = self.extract_contact_info(raw_text)
        sections = self.segment_sections(raw_text)

        words = raw_text.split()
        return {
            "filename": os.path.basename(pdf_path),
            "raw_text": raw_text,
            "contact_info": contact_info,
            "sections": sections,
            "character_count": len(raw_text),
            "word_count": len(words),
        }


# --- Standalone Verification Pipeline ---
if __name__ == "__main__":
    parser = ResumeParser()
    print("🚀 ResumeParser class loaded with .parse(), .extract_text(), and .segment_sections().")
