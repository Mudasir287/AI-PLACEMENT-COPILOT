import os 
import pymupdf as fitz

def extract_text_from_pdf(pdf_path:str) -> str :
    """
    OPENs A PDF DOCUMENT AND EXTRACTS ALL TEXT CONTENT PAGE BY PAGE
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File Not Found : {pdf_path}")

    #open the document 
    doc=fitz.open(pdf_path)
    extracted_text_blocks = []

    print(f"DOCUMENT LOADED : {pdf_path}")
    print(f"Total pages : {len(doc)}\n")

    #EXtract text from each page 
    for page_num,page in enumerate(doc,start=1):
        page_text=page.get_text("Text")
        print(f"---PAGE{page_num} Extracted ({len(page_text)}charcters)---")
        extracted_text_blocks.append(page_text)

    #RElease resources
    doc.close()

    return "\n".join(extracted_text_blocks).strip()

if __name__ == "__main__":
    sample_file = "sample_resume.pdf"

    if os.path.exists(sample_file):
        raw_text=extract_text_from_pdf(sample_file)
        print("\n"+"="*40)
        print("Raw Extracted text preview : ")
        print("="*40)
        print(raw_text[:500]+"\n\n...[TRUNCATED PREVIEW]...")
    else :
        print(f"Add '{sample_file}'to your root folder to run a text extraction.")