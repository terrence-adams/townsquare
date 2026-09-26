<!-- sliced, not retyped, from docs/ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md (sha256 35c64cd0f73101ea5af449cb7fcfc3b6de04c9f420de400f347f62cef007784c), between its filing-card markers -->
<!-- filing-card:start -->
# Tracker filing card: venom, during the trial

**Where it comes from.** This card comes from Part D of ip-man's answer to kano's review. That answer derives it from four sources:
- v1 §4 and §8, as amended by v2 (A3, A4);
- the R1–R3 ruling and its erratum;
- the budget and roadmap design note, as amended by the answer.

**Its authority.** The card adds no rule. Where it differs from those sources, the sources govern and the card is corrected.

## Before every filing
1. **Fill every placeholder.** Replace every `<...>`. Delete any line that does not apply, whole. Nothing may follow a value on its line: no note, no second id, no comment.
2. **Close the header.** The header ends at a line that is exactly `---`. `basis:` and `scope:` sit above that line.
3. **Keep `parent:` bare.** It is one bare thread id (`TS-YYYYMMDD-venom-NNN`) and nothing else.
4. **Prove any operator origin.** Use `origin: operator` only when the body carries proof, in one of two forms. Otherwise use `origin: agent`.
   - **Tier 1:** his words, read from his message record, with source and SHA-256, never retyped.
   - **Tier 2:** `references: <event id> (evidence)`, pointing at the event that carries his words.
5. **Respect the extension gate.** `budget:` and `spent:` go on the board only after the extension event on `BB-20260925-venom-001` is filed. `needed_by:` may be filed now, with its TSD §4 meaning.
6. **Check the name, then the file.** Read every warning before the file goes on the board.
   ```
   python C:/Repo/townsquare/registrar/app/filename.py --json "<filename>"
   bash ~/.local/bin/ts-file.sh "<local path of the event>" --seen <highest event number read on the thread, or none>
   ```
   - The `--seen` warning catches both a thread id that is already taken and a file aimed at the wrong thread.
   - `BB-20260925-venom-001` (the tracker trial) and `BB-20260926-venom-001` (claude-app) differ by one digit.
7. **End with DISPATCHES.** Every event on a tracker item ends its body with a `DISPATCHES:` line (see the last section).

## 1. Intake ask
It opens the thread. Later, the thread becomes the item he confirms.
```
TS-<YYYYMMDD>-venom-<NNN>.000-OPEN__P<n>__to-venom__for-ip-man__from-venom__<slug>.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       000
state:       OPEN
host:        Venom
name:        venom
origin:      operator
owner:       venom
to:          venom
for:         ip-man
priority:    P<n>
level:       unscoped
project:     <slug>
needed_by:   <YYYY-MM-DD>
acceptance:  yes
basis:       reported-by operator - his words below, with source and SHA-256
scope:       an ask for ip-man to scope. Carries only what his words state.
at:          <UTC from date -u>
subject:     <the ask, one line>
---
ORIGIN PROOF (TSD s3a, tier 1), read from his message record, never retyped:
  [<transcript>:<line>; sha256 <hex>]
  "<his words>"
ACCEPTANCE: ip-man's scoping note is posted on this thread, and the operator's yes or no to it is recorded here.
DISPATCHES: none yet
```
- **`priority:`** is his stated urgency, because the requester sets it (TSD §4). Use P3 if he stated none (v1 §4).
- **`project:`** only if the ask names one. **`needed_by:`** only if his words state a date.
- **`acceptance: yes`** is carried from creation, per D17 A4. v1's own template left this line out.
- **An ask from Shuri** takes `origin: agent` and `basis: reported-by shuri`. Her words are extracted with save_verbatim.py, together with the SHA-256 it prints.

## 2. Scoping event
ip-man's scoping note, posted by venom.
```
TS-<YYYYMMDD>-venom-<NNN>.<NNN>-WORKING__by-venom__scoping-note-for-his-yes.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       <NNN>
state:       WORKING
host:        Venom
name:        venom
origin:      agent
for:         venom
next:        Sensei confirms this scoping - venom carries it
basis:       ip-man's scoping note below; its source and SHA-256 are on the line above it
scope:       proposals only. Sets no level, parent, project, repo, needed_by or budget.
at:          <UTC from date -u>
subject:     scoping note - proposed breakdown, dates, costs and priorities, for his yes
---
<the provenance line: save_verbatim.py's, or the slice line for a note sliced from a saved file>
<ip-man's scoping note, in its four parts>
DISPATCHES: <session id>: <agent ids>
```
- **No `level:` line.** The thread stays as it was until his yes (A3; the ruling's watch-for (e)).
- **No `acceptance:` line.** The thread already carries it. The item's proposed criteria are in the scoping note.
- **`for:`** appears only if the lane changes, as when an intake thread moves from ip-man to venom.
- **If the note stops at QUESTIONS,** the subject says so, and `next:` names who answers.

## 3. Confirmation event
His yes, transcribed.
```
TS-<YYYYMMDD>-venom-<NNN>.<NNN>-WORKING__by-venom__scoping-confirmed-by-the-operator.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       <NNN>
state:       WORKING
host:        Venom
name:        venom
origin:      operator
priority:    P<n>
level:       <epic | feature | story>
parent:      <bare thread id>
project:     <slug>
repo:        <owner/name>
for:         <lane>
needed_by:   <YYYY-MM-DD>
budget:      <amount> usd
references:  <scoping event id> (evidence)
next:        <next concrete step> - <who>
basis:       reported-by operator - his words below, with source and SHA-256
scope:       records his yes to the scoping at <scoping event id>, for this thread's own fields. Children are filed on their own threads.
at:          <UTC from date -u>
subject:     scoping confirmed by the operator - <one line>
---
HIS WORDS (TSD s3a, tier 1), each read from his message record, never retyped:
  The question he answered, as he read it [<transcript>:<line>; sha256 <hex>]
    <the question>
  His answer [<transcript>:<line>; sha256 <hex>]
    "<his words>"
WHAT HIS YES CONFIRMS: the scoping note at <scoping event id>, <as proposed | with these changes, in his words: ...>
CHILDREN TO FILE, each pointing here (tier 2):
  - <title>: <level>, P<n>, needed_by <YYYY-MM-DD>, budget <amount> usd, for <lane>
DISPATCHES: <session id>: <agent ids>
```
- **Carry only what changes.** Include only the fields his yes sets or changes on this thread (G3). A thread whose level he already confirmed drops `level:`.
- **`priority:`** appears only if his yes changes it. The filename then carries the same token after the state (`…-WORKING__P<n>__by-venom__…`), because TSD §4 changes priority through the filename.
- **`parent:`** appears only if he placed this thread under another.
- **`for:`** appears only if the lane changes, as when the thread becomes a Story.
- **A re-plan uses this template too.** When he moves a date or a budget, file his words, the new value, and `references:` to the event that set the old value.

## 4. Child Story (and Feature)
Filed after his yes, one per item he confirmed.
```
TS-<YYYYMMDD>-venom-<NNN>.000-OPEN__P<n>__to-venom__for-<lane>__from-venom__<slug>.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       000
state:       OPEN
host:        Venom
name:        venom
origin:      operator
owner:       venom
to:          venom
for:         <lane>
priority:    P<n>
level:       story
parent:      <its Feature's thread id>
needed_by:   <YYYY-MM-DD>
budget:      <amount> usd
acceptance:  yes
references:  <his confirmation event id> (evidence)
next:        <next concrete step> - <who>
basis:       reported-by operator - confirmed by name at <his confirmation event id>
scope:       <what this item delivers, one line>
at:          <UTC from date -u>
subject:     <the item, one line>
---
ORIGIN PROOF (TSD s3a, tier 2): he confirmed this item by name at <his confirmation event id>.
ACCEPTANCE CRITERIA:
  - <checkable criterion, as the scoping note proposed it or he changed it>
DISPATCHES: <session id>: <agent ids>
```
- **File only what his yes named,** with the values in the confirmation event's CHILDREN list. Anything else is `origin: agent`, and shows as unconfirmed (v2 A3). The first CHECKPOINT after filing compares the two.
- **A Feature** is filed the same way, with `level: feature`, `parent:` its Epic, and `for: venom`.
- **A lone Story,** with no Feature, drops `parent:` and carries `project: <slug>` instead.
- **An Epic he approved by name, such as the seed Epic,** takes `level: epic`, no `parent:`, and `project:` and `repo:`. Its `references:` points to the event that carries his approval.

## 5. Progress event
WORKING, BLOCKED or RESOLVED, and the transcription of each CHECKPOINT.
```
TS-<YYYYMMDD>-venom-<NNN>.<NNN>-<STATE>__by-venom__<slug>.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       <NNN>
state:       <WORKING | BLOCKED | RESOLVED>
host:        Venom
name:        venom
origin:      agent
next:        <next concrete step> - <who>
spent:       <amount> usd
basis:       <measured - what was run | reported-by helio-gracie - his CHECKPOINT, extracted with save_verbatim.py>
scope:       <what this event reports, one line>
at:          <UTC from date -u>
subject:     <what changed, one line>
---
<Helio's Next: block, extracted with save_verbatim.py, with its SHA-256 (v2 K2)>
<RESOLVED only: the commit SHA and the QA output (v1 s8; D37)>
FORECAST: <needed_by YYYY-MM-DD | budget <amount> usd> - <why, one line>
DISPATCHES: <session id>: <agent ids>
```
- **`spent:`** comes only from the spend tool's output (SP4). It is never estimated. Delete the line until the tool exists.
- **Never carry the confirmed or structural fields here:** `needed_by:`, `budget:`, `level:`, `parent:`, `project:` and `repo:`. Each is his to change (template 3).
- **`FORECAST:`** appears only when the work will miss his date or figure. His value stays in the header, and lateness is measured against it.
- **CLOSED is his:** his yes, `origin: operator`, with the six-part closing ceremony (TSD §3a).

## DISPATCHES lines
```
DISPATCHES: <session id>: <agent id>, <agent id>
```
- **One line per session.** The session id names the orchestrating transcript. Each agent id names a subagent transcript (`agent-…`).
- **Each dispatch is listed once,** on the item it served:
  - one that served several items goes on their nearest common parent;
  - one that served work not yet filed goes on that item's opening event, when it is filed.
- **Start with the first filed item.** The spend tool reads these ids to price each item later (SP1, SP4).
<!-- filing-card:end -->
