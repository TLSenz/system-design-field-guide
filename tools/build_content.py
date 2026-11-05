#!/usr/bin/env python3
"""Convert the system-design curriculum markdown into typed JSON assets.

Usage:
    python3 tools/build_content.py --src ../system-design-curriculum \
        --out app/src/main/assets/content
"""
import argparse
import json
import os
import re
import sys

PARTS = [
    ("part-1", "Foundations", ["00", "01"]),
    ("part-2", "State", ["02", "03", "04", "05", "06"]),
    ("part-3", "Moving Work", ["07", "08"]),
    ("part-4", "The Surface", ["09", "10", "11", "12", "13"]),
    ("part-5", "Operating It", ["14", "15", "16", "17"]),
    ("part-6", "Putting It Together", ["18", "19", "20", "21", "22", "23", "24"]),
]

CHAPTER_RE = re.compile(r"^#\s+(\d{2})\s+[—–-]\s+(.+?)\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
H3_RE = re.compile(r"^###\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^```(.*)$")
OL_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
UL_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")


def slug(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60] or "section"


def join_lines(lines):
    out = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not out:
            out = line
        elif out.endswith(("-", "—", "/")) or line.startswith((")", ",", ".", ":", ";")):
            out += line if out.endswith(("—", "/")) else " " + line
        else:
            out += " " + line
    return out.strip()


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_blocks(lines):
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code
        m = FENCE_RE.match(stripped)
        if m:
            lang = m.group(1).strip()
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append({"type": "code", "lang": lang or "text", "code": "\n".join(code)})
            continue

        # divider
        if stripped in ("---", "***", "___"):
            blocks.append({"type": "divider"})
            i += 1
            continue

        # table
        if stripped.startswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            if len(table_lines) >= 2:
                header = split_row(table_lines[0])
                rows = []
                for raw in table_lines[2:]:
                    cells = split_row(raw)
                    if len(cells) < len(header):
                        cells += [""] * (len(header) - len(cells))
                    rows.append(cells[: len(header)])
                blocks.append({"type": "table", "header": header, "rows": rows})
            continue

        # blockquote (possibly multi-line)
        if stripped.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            text = join_lines(quote)
            blocks.append({"type": "quote", "text": text})
            continue

        # h3
        m = H3_RE.match(stripped)
        if m:
            blocks.append({"type": "heading", "level": 3, "text": m.group(1)})
            i += 1
            continue

        # ordered list
        m = OL_RE.match(line)
        if m:
            items = []
            while i < n:
                mm = OL_RE.match(lines[i])
                if not mm:
                    # continuation line
                    if lines[i].startswith(("   ", "\t")) and lines[i].strip() and items:
                        items[-1]["text"] = join_lines([items[-1]["text"], lines[i]])
                        i += 1
                        continue
                    break
                level = 0 if len(mm.group(1)) < 2 else 1
                items.append({"text": mm.group(3), "level": level})
                i += 1
            blocks.append({"type": "list", "ordered": True, "items": items})
            continue

        # unordered list
        m = UL_RE.match(line)
        if m:
            items = []
            while i < n:
                mm = UL_RE.match(lines[i])
                if not mm:
                    if lines[i].startswith(("   ", "\t")) and lines[i].strip() and items:
                        items[-1]["text"] = join_lines([items[-1]["text"], lines[i]])
                        i += 1
                        continue
                    break
                level = 0 if len(mm.group(1)) < 2 else 1
                items.append({"text": mm.group(2), "level": level})
                i += 1
            blocks.append({"type": "list", "ordered": False, "items": items})
            continue

        # paragraph
        para = []
        while i < n:
            s = lines[i].strip()
            if not s or s.startswith(("```", "|", ">", "#", "---")) or UL_RE.match(lines[i]) or OL_RE.match(lines[i]):
                break
            para.append(lines[i])
            i += 1
        if para:
            blocks.append({"type": "paragraph", "text": join_lines(para)})
        else:
            i += 1

    return blocks


def parse_self_check(lines):
    """Return (questions, remaining_lines_without_selfcheck)."""
    start = None
    for idx, line in enumerate(lines):
        if line.startswith("## ") and "Self-check" in line:
            start = idx
            break
    if start is None:
        return [], lines

    # find end: next h2 at same level (should be none) or end
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if re.match(r"^##\s+\d+\.", lines[idx]) and "Self-check" not in lines[idx]:
            end = idx
            break

    block = lines[start:end]
    answers_at = None
    for idx, line in enumerate(block):
        if line.strip() == "### Answers":
            answers_at = idx
            break

    q_lines = block[1:answers_at] if answers_at is not None else block[1:]
    a_lines = block[answers_at + 1:] if answers_at is not None else []

    def collect(lines_in, stop_at_divider=False):
        items = []
        current = None
        for raw in lines_in:
            s = raw.strip()
            if stop_at_divider and s == "---":
                break
            m = re.match(r"^(\d+)\.\s+(.*)$", raw)
            if m:
                if current:
                    items.append(current)
                current = {"n": int(m.group(1)), "text": m.group(2)}
            elif current is not None and s:
                if s.startswith("**Next:**"):
                    break
                current["text"] = join_lines([current["text"], s])
        if current:
            items.append(current)
        return items

    qs = collect(q_lines)
    ans = collect(a_lines, stop_at_divider=True)
    answers_by_n = {a["n"]: a["text"] for a in ans}
    pairs = []
    for q in qs:
        pairs.append({"q": q["text"], "a": answers_by_n.get(q["n"], "")})
    remaining = lines[:start] + lines[end:]
    return pairs, remaining


def parse_chapter(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read().replace("\r\n", "\n")
    lines = raw.split("\n")

    m = CHAPTER_RE.match(lines[0])
    if not m:
        raise ValueError("bad chapter header: %s" % lines[0])
    number, title = m.group(1), m.group(2)

    self_check, body = parse_self_check(lines)

    # drop trailing "Next:" footer
    while body and (not body[-1].strip() or body[-1].strip().startswith("**Next:**")):
        body.pop()

    # split into sections
    sections = []
    current_title = "Overview"
    current_lines = []
    for line in body[1:]:
        if H2_RE.match(line):
            sections.append((current_title, current_lines))
            current_title = H2_RE.match(line).group(1)
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_title, current_lines))

    out_sections = []
    for idx, (stitle, slines) in enumerate(sections):
        # strip leading dividers/empties
        while slines and (not slines[0].strip() or slines[0].strip() == "---"):
            slines = slines[1:]
        while slines and (not slines[-1].strip() or slines[-1].strip() == "---"):
            slines = slines[:-1]
        if not slines and idx > 0:
            continue
        blocks = parse_blocks(slines)
        if not blocks and idx == 0:
            continue
        out_sections.append({
            "id": "%s-%d" % (number, idx),
            "title": stitle,
            "blocks": blocks,
        })

    words = len(re.findall(r"\S+", raw))
    return {
        "id": number,
        "number": number,
        "title": title,
        "wordCount": words,
        "minutes": max(3, round(words / 220)),
        "sections": out_sections,
        "selfCheck": self_check,
    }


def parse_practice(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().replace("\r\n", "\n").split("\n")

    topic = None
    questions = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        m = H2_RE.match(line)
        if m:
            topic = m.group(1)
            i += 1
            continue
        m = re.match(r"^\*\*(Q\d+)\.\s+(.*)\*\*\s*$", line)
        if m and topic and topic not in ("Scoring",):
            qid, qtext = m.group(1), m.group(2)
            options = []
            i += 1
            while i < len(lines):
                om = re.match(r"^([A-D])\.\s+(.*)$", lines[i].rstrip())
                if not om:
                    break
                options.append(om.group(2).strip())
                i += 1
            # skip blanks
            while i < len(lines) and not lines[i].strip():
                i += 1
            explanation = ""
            if i < len(lines) and "<details>" in lines[i]:
                i += 1  # details + summary line
                while i < len(lines) and "</details>" not in lines[i]:
                    explanation += lines[i].rstrip() + "\n"
                    i += 1
                i += 1
            explanation = explanation.strip()
            am = re.match(r"^\*\*([A-D])(?:[\.\)]|\*\*)", explanation)
            answer_index = None
            if am:
                answer_index = "ABCD".index(am.group(1))
            else:
                # fall back: look for "**B." style inside
                am2 = re.search(r"\*\*([A-D])(?:[\.\)]|\*\*)", explanation)
                if am2:
                    answer_index = "ABCD".index(am2.group(1))
            if answer_index is None or len(options) < 2:
                i += 1
                continue
            questions.append({
                "id": "mcq-%d" % (len(questions) + 1),
                "topic": topic,
                "question": qtext,
                "options": options,
                "answerIndex": answer_index,
                "explanation": explanation,
            })
            continue
        i += 1
    return questions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="../system-design-curriculum")
    ap.add_argument("--out", default="app/src/main/assets/content")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    chapters = []
    for name in sorted(os.listdir(src)):
        if not re.match(r"^\d{2}-.*\.md$", name):
            continue
        chapters.append(parse_chapter(os.path.join(src, name)))

    by_id = {c["id"]: c for c in chapters}
    part_objs = []
    listed = set()
    for pid, ptitle, ids in PARTS:
        ids = [i for i in ids if i in by_id]
        part_objs.append({"id": pid, "title": ptitle, "chapterIds": ids})
        listed.update(ids)
    missing = [c["id"] for c in chapters if c["id"] not in listed]
    if missing:
        part_objs.append({"id": "part-x", "title": "More", "chapterIds": missing})

    index = {
        "title": "System Design",
        "subtitle": "From zero to senior engineer",
        "parts": part_objs,
        "chapters": [
            {
                "id": c["id"],
                "number": c["number"],
                "title": c["title"],
                "minutes": c["minutes"],
                "wordCount": c["wordCount"],
                "sectionCount": len(c["sections"]),
                "questionCount": len(c["selfCheck"]),
            }
            for c in chapters
        ],
    }

    with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    for c in chapters:
        with open(os.path.join(out, "ch-%s.json" % c["id"]), "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, separators=(",", ":"))

    # Practice MCQs come from the balanced bank in tools/mcq/ (see build_mcq.py).
    # The curriculum's 24-practice-bank.md is only a fallback.
    bank_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcq")
    if os.path.isdir(bank_dir):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import build_mcq
        bank = build_mcq.load_bank()
        problems = build_mcq.check(bank)
        if problems:
            sys.exit("MCQ bank failed length checks:\n" + "\n".join(problems))
        mcq = build_mcq.build(bank)
    else:
        practice_path = os.path.join(src, "24-practice-bank.md")
        mcq = parse_practice(practice_path) if os.path.exists(practice_path) else []
    with open(os.path.join(out, "questions.json"), "w", encoding="utf-8") as f:
        json.dump({"mcq": mcq}, f, ensure_ascii=False, separators=(",", ":"))

    total_sections = sum(len(c["sections"]) for c in chapters)
    total_sc = sum(len(c["selfCheck"]) for c in chapters)
    print("chapters: %d" % len(chapters))
    print("sections: %d" % total_sections)
    print("self-check questions: %d" % total_sc)
    print("mcq questions: %d" % len(mcq))
    print("topics: %s" % ", ".join(sorted({q["topic"] for q in mcq})))
    print("assets: %d files, %.1f KB" % (
        len(os.listdir(out)),
        sum(os.path.getsize(os.path.join(out, f)) for f in os.listdir(out)) / 1024.0,
    ))

    empty = [c["id"] for c in chapters if c["selfCheck"] and any(not p["a"] for p in c["selfCheck"])]
    if empty:
        print("WARNING: chapters with missing answers: %s" % empty, file=sys.stderr)


if __name__ == "__main__":
    main()
