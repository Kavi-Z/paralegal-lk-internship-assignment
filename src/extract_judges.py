import os
import json
import re
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path

# POINT TO THE PROGRAM, NOT THE INSTALLER! 
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF, falling back to OCR if it's unreadable."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        print(f"Standard extraction failed for {pdf_path}: {e}")

    # Trigger OCR if text is tiny OR if PyMuPDF missed the actual text layer 
    if len(text.strip()) < 150 or not re.search(r"(?i)(court|judge|judgment|order|petitioner)", text):
        print(f"  -> Text unreadable or missing. Triggering OCR fallback...")
        try:
            images = convert_from_path(pdf_path)
            for img in images:
                text += pytesseract.image_to_string(img)
        except Exception as e:
            print(f"  -> OCR failed: {e}")

    return text

def clean_judge_name(name_str):
    """Aggressively strips titles, case citations, and sentences."""
    # 1. Reject case citations immediately (e.g., "Smith v. Jones")
    if re.search(r"(?i)\s+v\.?\s+", name_str): 
        return None
        
    # 2. Strip explicit full-word and abbreviated titles
    clean = re.sub(r"(?i)\b(chief justice|justice|judge of the supreme court|judge of the court of appeal|judge)\b", "", name_str)
    clean = re.sub(r"(?i)\b(cj|j|pc|p\.c\.|c\.j\.|j\.|dr\.|dr|mr\.|mrs\.|ms\.)\b", "", clean)
    
    # 3. Remove weird punctuation and collapse spaces
    clean = re.sub(r"[^a-zA-Z\s\.]", "", clean).strip()
    clean = re.sub(r"\s+", " ", clean).strip(" .")
    
    # 4. GRAMMAR NUKE: Reject any string containing common sentence words or legal jargon
    grammar_nuke = r"(?i)\b(the|in|of|to|for|with|by|from|on|at|as|encountered|others|such|made|accordance|procedure|established|law|obstructions|omission|single|material|fact|leads|incomplete|cause|action|statement|claim|becomes|bad|function|party|picture|information|detail|opposite|understand|case|meet|arguments|apposite|allude|constitutional|proceedings|must|discontinued|relation|former|prime|minister|who|has|since|become|acts|omissions|allegedly|became|continue|his|counsel|councel|present|before|court|supreme|colombo|respondent|respondents|petitioner|petitioners|appellant|plaintiff|defendant|nature|exercise|mawatha|jayanthipura|battaramulla|article)\b"
    
    if re.search(grammar_nuke, clean):
        return None
        
    # 5. Length check: Names are rarely longer than 5 words
    if 3 < len(clean) < 40:
        if len(clean.split()) <= 5:
            return clean.title()
    return None

def extract_bench_and_author(text):
    """Uses advanced index-scanning and title-hunting to parse the bench and author."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    bench = []
    author_judge = []

    # --- 1. EXTRACT BENCH ---
    trigger_idx = -1
    for i, line in enumerate(lines[:150]):
        if re.match(r"(?i)^(before|coram|present|bench)[\s:]*", line):
            trigger_idx = i
            break

    if trigger_idx != -1:
        names_part = re.sub(r"(?i)^(before|coram|present|bench)[\s:]*", "", lines[trigger_idx])
        if names_part:
            for part in re.split(r"(?i)\band\b|,", names_part):
                name = clean_judge_name(part)
                if name: bench.append(name)
        
        # Look ABOVE (Added \bJ\b to catch "Amerasinghe, J,")
        for j in range(max(0, trigger_idx - 6), trigger_idx):
            if re.search(r"(?i)(\bJ\b|\bJ\.|Justice|\bCJ\b|\bC\.J\.|Chief Justice)", lines[j]):
                for part in re.split(r"(?i)\band\b|,", lines[j]):
                    name = clean_judge_name(part)
                    if name: bench.append(name)
                    
        # Look BELOW 
        if not bench:
            for j in range(trigger_idx + 1, min(len(lines), trigger_idx + 15)):
                line = lines[j]
                if re.match(r"(?i)^(counsel|councel|argued|decided|judgment|order|date|hearing|determination)[\s:]*", line): break
                if re.search(r"(?i)(respondent|petitioner|appellant|plaintiff|defendant|colombo|mawatha)", line): continue
                
                for part in re.split(r"(?i)\band\b|,", line):
                    name = clean_judge_name(part)
                    if name: bench.append(name)

    # TITLED FALLBACK (For PDF 1)
    if not bench:
        for i, line in enumerate(lines[:150]):
            if re.search(r"(?i)(respondent|petitioner|appellant|plaintiff|defendant|counsel|colombo)", line): continue
            if re.search(r"(?i)(\bJ\b|\bJ\.|\bCJ\b|\bC\.J\.|Justice)", line):
                for part in re.split(r"(?i)\band\b|,", line):
                    name = clean_judge_name(part)
                    if name: bench.append(name)

    # --- 2. EXTRACT AUTHOR JUDGE ---
    author_match = re.search(r"(?i)(?:judgment|order)\s+(?:of|delivered by|by)[\s:]+([A-Za-z\s\.]+?)(?=\n|,)", text)
    if author_match:
        name = clean_judge_name(author_match.group(1))
        if name: author_judge.append(name)

    # Signature blocks at the absolute bottom (Expanded to catch PDF 1 Author)
    if not author_judge:
        bottom_lines = lines[-60:] 
        for i in range(len(bottom_lines) - 1):
            if re.search(r"(?i)(chief justice|judge of the supreme court|judge of the court of appeal|\bJ\b|\bJ\.|\bCJ\b|\bC\.J\.)", bottom_lines[i+1]):
                name = clean_judge_name(bottom_lines[i])
                if name: author_judge.append(name)

    bench = list(dict.fromkeys(bench))
    author_judge = list(dict.fromkeys(author_judge))

    return bench, author_judge

def process_pdfs(data_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in sorted(os.listdir(data_dir)):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(data_dir, filename)
            print(f"Processing: {filename}")
            
            text = extract_text_from_pdf(pdf_path)
            bench, author_judge = extract_bench_and_author(text)

            output_data = {
                "source_file": filename,
                "bench": bench,
                "author_judge": author_judge
            }

            json_filename = filename.replace(".pdf", ".json")
            json_path = os.path.join(output_dir, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4)
                
            print(f"  -> bench:        {bench}")
            print(f"  -> author_judge: {author_judge}")
            print(f"  -> written to:   {json_filename}\n")

if __name__ == "__main__":
    process_pdfs("data", "output")