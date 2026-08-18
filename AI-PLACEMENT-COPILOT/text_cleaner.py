import re
import unicodedata
from typing import Dict

def clean_raw_text(raw_text: str) -> str:
    """
    Cleans raw text extracted from PDF resumes.
    - Normalizes Unicode characters and ligatures
    - Converts non-standard bullets into uniform dashes
    - Fixes hyphenated words split across lines
    - Strips excess whitespace and consecutive empty lines
    """
    if not raw_text:
        return ""

    # 1. Normalize Unicode (converts special ligatures & accents to standard forms)
    text = unicodedata.normalize("NFKD", raw_text)

    # 2. Convert varied bullet characters into standard dashed list items
    bullet_pattern = r"[\u2022\u2023\u25E6\u2043\u2219\uf0b7▪•*]"
    text = re.sub(bullet_pattern, "\n- ", text)

    # 3. Replace non-breaking spaces and tabs with standard single spaces
    text = text.replace("\xa0", " ").replace("\t", " ")

    # 4. Rejoin words hyphenated across line breaks (e.g., 'engi-\nneer' -> 'engineer')
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # 5. Collapse multiple horizontal spaces into a single space
    text = re.sub(r"[ ]{2,}", " ", text)

    # 6. Reduce 3 or more consecutive newlines down to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_resume_sections(cleaned_text: str) -> Dict[str, str]:
    """
    Parses cleaned text and isolates standard resume sections into a dictionary:
    - Contact / Header Info
    - Skills
    - Experience
    - Education
    - Projects
    """
    sections = {
        "header": "",
        "skills": "",
        "experience": "",
        "education": "",
        "projects": "",
        "other": ""
    }

    # Common aliases for section headers
    section_patterns = {
        "skills": r"(?:technical\s+skills|skills|technologies|core\s+competencies)",
        "experience": r"(?:work\s+experience|professional\s+experience|experience|employment\s+history)",
        "education": r"(?:education|academic\s+background|qualifications)",
        "projects": r"(?:projects|technical\s+projects|academic\s+projects|key\s+projects)"
    }

    # Build regex to match header boundaries (case-insensitive, on fresh lines)
    combined_regex = r"(?im)^(?P<header_name>" + "|".join(section_patterns.values()) + r")\s*[:\n]"

    # Find all header positions
    matches = list(re.finditer(combined_regex, cleaned_text))

    if not matches:
        # If no standard section headers were detected, store everything under header
        sections["header"] = cleaned_text
        return sections

    # Capture header / contact info before the first section
    first_match_start = matches[0].start()
    sections["header"] = cleaned_text[:first_match_start].strip()

    # Slice text between consecutive headers
    for i, match in enumerate(matches):
        raw_header = match.group("header_name").strip().lower()
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned_text)

        content = cleaned_text[start_pos:end_pos].strip()

        # Map matched header to standard category
        assigned_key = "other"
        for key, pattern in section_patterns.items():
            if re.search(f"^{pattern}$", raw_header, re.IGNORECASE):
                assigned_key = key
                break

        sections[assigned_key] = content

    return sections


if __name__ == "__main__":
    import os
    from pdf_parser import extract_text_from_pdf

    sample_pdf_file = "sample_resume.pdf"

    if os.path.exists(sample_pdf_file):
        print(f"🔄 Parsing and cleaning: {sample_pdf_file}")
        raw = extract_text_from_pdf(sample_pdf_file)
        cleaned = clean_raw_text(raw)
        parsed_dict = extract_resume_sections(cleaned)

        print("\n" + "=" * 50)
        print("✅ STRUCTURED RESUME DICTIONARY OUTPUT:")
        print("=" * 50)
        for section, body in parsed_dict.items():
            if body:
                print(f"\n📂 [{section.upper()} SECTION] ({len(body)} chars):")
                print(body[:200] + ("..." if len(body) > 200 else ""))
    else:
        print(f"⚠️ '{sample_pdf_file}' not found. Please run make_pdf.py first.")