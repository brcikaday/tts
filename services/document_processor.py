import fitz
from docx import Document
from fastapi import HTTPException, status, UploadFile
import tempfile
import os
import re

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    text = extract_text_and_clean(text)
    return text


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    text = extract_text_and_clean(text)
    return text





def chunking_file(file: UploadFile, chunk_size: int = 1024 * 1024): 
    total_size = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix= os.path.splitext(file.filename)[1]) as temp_file:
        while True:
            chunk = file.file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > 200 * 1024 * 1024: 
                os.remove(temp_file.name) 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds limit")
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    return temp_file_path, total_size


def extract_text_and_clean(text):

    
    # 1. Remove page numbers (standalone numbers on a line)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # 2. Remove URLs — ElevenLabs will try to read these out loud
    text = re.sub(r'http\S+|www\.\S+', '', text)
    
    # 3. Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # 4. Remove figure/table references
    text = re.sub(r'\[?(figure|fig|table|chart|graph|image|diagram)\.?\s*\d+[\.\d]*\]?', 
                  '', text, flags=re.IGNORECASE)
    
    # 5. Remove citation brackets like [1], [2,3], (Smith et al., 2019)
    text = re.sub(r'\[\d+[\d,\s]*\]', '', text)
    text = re.sub(r'\([A-Z][a-z]+.*?\d{4}\)', '', text)
    
    # 6. Remove excessive whitespace and blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 7. Remove special characters that confuse TTS
    text = re.sub(r'[•●▪▸◦‣]', '', text)  # bullet symbols
    text = re.sub(r'[_]{2,}', '', text)    # underscores used as dividers
    text = re.sub(r'[-]{3,}', '', text)    # dashes used as dividers
    text = re.sub(r'[=]{2,}', '', text)    # equals signs used as dividers
    
    # 8. Expand common abbreviations ElevenLabs reads awkwardly
    abbreviations = {
        r'\bDr\.': 'Doctor',
        r'\bProf\.': 'Professor',
        r'\bMr\.': 'Mister',
        r'\bMrs\.': 'Missus',
        r'\betc\.': 'et cetera',
        r'\be\.g\.': 'for example',
        r'\bi\.e\.': 'that is',
        r'\bvs\.': 'versus',
        r'\bFig\.': 'Figure',
        r'\bEq\.': 'Equation',
        r'\bch\.': 'chapter',
        r'\bpp\.': 'pages',
    }
    for pattern, replacement in abbreviations.items():
        text = re.sub(pattern, replacement, text)
    
    # 9. Handle numbers and symbols ElevenLabs handles poorly
    text = re.sub(r'(\d+)%', r'\1 percent', text)
    text = re.sub(r'\$(\d+)', r'\1 dollars', text)
    text = re.sub(r'(\d+)\s*°C', r'\1 degrees Celsius', text)
    text = re.sub(r'(\d+)\s*°F', r'\1 degrees Fahrenheit', text)
    
    # 10. Fix hyphenated line breaks common in PDFs
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    
    # 11. Strip leading/trailing whitespace
    text = text.strip()
    
    return text