# ⚖️ Sri Lankan Court Judgment — Judge Extraction Pipeline

> A deterministic, rule-based data extraction pipeline for parsing judge information from Sri Lankan court decisions — **no LLMs or Generative AI used**.

---

## 🧭 Overview

Sri Lankan court PDFs are notoriously inconsistent in formatting. This pipeline handles that chaos with a robust, four-stage extraction process — fully deterministic, fully auditable.

---

## 🔬 How It Works

### Stage 1 — Robust Text Extraction & OCR Fallback

The script first attempts to extract the embedded text layer from the PDF using **PyMuPDF (`fitz`)**.

Court documents are frequently scanned images rather than digital text, so the system automatically evaluates extraction quality by:

- Checking extracted text length
- Searching for basic legal keywords

If the text is too short or missing key terms, an **OCR fallback** is triggered using **`pdf2image`** and **`pytesseract`** to extract text directly from the scanned images.

---

### Stage 2 — Bench Extraction (Keyword & Title Hunting)

To identify the panel of judges (*the bench*), the script scans the **first 150 lines** of the document for standard trigger words:

| Trigger Word | Example Usage |
|---|---|
| `BEFORE` | `BEFORE: Hon. Justice Silva` |
| `PRESENT` | `PRESENT: Wigneswaran J.` |
| `CORAM` | `CORAM: Fernando CJ, Weerasuriya J.` |

Once detected, names are extracted from the same line, as well as immediately before or after the trigger line.

**Fallback — Title Hunting:**
If trigger words are absent, the system falls back to scanning for judicial title patterns:

```
J.  |  CJ  |  Chief Justice  |  P.C.
```

---

### Stage 3 — Author Judge Extraction (Deductive Parsing)

Authoring formats vary significantly across judgments. The system uses **four prioritized strategies**:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Subtraction Method                                       │
│     Detects "I agree" signatures → removes those judges      │
│     from the bench → remaining judge = author               │
├─────────────────────────────────────────────────────────────┤
│  2. Explicit Declarations                                    │
│     "Judgment delivered by..."  /  "Order by..."            │
├─────────────────────────────────────────────────────────────┤
│  3. Bottom Signature Blocks                                  │
│     Judges listed at the end → joint authorship             │
├─────────────────────────────────────────────────────────────┤
│  4. Mid-Document Signatures                                  │
│     Author signs immediately after a date near the start    │
│     of their judgment section                               │
└─────────────────────────────────────────────────────────────┘
```

---

### Stage 4 — Data Sanitization ("Grammar Nuke")

All name candidates are passed through a strict cleaning pipeline before being included in the final output.

**Filters applied:**

- ❌ Rejects case citations (e.g. strings containing `" v. "`)
- ❌ Strips titles and prefixes: `Chief Justice`, `J.`, `PC`, `Dr.`
- ❌ Removes signature artifacts: `Sgd.`, `I agree`
- ❌ Eliminates common English stopwords: `the`, `in`, `of`, …
- ❌ Filters Sri Lankan address terms: `Colombo`, `Mawatha`, …
- ❌ Removes legal jargon: `Respondent`, `Counsel`, `Appellant`, …

**Final constraints** (word count limits, character filtering) ensure only valid human names reach the JSON output.

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/judge-extraction.git
cd judge-extraction

# Install dependencies and run
uv install
uv run src/extract_judges.py
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `PyMuPDF (fitz)` | Primary PDF text extraction |
| `pdf2image` | Converts PDF pages to images for OCR |
| `pytesseract` | OCR engine for scanned documents |
| `uv` | Package manager & runner |

**Requires:** Python 3.10+

---

## 📄 Output

The pipeline produces a structured **JSON output** with the extracted bench and author judge(s) for each document.

```json
{
  "bench": ["Silva J.", "Fernando CJ", "Weerasuriya J."],
  "author": "Fernando CJ"
}
```

---

## ⚙️ Design Principles

- ✅ **No LLMs or Generative AI** — fully deterministic and rule-based
- ✅ **Auditable** — every decision in the pipeline is traceable
- ✅ **Resilient** — multiple fallback strategies at every stage
- ✅ **Precise** — aggressive sanitization to prevent false positives

---

*Built for the Sri Lankan legal data ecosystem.*
