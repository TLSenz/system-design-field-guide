#!/usr/bin/env python3
"""Build the practice MCQs (questions.json) from the bank in tools/mcq/.

Each bank entry lists the correct option separately from the three distractors.
This script:
  * places the correct answer so A/B/C/D are used equally (deterministic, seeded),
  * shuffles the distractors,
  * rewrites {C}/{W1}/{W2}/{W3} in the explanation to the final letters,
  * checks that the correct option does not stand out by length.

Usage:
    python3 tools/build_mcq.py [--out app/src/main/assets/content/questions.json] [--report]
"""
import argparse
import importlib.util
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BANK_DIR = os.path.join(HERE, "mcq")
SEED = 20261105
LETTERS = "ABCD"

# Length guard: the correct option may not be more than this much longer than
# the average distractor, nor the shortest by a wide margin.
MAX_RATIO = 1.25
MIN_RATIO = 0.80
# Across the whole bank, the correct option should be the longest (or the
# shortest) option in no more than this share of questions (chance is 25%).
MAX_LONGEST_SHARE = 0.35
MAX_SHORTEST_SHARE = 0.35


def load_bank():
    questions = []
    for name in sorted(os.listdir(BANK_DIR)):
        if not (name.startswith("bank_") and name.endswith(".py")):
            continue
        spec = importlib.util.spec_from_file_location(name[:-3], os.path.join(BANK_DIR, name))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        questions.extend(mod.QUESTIONS)
    return questions


def balanced_positions(n, rng):
    """Positions 0..3 used equally, shuffled, with no run longer than 2."""
    base = [i % 4 for i in range(n)]
    for _ in range(10000):
        rng.shuffle(base)
        if all(not (base[i] == base[i - 1] == base[i - 2]) for i in range(2, n)):
            return base
    return base


BULLET_RE = re.compile(r"^- \*\*([A-D]):\*\*")


def sort_option_bullets(text):
    """Order consecutive '- **X:**' bullets alphabetically by option letter."""
    lines = text.split("\n")
    out, run = [], []
    for line in lines + [None]:
        m = BULLET_RE.match(line) if line is not None else None
        if m:
            run.append((m.group(1), line))
            continue
        out.extend(l for _, l in sorted(run))
        run = []
        if line is not None:
            out.append(line)
    return "\n".join(out)


def build(bank):
    rng = random.Random(SEED)
    positions = balanced_positions(len(bank), rng)
    out = []
    for idx, (q, pos) in enumerate(zip(bank, positions)):
        assert len(q["w"]) == 3, "need exactly 3 distractors: %s" % q["q"][:60]
        wrong = list(enumerate(q["w"], start=1))
        rng.shuffle(wrong)
        options = [None] * 4
        letter_of = {}
        options[pos] = q["c"]
        letter_of["C"] = LETTERS[pos]
        slots = [i for i in range(4) if i != pos]
        for slot, (wi, text) in zip(slots, wrong):
            options[slot] = text
            letter_of["W%d" % wi] = LETTERS[slot]
        explanation = q["x"]
        for key, letter in letter_of.items():
            explanation = explanation.replace("{%s}" % key, letter)
        assert "{" not in explanation.replace("{}", ""), "unreplaced token in: %s" % q["q"][:60]
        explanation = sort_option_bullets(explanation)
        out.append({
            "id": "mcq2-%d" % (idx + 1),
            "topic": q["topic"],
            "question": q["q"],
            "options": options,
            "answerIndex": pos,
            "explanation": explanation,
        })
    return out


def check(bank, report=False):
    problems = []
    longest = 0
    shortest = 0
    for i, q in enumerate(bank, start=1):
        lc = len(q["c"])
        lw = [len(w) for w in q["w"]]
        ratio = lc / (sum(lw) / 3.0)
        if lc >= max(lw):
            longest += 1
        if lc <= min(lw):
            shortest += 1
        if ratio > MAX_RATIO or ratio < MIN_RATIO:
            problems.append("#%d ratio %.2f: %s" % (i, ratio, q["q"][:70]))
        if report:
            print("#%-3d %-28s ratio %.2f  c=%3d  w=%s" % (i, q["topic"][:28], ratio, lc, lw))
    n = float(len(bank))
    print("questions: %d, correct is longest in %d (%.0f%%), shortest in %d (%.0f%%)" % (
        len(bank), longest, longest / n * 100, shortest, shortest / n * 100))
    if longest / n > MAX_LONGEST_SHARE:
        problems.append("correct option is the longest in %.0f%% of questions" % (longest / n * 100))
    if shortest / n > MAX_SHORTEST_SHARE:
        problems.append("correct option is the shortest in %.0f%% of questions" % (shortest / n * 100))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "app", "src", "main", "assets", "content", "questions.json"))
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    bank = load_bank()
    problems = check(bank, args.report)
    for p in problems:
        print("LENGTH:", p)
    if problems:
        sys.exit(1)

    mcq = build(bank)
    counts = [sum(1 for m in mcq if m["answerIndex"] == i) for i in range(4)]
    print("answer positions A/B/C/D: %s" % counts)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"mcq": mcq}, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote %s" % os.path.abspath(args.out))


if __name__ == "__main__":
    main()
