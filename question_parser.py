"""
Ziglag Institute Question Parser
Supports Word (.docx), PDF (.pdf), Excel/CSV (.csv), and Plain Text (.txt).
Extracts questions, options (A-D), answers, hints, and step-by-step explanations.
"""

import re
import io

try:
    import docx
except ImportError:
    docx = None

try:
    import pymupdf  # PyMuPDF
except ImportError:
    pymupdf = None


def extract_text_from_file(file_bytes, filename):
    """Extract raw text from docx, pdf, or text files."""
    ext = filename.lower().split('.')[-1]

    if ext == 'docx':
        if not docx:
            raise ImportError("python-docx is required for Word document parsing.")
        doc = docx.Document(io.BytesIO(file_bytes))
        lines = []
        for p in doc.paragraphs:
            if p.text.strip():
                lines.append(p.text.strip())
        # Also extract text from any tables in the document
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    lines.append("  ".join(row_cells))
        return "\n".join(lines)

    elif ext == 'pdf':
        if not pymupdf:
            raise ImportError("pymupdf is required for PDF parsing.")
        pdf = pymupdf.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        for page in pdf:
            p_text = page.get_text()
            if p_text.strip():
                pages_text.append(p_text.strip())
        return "\n\n".join(pages_text)

    else:
        # Plain text / CSV
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return file_bytes.decode('latin-1', errors='ignore')


def parse_questions_from_text(raw_text, default_subject="mathematics", default_topic="General", default_difficulty="Intermediate", default_year=2026):
    """Intelligently parse raw text into structured CBT question objects."""
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

    # 1. Check for dedicated Answer Key / Marking Scheme at the end
    answer_key = {}
    key_match = re.search(r'(?i)(?:^|\n)\s*(?:answer\s+key|marking\s+scheme|answers?\s+summary|official\s+keys?)\s*[:\n]+([\s\S]+)$', text)
    if key_match:
        key_section = key_match.group(1)
        for k_match in re.finditer(r'(\d+)[\.\)\:\-\s]+([A-D])\b', key_section):
            q_num = int(k_match.group(1))
            answer_key[q_num] = k_match.group(2).upper()
        # Truncate answer key so it doesn't get parsed as questions
        text = text[:key_match.start()]

    # 2. Find question boundary headers: "1. ", "1) ", "Question 1:", "[1] "
    matches = list(re.finditer(r'(?:^|\n)\s*(?:Q(?:uestion)?\s*)?(\d+)[\.\)\]\:]\s+', text))
    questions = []

    if matches:
        for idx, m in enumerate(matches):
            q_num = int(m.group(1))
            start_pos = m.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            q_body = text[start_pos:end_pos].strip()

            parsed_q = parse_single_question_body(
                q_body, q_num, answer_key.get(q_num),
                default_subject, default_topic, default_difficulty, default_year
            )
            if parsed_q:
                questions.append(parsed_q)
    else:
        # Fallback if unnumbered: split by double linebreaks
        blocks = re.split(r'\n{2,}', text)
        for idx, block in enumerate(blocks, 1):
            parsed_q = parse_single_question_body(
                block.strip(), idx, answer_key.get(idx),
                default_subject, default_topic, default_difficulty, default_year
            )
            if parsed_q:
                questions.append(parsed_q)

    return questions


def parse_single_question_body(body, q_num, key_answer=None, default_subject="mathematics", default_topic="General", default_difficulty="Intermediate", default_year=2026):
    """Parse a single question's body into question text, options, answer, explanation."""
    if len(body) < 8:
        return None

    # Extract Explanation / Solution
    explanation = ""
    exp_match = re.search(r'(?i)(?:explanation|solution|derivation)[\s\:\-]+([\s\S]+?)(?=$|\n[A-D][\.\)])', body)
    if exp_match:
        explanation = exp_match.group(1).strip()
        body = body[:exp_match.start()] + body[exp_match.end():]

    # Extract Hint if present
    hint = ""
    hint_match = re.search(r'(?i)hint[\s\:\-]+([\s\S]+?)(?=$|\n[A-D][\.\)]|\n(?:explanation|solution))', body)
    if hint_match:
        hint = hint_match.group(1).strip()
        body = body[:hint_match.start()] + body[hint_match.end():]

    # Extract Inline Correct Answer: "Ans: B", "Answer: C", "Correct: A"
    inline_ans = None
    ans_match = re.search(r'(?i)(?:ans(?:wer)?|correct(?:\s*option)?|key)[\s\:\-]+([A-D])\b', body)
    if ans_match:
        inline_ans = ans_match.group(1).upper()
        body = body[:ans_match.start()] + body[ans_match.end():]

    correct_option = inline_ans or key_answer or "A"

    # Extract options: A, B, C, D
    # Match A. ... B. ... C. ... D. ... or (A) ... (B) ... or [A] ...
    opt_pattern = r'(?:^|\n|\s{2,})(?:\(([A-D])\)|\[([A-D])\]|([A-D])[\.\)\:\-])\s*'
    opt_splits = re.split(opt_pattern, body)

    options = []
    question_text = ""

    if len(opt_splits) > 1:
        question_text = opt_splits[0].strip()
        question_text = re.sub(r'^(?:Q(?:uestion)?\s*)?\d+[\.\)\]\:]\s*', '', question_text)

        idx = 1
        while idx < len(opt_splits):
            label = opt_splits[idx] or opt_splits[idx + 1] or opt_splits[idx + 2]
            text_val = opt_splits[idx + 3].strip() if (idx + 3) < len(opt_splits) else ""
            if label:
                options.append({
                    "label": label.upper(),
                    "text": text_val
                })
            idx += 4
    else:
        question_text = re.sub(r'^(?:Q(?:uestion)?\s*)?\d+[\.\)\]\:]\s*', '', body).strip()

    # Ensure all 4 options (A, B, C, D) are defined
    existing_labels = {o["label"] for o in options}
    for req_label in ["A", "B", "C", "D"]:
        if req_label not in existing_labels:
            options.append({
                "label": req_label,
                "text": f"Option {req_label}"
            })

    options.sort(key=lambda o: o["label"])

    if not explanation:
        explanation = f"Correct option is ({correct_option}). Official step-by-step solution provided by Ziglag Institute."

    return {
        "id": f"q_import_{q_num}_{int(abs(hash(question_text)) % 100000)}",
        "question_text": question_text,
        "options": options,
        "correct_option": correct_option,
        "hint": hint,
        "explanation": explanation,
        "subject": default_subject.lower(),
        "topic": default_topic,
        "difficulty": default_difficulty,
        "year": int(default_year)
    }
