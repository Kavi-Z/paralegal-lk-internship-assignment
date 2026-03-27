# Intern Assessment – Judge Extraction Task

## Overview

You are required to build a **deterministic extraction system** to identify:

1. **bench** – All judges listed as part of the bench (coram/present/before).
2. **author_judge** – Judge(s) who authored/delivered the final judgment (may be one or more).

You must extract this information from the court decisions provided.

---

## Input

- All input court decisions are **PDF files** placed inside the `data/` folder.
- There are exactly **4 court decisions**, named `sample-judgment-1.pdf` through `sample-judgment-4.pdf`.
- Your program only needs to handle PDF files.

Your program must automatically process all `.pdf` files inside the `data/` folder.

---

## Required Output

Your program must generate structured output in JSON format.

For each input file, produce:

{
  "source_file": "sample-judgment-1.pdf",
  "bench": ["Judge Name 1", "Judge Name 2"],
  "author_judge": ["Judge Name 1"]
}

Your program must write one JSON file per input file into the `output/` folder, matching the input filename:

- `data/sample-judgment-1.pdf` → `output/sample-judgment-1.json`
- `data/sample-judgment-2.pdf` → `output/sample-judgment-2.json`
- etc.

The output must be reproducible by running your script.

---

## Rules (Very Important)

1. ❌ No LLMs or Generative AI models.
   - No OpenAI, Anthropic, OpenRouter, Gemini, etc.
   - No AI-based extraction tools.
2. ❌ No manual editing of results.
3. ✅ You may use any non-LLM approach, including but not limited to:
   - Regex and rule-based parsing
   - NLP libraries (e.g. spaCy, NLTK, stanza)
   - Any other method that does not involve prompting a generative model
4. ✅ All work must be included in a Git repository.
5. ✅ The project must include clear execution instructions in `README.md`.
6. ✅ Your `README.md` must include an **## Approach** section describing your extraction approach in plain English.

---

## What We Are Evaluating

We will evaluate:

- Correctness of `bench` extraction
- Correctness of `author_judge` extraction
- Robust handling of formatting variations
- Code structure and clarity
- Reproducibility of results

---

## Environment & Execution

- Use **uv** for dependency management. You may assume `uv` is already installed on the testing environment.
- Python version must be **3.11 or higher**.
- You may add any dependencies you need, but they must be declared in `pyproject.toml` so that `uv sync` installs them.
- Your `README.md` must include **complete instructions** to clone, set up, and run your project. We will evaluate your submission by following these instructions exactly.

---

## Submission Instructions

Send an email with the subject line: "Application for Engineering Internship - {Your First Name} {Your Last Name}"
to admin@paralegal.lk.

Your email should include:

- A link to your GitHub repository with the answer.
    - Note: your answer repository **must** be named `paralegal-lk-internship-assignment` and **must** be public
- Your CV as an attachment
- Alongside a cover letter explaining why you are interested in the role 
---

## Notes

- Your solution must run without manual intervention.
- Code quality and clarity matter.
- Make reasonable assumptions, but document them in your README.
