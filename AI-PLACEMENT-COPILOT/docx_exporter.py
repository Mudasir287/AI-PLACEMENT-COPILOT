import io
from typing import List, Dict, Optional, Any
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


class DocxExporter:
    """
    Standardized ATS-compliant Word document (.docx) exporter.
    Applies clean typography, 0.75-inch margins, and structured headers.
    """

    def __init__(self):
        pass

    def build_resume_docx(
        self,
        name: str,
        contact_info: Dict[str, Optional[str]],
        summary: str,
        skills: List[str],
        experience_bullets: List[str],
        target_role: Optional[str] = None
    ) -> io.BytesIO:
        """
        Builds a professionally styled, ATS-parseable DOCX resume in-memory.
        """
        doc = Document()

        # Set standard 0.75-inch page margins
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # Candidate Name (Header)
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_p.add_run(name)
        title_run.font.name = "Calibri"
        title_run.font.size = Pt(22)
        title_run.bold = True
        title_run.font.color.rgb = RGBColor(15, 23, 42)

        # Contact Info Line
        contact_items = [v for v in contact_info.values() if v]
        if target_role:
            contact_items.insert(0, target_role)

        contact_p = doc.add_paragraph()
        contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_run = contact_p.add_run(" | ".join(contact_items))
        contact_run.font.name = "Calibri"
        contact_run.font.size = Pt(10)
        contact_run.font.color.rgb = RGBColor(100, 116, 139)

        # Helper to add standardized section headers
        def add_section_heading(heading_text: str):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(heading_text.upper())
            run.font.name = "Calibri"
            run.font.size = Pt(12)
            run.bold = True
            run.font.color.rgb = RGBColor(2, 132, 199)

        # 1. Professional Summary
        if summary:
            add_section_heading("Professional Summary")
            sum_p = doc.add_paragraph()
            sum_p.paragraph_format.space_after = Pt(6)
            sum_run = sum_p.add_run(summary)
            sum_run.font.name = "Calibri"
            sum_run.font.size = Pt(10.5)

        # 2. Technical Skills
        if skills:
            add_section_heading("Technical & Core Competencies")
            skills_p = doc.add_paragraph()
            skills_p.paragraph_format.space_after = Pt(6)
            skills_run = skills_p.add_run(" • ".join(skills))
            skills_run.font.name = "Calibri"
            skills_run.font.size = Pt(10.5)

        # 3. Professional Experience (STAR Bullets)
        if experience_bullets:
            add_section_heading("Professional Experience & Key Achievements")
            for bullet in experience_bullets:
                clean_bullet = bullet.strip("• \t\r\n")
                if not clean_bullet:
                    continue
                bullet_p = doc.add_paragraph(style="List Bullet")
                bullet_p.paragraph_format.space_after = Pt(3)
                bullet_run = bullet_p.add_run(clean_bullet)
                bullet_run.font.name = "Calibri"
                bullet_run.font.size = Pt(10)

        # Export into BytesIO buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    def export_resume(self, *args, **kwargs):
        """Backward-compatibility alias."""
        return self.build_resume_docx(*args, **kwargs)


# Alias to satisfy both naming conventions across all modules
DocxResumeExporter = DocxExporter


# --- Verification Pipeline ---
if __name__ == "__main__":
    exporter = DocxResumeExporter()
    print("✅ DocxResumeExporter and DocxExporter loaded successfully.")
