import os
import json
import re
import fitz
import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        print(f"Standard extraction failed for {pdf_path}: {e}")

    if len(text.strip()) < 150 or not re.search(r"(?i)(court|judge|judgment|order|petitioner)", text):
        print(f"  Text unreadable.OCR fallback is called...")
        try:
            images = convert_from_path(pdf_path)
            for img in images:
                text += pytesseract.image_to_string(img)
        except Exception as e:
            print(f"  OCR failed: {e}")

    return text

def clean_judge_name(name_str):
    if not name_str:
        return None

    if re.search(r"(?i)\s+v\.?\s+", name_str):
        return None

    clean = re.sub(r"(?i)\b(i agree|agree|agreed|sgd\.?|signed|true copy|signature)\b", "", name_str)
    clean = re.sub(r"(?i)\b(chief justice|justice|judge of the supreme court|judge of the court of appeal|judge)\b", "", clean)
    clean = re.sub(r"(?i)\b(cj|pc|p\.c\.|c\.j\.|dr\.|dr|mr\.|mrs\.|ms\.)\b", "", clean)
    clean = re.sub(r"(?i)(,\s*J\.?|\bJ\.?\s*$)", "", clean)
    clean = re.sub(r"[^a-zA-Z\s\.]", "", clean).strip()
    clean = re.sub(r"\s+", " ", clean).strip(" .")

    grammar_nuke = (
        r"(?i)\b(the|in|of|to|for|with|by|from|on|at|as|encountered|others|such|made|"
        r"accordance|procedure|established|law|obstructions|omission|single|material|"
        r"fact|leads|incomplete|cause|action|statement|claim|becomes|bad|function|party|"
        r"picture|information|detail|opposite|understand|case|meet|arguments|apposite|"
        r"allude|constitutional|proceedings|must|discontinued|relation|former|prime|"
        r"minister|who|has|since|become|acts|omissions|allegedly|became|continue|his|"
        r"counsel|councel|present|before|court|supreme|colombo|respondent|respondents|"
        r"petitioner|petitioners|appellant|plaintiff|defendant|nature|exercise|mawatha|"
        r"jayanthipura|battaramulla|article)\b"
    )

    if re.search(grammar_nuke, clean):
        return None

    if 3 < len(clean) < 40 and len(clean.split()) <= 6:
        return clean.title()
    return None

def _surnames_overlap(name_a: str, name_b: str) -> bool:
    a_last = name_a.strip().split()[-1].lower() if name_a.strip() else ""
    b_last = name_b.strip().split()[-1].lower() if name_b.strip() else ""
    if not a_last or not b_last:
        return False
    return a_last in name_b.lower() or b_last in name_a.lower()

def extract_bench_and_author(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    bench = []
    author_judge = []

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
                if name:
                    bench.append(name)

        for j in range(max(0, trigger_idx - 8), trigger_idx):
            if re.search(r"(?i)(\bJ\b|\bJ\.|\bCJ\b|\bC\.J\.|Chief Justice|Justice)", lines[j]):
                for part in re.split(r"(?i)\band\b|,", lines[j]):
                    name = clean_judge_name(part)
                    if name:
                        bench.append(name)

        if not bench:
            for j in range(trigger_idx + 1, min(len(lines), trigger_idx + 15)):
                line = lines[j]
                if re.match(r"(?i)^(counsel|councel|argued|decided|judgment|order|date|hearing|determination)[\s:]*", line):
                    break
                if re.search(r"(?i)(respondent|petitioner|appellant|plaintiff|defendant|colombo|mawatha)", line):
                    continue
                for part in re.split(r"(?i)\band\b|,", line):
                    name = clean_judge_name(part)
                    if name:
                        bench.append(name)

    if not bench:
        for i, line in enumerate(lines[:150]):
            if re.search(r"(?i)(respondent|petitioner|appellant|plaintiff|defendant|counsel|colombo)", line):
                continue
            if re.search(r"(?i)(\bJ\b|\bJ\.|\bCJ\b|\bC\.J\.|Justice)", line):
                for part in re.split(r"(?i)\band\b|,", line):
                    name = clean_judge_name(part)
                    if name:
                        bench.append(name)

    if not bench:
        for i in range(len(lines[:150]) - 1):
            if re.match(r"(?i)^(Justice|Judge|CJ|J\.)\s*$", lines[i + 1]):
                name = clean_judge_name(lines[i])
                if name:
                    bench.append(name)

    bench = list(dict.fromkeys(bench))

    author_match = re.search(
        r"(?i)(?:judgment|order)\s+(?:of|delivered\s+by|written\s+by|by)\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z\s\.]{2,40}?)(?=\n|,|\bJ\b|\bJustice\b)",
        text,
    )
    if author_match:
        name = clean_judge_name(author_match.group(1))
        if name:
            return bench, [name]

    bottom = lines[-120:]
    agreeing_names = []

    for i, line in enumerate(bottom):
        if re.search(r"(?i)\bi\s+agree\b", line):
            candidate = re.sub(r"(?i)\bi\s+agree.*", "", line).strip()
            name = clean_judge_name(candidate)
            if name:
                agreeing_names.append(name)
            for j in range(max(0, i - 5), i):
                name = clean_judge_name(bottom[j])
                if name:
                    agreeing_names.append(name)

    if agreeing_names and bench:
        non_agreeing = [
            b for b in bench
            if not any(_surnames_overlap(b, a) for a in agreeing_names)
        ]
        if non_agreeing and len(non_agreeing) < len(bench):
            return bench, list(dict.fromkeys(non_agreeing))

    bottom60 = lines[-60:]
    for i in range(len(bottom60) - 1):
        if re.search(
            r"(?i)(chief justice|judge of the supreme court|judge of the court of appeal|\bJ\b|\bJ\.|\bCJ\b|\bC\.J\.)",
            bottom60[i + 1],
        ):
            name = clean_judge_name(bottom60[i])
            if name:
                author_judge.append(name)

    if author_judge:
        return bench, list(dict.fromkeys(author_judge))

    for i, line in enumerate(lines[:100]):
        if re.match(r"(?i)^[a-z]+\s+\d{1,2},\s+\d{4}", line):
            if i + 1 < len(lines):
                name = clean_judge_name(lines[i + 1])
                if name:
                    author_judge.append(name)

    if not author_judge and len(bench) == 1:
        author_judge = list(bench)

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

            print(f"   bench:        {bench}")
            print(f"   author_judge: {author_judge}")
            print(f"   written to:   {json_filename}\n")

if __name__ == "__main__":
    process_pdfs("data", "output")