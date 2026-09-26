"""Fill B.6's and P2's day-of values (<YYYYMMDD>, <NNN>) precisely, verified.

Usage: python decision-6-fill-day-of-values.py <YYYYMMDD> <NNN>

Reads the pinned B.6 template (kano-review's fenced block, sha256 f0dac81e...)
and the pinned P2 draft (decision-6-p2-body-draft.json, sha256 96a760d0...),
both from this repo. Fills ONLY the "<YYYYMMDD>-venom-<NNN>" pattern -- never
the card's own "<YYYYMMDD>-claude-app-<NNN>" instructional examples, which
must stay as template text -- and verifies byte-for-byte that nothing else
differs from the pinned source before writing the day's files. Stops
(non-zero exit, no files written) if a placeholder remains unfilled, if the
fill hit more or fewer spots than expected, or if any other byte differs
from the pinned template.

<YYYYMMDD> is the UTC date at filing time (the same clock B.6's own `at:`
field uses). <NNN> is the next free BB-<YYYYMMDD>-venom- sequence number on
the live board at that moment (checked by hand against the Bulletin Board
folder before running this script, the same way B.6's own card instructs
claude-app to find its next free number).

Exit 0 and two files written on success. Exit 1 and nothing written on any
check failure -- safe to chain with `&&` in the send command that follows.

This script and the draft it reads are committed in the repo (a stable
path); its OUTPUTS go outside the repo, to an explicit absolute directory,
because the working tree is shared with other sessions.
"""
import sys, hashlib, re, pathlib

KANO_REVIEW = r"C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md"
P2_DRAFT = r"C:\Repo\townsquare\docs\decision-6-p2-body-draft.json"
OUT_DIR = pathlib.Path(r"C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep")

B6_HASH = "f0dac81e737b7f0ffe9ccc7c39174013b002d799e2b54579a6176b240c347a15"
P2_HASH = "96a760d088b49305668e25ff4cca9be9282cba29bd9616b9e89f0c907033c9c7"

FILENAME_TEMPLATE = ("BB-<YYYYMMDD>-venom-<NNN>.000-OPEN__to-all__impact-informational__"
                     "from-venom__claude-app-registered-on-its-behalf-offsite-writer-and-"
                     "posting-card-on-trial.txt")


def die(msg):
    print(f"STOP: {msg}", file=sys.stderr)
    sys.exit(1)


def extract_b6_block(text_lines):
    start_idx = next(i for i, l in enumerate(text_lines) if l.startswith("### B.6 Draft"))
    fence1 = next(i for i in range(start_idx, len(text_lines)) if text_lines[i].strip() == "```")
    fence2 = next(i for i in range(fence1 + 1, len(text_lines)) if text_lines[i].strip() == "```")
    return "".join(text_lines[fence1 + 1:fence2])


def day_body_path(yyyymmdd, nnn):
    return OUT_DIR / f"B6-{yyyymmdd}-venom-{nnn}-body.txt"


def day_p2_path(yyyymmdd, nnn):
    return OUT_DIR / f"p2-body-{yyyymmdd}-venom-{nnn}.json"


def main():
    if len(sys.argv) != 3:
        die("usage: decision-6-fill-day-of-values.py <YYYYMMDD> <NNN>")
    yyyymmdd, nnn = sys.argv[1], sys.argv[2]
    if not re.fullmatch(r"\d{8}", yyyymmdd):
        die(f"YYYYMMDD must be 8 digits, got {yyyymmdd!r}")
    if not re.fullmatch(r"\d{3}", nnn):
        die(f"NNN must be 3 digits, got {nnn!r}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(KANO_REVIEW, "r", encoding="utf-8", newline="") as f:
        lines = f.readlines()
    b6_block = extract_b6_block(lines)
    if hashlib.sha256(b6_block.encode("utf-8")).hexdigest() != B6_HASH:
        die("B.6's template in kano-review.md no longer matches the pinned hash -- "
            "the design changed since this script was written. Do not proceed.")

    with open(P2_DRAFT, "r", encoding="utf-8", newline="") as f:
        p2_draft = f.read()
    if hashlib.sha256(p2_draft.encode("utf-8")).hexdigest() != P2_HASH:
        die("decision-6-p2-body-draft.json no longer matches the pinned hash. Do not proceed.")

    target = "<YYYYMMDD>-venom-<NNN>"
    replacement = f"{yyyymmdd}-venom-{nnn}"
    instructional = "<YYYYMMDD>-claude-app-<NNN>"

    # --- B.6 body: exactly one substitution site (the id: line), instructional pattern untouched ---
    if b6_block.count(target) != 1:
        die(f"expected exactly 1 occurrence of {target!r} in B.6's body, found {b6_block.count(target)}")
    before_instr = b6_block.count(instructional)
    b6_filled = b6_block.replace(target, replacement)
    if b6_filled.count(instructional) != before_instr:
        die("the card's own instructional examples were touched -- aborting")
    if b6_filled.replace(replacement, target) != b6_block:
        die("unexpected difference beyond the one substitution -- aborting")

    # --- Filename token (same pattern, not part of the hashed body) ---
    if FILENAME_TEMPLATE.count(target) != 1:
        die("filename template shape has changed unexpectedly")
    filename = FILENAME_TEMPLATE.replace(target, replacement)

    # --- P2 body: fill the same pattern inside the annotation field only ---
    if p2_draft.count(target) != 1:
        die(f"expected exactly 1 occurrence of {target!r} in the P2 draft, found {p2_draft.count(target)}")
    p2_filled = p2_draft.replace(target, replacement)
    if p2_filled.replace(replacement, target) != p2_draft:
        die("unexpected difference beyond the one substitution in the P2 body -- aborting")
    if "<" in p2_filled or ">" in p2_filled:
        die("a placeholder-shaped angle bracket remains in the filled P2 body -- aborting")

    b6_out = day_body_path(yyyymmdd, nnn)
    p2_out = day_p2_path(yyyymmdd, nnn)
    b6_out.write_text(b6_filled, encoding="utf-8", newline="\n")
    p2_out.write_text(p2_filled, encoding="utf-8", newline="\n")

    print(f"OK: filename            = {filename}")
    print(f"OK: B.6 body written to = {b6_out}")
    print(f"OK: P2 body written to  = {p2_out}")
    # No hash comparison against the pinned draft here: a filled body's hash
    # necessarily differs from the template's (that's the whole point of
    # filling it), so there is nothing meaningful to compare it against.
    # The safety check already ran above, before either file was written.


if __name__ == "__main__":
    main()
