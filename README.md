## Approach

This solution strictly adheres to the assessment constraint of not using Generative AI or LLMs. Instead, it utilizes a deterministic, rule-based data extraction pipeline built in Python to handle the highly inconsistent formatting of Sri Lankan court decisions.

The extraction process is divided into four main stages:

---

### 1. Robust Text Extraction & OCR Fallback

The script initially attempts to extract the text layer from the PDF using **PyMuPDF (fitz)**. However, court documents are frequently scanned images rather than digital text.

To handle this, the system:
- Checks the extracted text length
- Searches for basic legal keywords

If the text is too short or missing key terms, the script automatically triggers an **OCR fallback** using **pdf2image** and **pytesseract** to extract text from images.

---

### 2. Bench Extraction (Keyword & Title Hunting)

To identify the panel of judges (the *bench*), the script scans the first 150 lines of the document for standard trigger words such as:

- `BEFORE`
- `PRESENT`
- `CORAM`

Once detected, it extracts names:
- On the same line
- Immediately before or after the trigger line

**Fallback Strategy (Title Hunting):**  
If trigger words are missing, the system scans for judicial titles such as:
- `J.`
- `CJ`
- `Chief Justice`

This ensures robustness across differently formatted documents.

---

### 3. Author Judge Extraction (Deductive Parsing)

Since authoring formats vary across judgments, the system uses multiple prioritized strategies:

- **Subtraction Method:**  
  Detects `"I agree"` signatures at the bottom of the document. These judges are removed from the bench list, and the remaining judge is identified as the author.

- **Explicit Declarations:**  
  Searches for phrases like:
  - `"Judgment delivered by..."`
  - `"Order by..."`

- **Bottom Signature Blocks:**  
  Extracts all judges listed at the end when judgments are jointly authored.

- **Mid-Document Signatures:**  
  Captures cases where the author signs immediately after a date near the beginning of their judgment.

---

### 4. Data Sanitization ("Grammar Nuke")

To prevent incorrect extraction of non-name text, all candidates go through a strict cleaning pipeline:

- Rejects case citations (e.g., strings containing `" v. "`)
- Removes titles and prefixes:
  - `Chief Justice`, `J.`, `PC`, `Dr.`
- Removes signature artifacts:
  - `Sgd.`, `I agree`

**Grammar Nuke Filter:**
- Eliminates common English words (`the`, `in`, `of`, etc.)
- Filters Sri Lankan address terms (`Colombo`, `Mawatha`)
- Removes legal jargon (`Respondent`, `Counsel`, `Appellant`)

Finally, constraints such as:
- Word count limits
- Character filtering

ensure that only valid human names are included in the final JSON output.

**Installation:**
- Clone the repository:
  
- git clone https://github.com/your-username/judge-extraction.git
- cd judge-extraction
- uv install
- uv run src/extract_judges.py

**Dependencies:**
Python 3.10+
PyMuPDF (fitz)
pdf2image
pytesseract
uv package manager
