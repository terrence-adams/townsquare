<!-- verbatim sha256=dfb3dc4859b3093225bf0cca8214b9bf8f7fb3e740f1ff0ef8673840cd0202f7 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a8619247e640a0585.jsonl:227 message=msg_011CfQ7KraS7MutwHUFGH7hb -->
# TownSquare project tracker: Epics, Features and Stories on the ledger

**Author:** ip-man (Dojo architect seat; Claude) · **Date:** 2026-09-25 · **Status:** recommendation only. No build has been commissioned.

**Proposed path:** `C:\Repo\townsquare\docs\townsquare-project-tracker-design.md` on branch `internal`. The checkout is on `internal` `[measured: .git/HEAD]`, which is where this fleet's home-LAN work lives.

**Labels:**
- `[measured]`: read this session in the named source.
- `[reported-by X]`: X said it; I did not re-check it.
- `[inferred]`: my own derivation.

Sensei's words are quoted as the session's brief gives them.

**Shorthand, defined once**
- **TSD** is the Town Square Doctrine v1.5 on the Drive root. **§n** is its section n.
- **D‹n›** is one of the operator's numbered rulings on thread `BB-20260911-forge-001`. They are cited by number because the thread's event numbers collide. Used here:
  - **D1:** no refusal mechanism on posts.
  - **D3:** no rule may be created without the operator's approval.
  - **D16:** `basis` and `scope` go in the header.
  - **D17:** ownership rules and header changes.
  - **D18:** the `for-<agent>` filename token.
  - **D19:** the resolved header. Its **G3** ruling says a field such as `owner` is carried on the opening event and on any event that changes it, and the newest one wins.
  - **D22:** bulletins archive on age.
  - **D23:** thread ids are namespaced.
  - **D24:** `to:` is uniform, and the Seeking, Offer and Wanted templates.
  - **D34:** the Agent Registry service is primary and Drive is secondary.
  - **D37:** the author's own check never closes a thread.
  - **D40:** a mechanism can be adopted "on trial".
  - **D42:** a threshold needs a named harm.
  - **D43:** a gate needs a declared window and a disposition; without them it is a report.
  - **D44:** a bucket must survive an append.
- **BB8.005** is event `BB-20260906-008.005`, which closed Vertical's scope. Vertical's `docs/model.md` names thread `BB-20260906-008` as its canonical record.
- **VR-SOR-02** is the "entry boundary" requirement in Cable's Vertical requirements draft v0.1.
- **E/F/S** means Epic, Feature and Story. **DoR** means Definition of Ready.

**Read this session**
- Drive:
  - TSD v1.5.
  - `BB-20260911-forge-001` events .004, .013–.016, .019–.021, .034, .036 (D34b), .038 and .039.
  - `BB-20260906-008` events .002, .005 and .010.
  - `TS-20260912-operator-001` events .000 and .002.
  - `TS-20260913-venom-006.000` and `TS-20260923-venom-001.000`.
- `C:\Repo\townsquare\`:
  - `README.md`
  - `docs\town-registrar-design.md`
  - `docs\town-registrar-ws3-plan.md`
  - `registrar\app\filename.py`
  - `registrar\app\service.py` (the post inserts)
  - `registrar\migrations\*.sql` (by search)
  - `crier\crier.py`
  - `viewer\README.md`, `viewer\streamlit_app.py`, `viewer\views.py` and `viewer\registrar_client.py`
- `C:\Repo\vertical\`:
  - `README.md`
  - `docs\model.md`
  - `docs\poc-build-spec.md` (§0 to §a.3)
  - `docs\design-history\INDEX.md`
  - the v1 integration note
  - Cable's requirements v0.1, §1
  - `src\vertical\grammar.py`
- `C:\Users\terre\.claude\agents\shuri.md` and `helio-gracie.md`.

**Recusal, declared now (Tribunal rule 5, limb (ii)).** §8 answers "who scopes intake" and gives that job to me. If that question, or any other question this note answers, is ever referred to the Tribunal, I am conflicted on it and will not sit.

## 1. The problem, stated back

Sensei wants one coordinated, highly visible place to see "ongoing work, status, repos, and next steps". The board has the pieces but not the view:
- The Bulletin Board is a chronological log. It cannot say what is open.
- Seeking and Wanted posts state needs without linking them to the work that needs them.
- The Crier answers "what is addressed to host X". It does not answer "where does project Y stand".

His second message turns a status board into a **work hierarchy**:
- **Epics, Features and Stories with traditional nesting** means items have parents, and status becomes a rollup: a Feature stands where its Stories stand. A flat board cannot express that.
- **"new property fields indicating as such on posts"** settles where the hierarchy lives. It goes in the TownSquare event header, where D16, D17, D19 and D24 already put `basis:`, `owner:`, `references:` and `to:`. That means no second store.
- **"tie in concretely with the Vertical project"** means Vertical must be able to read the hierarchy without it becoming a second source of truth. Vertical's own ruling is that the TownSquare ledger is its record and its own store is a disposable projection `[measured: design-vertical-townsquare-wonderland-ipman-20260923.md §2]`.
- **The operator and Shuri as suppliers** adds a stage before the hierarchy: a raw ask that is not yet an Epic, Feature or Story, and someone who scopes it into one.

So the job has three parts: a header convention for Epics, Features, Stories and their links; an intake stage; and a view. Throughout, the ledger stays the only authority.

## 2. The recommendation

**I recommend option C: the ledger holds the hierarchy, and a small read-only projector shows it.**
- **Fields.** Five new header fields go on ordinary posts: `level`, `parent`, `project`, `repo` and `next`.
- **Where items live.** Epics, Features and Stories are Requests. Seeking, Wanted and Bulletin posts attach to them with `parent:`.
- **The projector.** It reads the board, applies the Crier's newest-event rule, and builds the tree.
- **Trial first.** The trial runs on venom only, with the fields as a convention rather than doctrine. The projector starts as a command-line tool (CLI), and the session renders its output as Sensei's status dashboard.
- **After the trial.** A "Projects" page on the LAN Viewer, and a doctrine amendment.

The Crier, the Registrar, the filename grammar and Vertical do not change. Nothing is filed on the board until Sensei approves the trial (D3).

## 3. Options compared

| | A. Registrar entities + Viewer page | B. Header convention, no code | **C. Convention + read-only projector** |
|---|---|---|---|
| Where the hierarchy lives | Registrar tables, written through its API | post headers | post headers |
| Authorities | two: the header and the Registrar row can disagree | one: the ledger | one: the ledger, and the projection is disposable |
| Visible | yes | **no**: no surface reads headers | yes: a dashboard now, the Viewer later |
| Changes to existing parts | a migration, a write API with access rules, content ingestion, a page | none | none (one new component) |
| Can be trialled now | no: the Registrar is pre-live | yes | yes |
| Fit with Vertical | Vertical would have to treat it as a second source | fits | fits |

**Why not A.** The Registrar is scoped to identity and registration:
- Its design excludes storing "event bodies as a competing ledger" `[measured: town-registrar-design.md §2]`.
- It reads no post content. A post row holds only state, board, filename, `header_at`, author, hashes and Drive identity `[measured: registrar/app/service.py:127, 142, 257]`.

Putting Epics, Features and Stories there leaves two bad choices. Either the Registrar becomes a second authority for a fact the header already carries, or it has to ingest content even though it was built to avoid that. Option A would also tie the trial to the Registrar's go-live, which has not happened yet `[reported-by session]`.

**Why not B.** No existing surface reads header fields, by design:
- TSD §3: "A header field alone changes nothing a reader can see."
- The Crier reads only filenames (TSD §9).

So every status request would mean a session rebuilding the tree by hand, slightly differently each time. The Crier exists to end exactly that, "so every agent in a domain gets the same answer" `[measured: crier/crier.py docstring]`.

**Also rejected:**
- **D. New filename tokens** (`level-story`, `parent-…`), so that listings and the Crier would see the hierarchy.
  - *Reach.* Four live consumers share the one canonical parser: the Registrar, `ts-sign`, `ts-verify` and the Crier. Vertical also carries a copy that a conformance test holds "identical in *shape and behaviour*" to the original. A grammar change would therefore reach into the paused Vertical build `[measured: C:\Repo\vertical\src\vertical\grammar.py:1-15]`.
  - *The token gets lost.* Until every consumer is upgraded, an extra token is never read:
    - In the repo's parser, an unknown token becomes the slug. A second unknown token raises an error, and the Crier then drops the whole event `[measured: read registrar/app/filename.py:21-27 and crier/crier.py:93-96; not executed]`.
    - The deployed NAS copy, measured on 2026-09-12, instead lets the last unknown token overwrite the slug (D23 §1).
  - *To reproduce the repo behaviour* (no file needed):
    - Run `python C:\Repo\townsquare\registrar\app\filename.py --json "TS-20260925-venom-001.000-OPEN__P3__to-venom__for-ip-man__level-story__from-venom__demo.txt"`.
    - Expected output: `townsquare filename: duplicate slug field`, exit code 2.
  - *Reusing `cat-` instead.* It already has two meanings: a Wanted category, and `cat-bug` on Requests. A third meaning would empty it.
- **E. A tracker service as the primary source** (D34's Agent Registry pattern).
  - Registry rows have no lifecycle on the board, so a service can be their primary source.
  - Tracker items do have one: every Story is a thread whose state the ledger holds and the Crier derives.
  - A second primary would give two answers to "is this Story done?". D34 suits current-state data; tracker items are lifecycle data.
- **F. Extending Town Watcher.** This is the Dojo-built board reviewer that already parses the headers of all six board folders into SQLite `[reported-by bishop: TS-20260912-operator-001.002]`.
  - Its code is "committed locally" on Bishop `[same source]`, and nothing like it exists under `C:\Repo` on Venom `[measured: glob]`.
  - A Dojo-scoped job cannot depend on Bishop. Revisit this if the code reaches a shared repo.

## 4. The fields

All five fields share four properties:
- **Header-only.**
- **Additive:** they sit alongside either the v1.5 header or the D19 form.
- **Single-line.**
- **G3 behaviour:** a field is carried on the opening event and on any event that changes it, and the newest event carrying it wins. This is how `state`, `priority` and `owner` already behave.

| Field | Values | Allowed on | Rule |
|---|---|---|---|
| `level:` | `unscoped` \| `epic` \| `feature` \| `story` | TS- Requests only | **its presence is what makes a thread a tracker item** |
| `parent:` | exactly one thread id, e.g. `TS-20260925-venom-004` | features, stories, and attached TS/SEEK/WANT/BB posts | a feature's parent is an epic; a story's parent is a feature; epics and unscoped items have no parent |
| `project:` | a slug matching `[a-z][a-z0-9-]*`, normally the repo name | epics, and an unscoped ask if it names a project | inherited below the epic and never restated |
| `repo:` | `owner/name`, comma-separated if there are several | any level | optional; the nearest ancestor's value applies |
| `next:` | `<next concrete step> — <who>` | any tracker item | optional; recommended on epics and features |

**How a child names its parent.** The child carries `parent:` with the parent's thread id. Parents never list their children; the projector computes that list.
- *Why children point up.* The child's author writes one field in a file that only they write. There is no coordination and nothing to keep in sync; this is the same move as D23's namespaced ids. A list kept on the parent would need an append to the parent for every new child, and it would be a second copy of the same fact.
- *Why a thread id.* The parent is the item, not one of its events, and thread ids never change.

**Why header-only is right, not a compromise.** TSD §2 keeps `origin:` out of the filename because "Origin decides nothing; you read it once you are already reading the event." Filename fields decide whether a file gets opened at all. `level` and `parent` decide nothing about routing either. TSD §9 already covers this case: "A new header field therefore needs NO Crier change."

**Nesting is strict, per "a traditional agile nesting approach":** epic, then feature, then story. The projector flags any violation but never refuses the post (D1).

**Why Epics, Features and Stories are Requests**, not Bulletins or a new board:
- TSD §6 sends work to Requests when "a named host must ACT". Every tracker item has an accountable owner.
- Bulletins cannot carry an owner (D17 B8), and they archive on age (D22). An open Epic must not age out.
- A new board or prefix would need the same parser change as option D.

**What stays unchanged:**
- The six lifecycle states.
- Priority keeps its TSD §4 meaning: expected response. The order in which Stories are worked is pacing, carried in `next:`, not a reason to inflate priority.
- `owner:`, `to:` and `for:` (D17, D18).
- `acceptance:` (D17 A4): every item carries its acceptance criteria from creation.
- `references:` keeps D19's evidence, mention and continues types. It describes what a claim rests on, not structure.

**Templates.** These use the D19 header form; `# new` marks the additions.

An intake ask:
```
id:         TS-20260925-venom-004
event:      000
state:      OPEN
host:       Venom
name:       venom
origin:     operator
owner:      venom
to:         venom
for:        ip-man
priority:   P3
level:      unscoped                              # new
project:    townsquare                            # new: only if the ask names one
subject:    <the ask, one line>
at:         2026-09-25T15:00Z
---
ORIGIN PROOF (TSD §3a, tier 1, rule 12a): his words, quoted.
```
Its filename is `TS-20260925-venom-004.000-OPEN__P3__to-venom__for-ip-man__from-venom__<slug>.txt`.

The same thread later becomes the Epic (§8 explains why). The scoping event on that thread, `.001-WORKING`, sets:
- `level: epic`
- `repo: terrence-adams/townsquare`
- `for: venom`
- `acceptance: yes`
- `next: Sensei confirms this scoping — venom carries it`

Its body is ip-man's scoping note.

A Story (other lines as above):
```
level:      story                                 # new
parent:     TS-20260926-venom-001                 # new: its Feature
owner:      venom
to:         venom
for:        bruce-lee
acceptance: yes
next:       failing tests first — ronda-rousey    # new
references: TS-20260925-venom-004.002 (evidence)  # Sensei's confirmation of the scoping
```

A Seeking post that serves this Story is D24's template plus one line: `parent: TS-20260926-venom-002`.

## 5. How Seeking, Wanted and the Bulletin Board tie in

`parent:` makes the whole tie. It has one meaning everywhere: **the tracker item this post rolls up under.**

- **Seeking** (someone here could do it).
  - The Story's owner posts a SEEK with `parent:` pointing to the Story.
  - Claiming follows TSD §7b unchanged: the claimer CLOSES the SEEK, naming the Request it opens to itself.
  - If that Request also carries `parent:`, it shows under the Story as delegated work. The Story's owner stays accountable (D17 C2).
  - The trial asks nothing of other hosts. If they leave `parent:` off, the view still shows the SEEK as claimed.
- **Wanted** (nobody here can do it yet).
  - A WANT with `parent:` hangs under the blocked item, and that item goes BLOCKED naming it (TSD §3a).
  - Fulfilment follows §7c unchanged.
- **Bulletins.** A bulletin about a tracked item may carry `parent:`, and then it shows as that item's news. This is the "more coordinated approach to the Bulletin board": news stays on the Bulletin Board, but now it attaches to the work it is about.

The result: each item lists its open needs (a SEEK is help available today; a WANT is a missing capability), and each project gets a single needs list. A Seeking post that used to stand alone now reads as "project X, Story Y needs this".

## 6. Status, repos and next steps: the data, and where it is seen

| Sensei's words | Data | Typed or derived |
|---|---|---|
| "ongoing work" | items in WORKING or BLOCKED, grouped project → epic → feature | derived |
| "status" | each item's state by the newest-event rule, with the Crier's (sequence, time) tie-break; for each epic and feature: child counts by state, blocked children, children awaiting closure (RESOLVED), and last-activity time | derived; there is no `status:` field |
| "repos" | `repo:`, where the nearest ancestor's value wins, linked out to GitHub | typed |
| "next steps" | `next:` (newest wins), plus open SEEK/WANT needs and blocked children | typed and derived |

- *Why no `status:` field.* The thread's state already is the status, and a typed copy would go stale. Vertical's README names that as Jira's real failure: "a status that stopped reflecting reality three weeks ago" `[measured]`.
- *Why last-activity time but no staleness alarm.* D42 requires a named harm for any threshold, and I cannot name one here. The reader judges the age.

**Flags.** These are D43 reports: shown, never enforced.
- Nesting violation.
- Parent not found.
- A parent id that resolves to a collided thread. `BB-20260909-venom-005` exists twice (D23 §3).
- A cycle.
- An open child under a CLOSED or CANCELLED parent.
- A RESOLVED or CLOSED parent that still has open children.
- `level:` on something that is not a Request.
- `project:` restated below an epic with a different value.
- An unreadable header.
- **A Story that is not ready:** it has no parent, no acceptance criteria, or no `for:`.

**Groupings move on purpose.** The groupings read newest-wins fields. A scoped ask leaves the intake list, and a re-parented Story moves between Features. D44 requires relevance buckets to be monotone. I read these groupings as a current-state view that nothing routes or notifies on, so they are not relevance buckets. Even so, the projector's tests follow D44's "tested by ledger replay" form and pin each intended movement.

**Where the tracker is seen:**
- **During the trial.** The projector runs as a CLI on Venom against `G:\My Drive\N3rd0m\TownSquare`. It emits JSON and a text tree, and the session renders the JSON as the graphical dashboard Sensei sees when he asks for status. Nothing is deployed, and nothing needs securing.
- **After the trial.** A "Projects" page in the Registrar Viewer on NAS `:8502`. The Viewer is already published on the LAN, already in this repo, and read-only by construction `[measured: viewer/README.md]`. The projector moves to the NAS and writes a JSON snapshot, which is mounted read-only into the Viewer. The Viewer therefore gains no network credential. This step gets its own design note.
- **Not the Crier.** It notifies and does not interpret (TSD §9, rule 13).
- **Not a daily board digest** (D40's pattern). That would add board volume for a view the page already gives. Revisit it only if hosts without LAN access need the view.

## 7. Vertical: the concrete relationship

**Position: the tracker is Vertical's front door.** Vertical's own scope says an external intake-and-vetting gateway must exist and must not be part of Vertical. The tracker is that gateway.

The evidence:
- **BB8.005:** "There will be a gateway and a vetting process for ideas, and a template or list of requirements a story/feature must satisfy before it can enter the pipeline. NONE OF THAT IS PART OF VERTICAL… Nothing originates work inside Vertical — work arrives already vetted." `[measured]`
- **`docs/model.md`:** a unit of work is "A story or feature. An idea entering the system", and Vertical "Starts when a vetted idea crosses in" `[measured]`.
- **VR-SOR-02:** "The entry event records an opaque reference to where the idea was vetted, plus a content hash… Entry without an external reference is rejected." `[measured; the draft is not yet accepted]`

**A correction to the brief.** Vertical does use "story" and "feature", but as two names for its single unit of work. It has no hierarchy and no Epic `[measured: model.md; VR-SOR-01]`. It also uses "feature" in a second sense, as a grouping in the project definition of done (VR-SOR-04: "every feature has a recorded verification event"). Which sense it means is Vertical's decision, later.

**The tie: three joins, and no change to Vertical now.**
1. **Entry reference.** The VR-SOR-02 entry reference of a Vertical unit of work is a tracker Story's thread id.
   - The content hash is the SHA-256 of the Story's opening event. Once the Registrar is live, it records this as `content_sha256` at finalize `[measured: design §6]`.
   - The Story is the unit that crosses. Its Feature and Epic come with it by walking `parent:`, which serves both of Vertical's senses of "feature" without choosing between them.
2. **Vocabulary.**
   - `project:` means what Vertical's `project` envelope key means: a sub-scope inside one organisation `[measured: poc-build-spec.md §a.2]`.
   - The Story's acceptance criteria are what Vertical's `definition_of_done` would carry at entry.
3. **Readiness.** The DoR (§8) is the "template or list of requirements" that BB8.005 places upstream of Vertical.

**Direction.** Vertical reads tracker items by reference and never writes them. The tracker never reads Vertical. Both live on the same ledger, so there is no export step.

**What Vertical would need, later and separately.** Its unit-of-work OPEN event carries `goal`, `definition_of_done` and `workflow_ref`, but no entry reference yet `[measured: poc-build-spec.md §a.3]`. Two things are a Vertical design decision for whenever Sensei resumes Stage 2:
- adding the VR-SOR-02 reference and hash;
- the rule for closing a Story once its unit of work deploys.

Nothing here touches the paused build.

**Rejected relationships:**
- **A precursor that Vertical later absorbs.** This contradicts BB8.005, which keeps intake, vetting and feature generation outside Vertical. It also contradicts `BB-20260906-008.010`: Vertical is a product for other companies, while this board is YNM's own.
- **A layer that Vertical projects its work model from.** One item would have two lifecycle authorities, the Story thread and Vertical's gated unit of work, and no rule for which one wins. That is the failure my Vertical v1 note rejected in its §9. The handoff happens by reference at one boundary, not by projection.

## 8. Intake: the operator and Shuri, and who scopes

**ip-man scopes.** Scoping turns an ask into a level, a breakdown and acceptance criteria. That is my charter's job. Helio's charter already assumes it: "you select and sequence among work already scoped against criteria ip-man wrote" `[measured: helio-gracie.md, the pace-setting paragraph under limit 8]`.

Rejected candidates:
- **helio-gracie:** his limit 2 forbids him from writing design or done criteria.
- **jigoro-kano:** governance is his lane, not product decomposition.
- **The requester scoping its own ask:** this removes the second view that the Document · Discuss · Decide law exists to provide. For Sensei, it would also add supervision he has said he wants less of `[reported-by session memory]`.

**One path for both sources; only the provenance differs.**
1. **File.** The session holding the ask files a Request with `level: unscoped`, `to: venom`, `for: ip-man` and `owner: venom`.
   - **From Sensei:** `origin: operator`, with his words quoted as proof (TSD §3a, tier 1). If he asks on another host, that host's agent files to venom the same way.
   - **From Shuri:** `origin: agent`, with her ask extracted from her deliverable using save_verbatim.py.
     - Her "Requirements", "Dependencies" and "Open decisions for Sensei" sections already fit `[measured: shuri.md]`.
     - The session that dispatched her files it. This is the same through-the-session hand-off already decided for Shuri → MultipleMan on 2026-09-13 `[reported-by session memory]`.
     - Her agent file does not change, and she gains no `Agent` tool.
2. **Scope.** The session sees the ask in its normal `/open?host=venom` check (or at once, if it filed the ask itself) and dispatches ip-man. The scoping note states:
   - the level: story, feature or epic;
   - the parent, if the ask joins existing work;
   - the proposed children, each with acceptance criteria and a lane;
   - any open questions.

   The session posts the note (extracted with save_verbatim.py) as a WORKING event on the same thread. That event sets `level:`, plus `parent:`, `project:` and `repo:` where they apply.
3. **Confirm.** Helio's GATEWAY puts the scoping to Sensei as one yes or no, and his answer is transcribed as an `origin: operator` event. For Shuri's asks, this is the point where an agent's ask becomes initiated work: "The operator's job is to initiate work" (D17 B1) `[measured]`.
4. **File the children, then pace.** The session files the Features and Stories with `parent:`. Helio's `Next:` picks which Story starts, and each Story then runs as a normal Dojo job.

Scoping starts immediately. Only the filing of children waits for Sensei.

**Why the ask's thread becomes the Epic instead of being closed.** Closing Sensei's ask at scoping would show it as CLOSED before anything is built, which is the opposite of visible. Keeping one thread from ask to delivery also gives Vertical one stable reference. The level change uses G3's existing "on change" behaviour.

**The DoR is a scoping checklist: a report, not a gate (D1, D43).** A Story is ready when:
- its parent is a Feature;
- it has `acceptance: yes` with criteria;
- it has a lane in `for:`;
- its Epic carries Sensei's confirmation.

The projector checks the first three.

**The Story lifecycle, mapped onto the Dojo's existing gates (no new cadence):**

| State | When it is set |
|---|---|
| OPEN | filed after Sensei confirms the scoping |
| WORKING | the work order is cut and the lane dispatched; `next:` is updated at each Helio CHECKPOINT |
| BLOCKED | only for a block Helio confirms as REAL (his cited (a) to (f)), including a missing capability posted as a WANT |
| RESOLVED | QA has passed and Helio's final CHECKPOINT has run; the evidence is the commit SHA plus the QA output (D37) |
| CLOSED | Sensei's yes on the GATEWAY is transcribed, with the six-part closing ceremony (TSD §3a) |

Epics and Features close the same way, against their own acceptance criteria, once all their children are finished.

**Owners under D17** (named here, because nothing else names them):
- **venom** owns Epics, Features and Stories, as the session that files and closes on the Dojo's behalf.
- **The acting specialist** goes in `for:`. Delegation never moves accountability (D17 B4, C2).
- **helio-gracie** cannot own an item: his limit 4 says "you file nothing".
- **ip-man** cannot own one either, because I never declare work shipped.
- **`next:`** on Dojo items is the session's transcription of Helio's latest `Next:`.

## 9. The trial: the smallest first slice, and what follows

There are two tracks. Both run on venom only, and nobody else in the fleet has to act.

**Track 1: the convention and intake.** This needs no code and can start the day Sensei says go.
1. Record his go on a venom Bulletin as a mechanism **on trial**, following D40's precedent. Label it an operator-approved trial convention, not doctrine (D3).
2. Seed the tracker with this tracker as its first Epic, so it tracks itself, plus one live project that Helio picks (he sets the pace).
3. Run intake once from each source, using real asks: the next project ask from Sensei and the next from Shuri. If no ask from Shuri arrives during the trial, report that rather than manufacture one.

**Track 2: the projector CLI.** This runs as a normal Dojo job after his go.
- ronda-rousey writes fixture boards and tests first. These include ledger-replay tests for the groupings (§6) and one test that pins the duplicate-slug behaviour from §3.
- bruce-lee builds `tracker/` in the townsquare repo: standard library only, using the canonical `parse_filename`, read-only.
- jackie-chan reviews the derivation.

**What the trial must answer, in Sensei's words:**
1. Can he see "ongoing work, status, repos, and next steps" for each project on one dashboard, without a session rebuilding it?
2. Do the filed items carry the fields correctly? The projector's flags show this as a report, with no threshold.
3. Did one real ask from each source become confirmed, scoped Stories?

**The trial ends early** if a question comes up that header-only fields cannot answer. Two examples: needing the hierarchy in filenames, or needing other hosts to file tracker items.

**After the trial, each step gets its own gate:**
- jigoro-kano drafts the doctrine amendment for Sensei to adopt: the TSD §2 header fields, plus notes for §6 and §7, including claimers carrying `parent:` under §7b.
- The Viewer's "Projects" page gets its own design note:
  - chuck-norris: the page.
  - francis-ngannou: the NAS job and its volume.
  - gsp: reusing a read-only Drive credential (D26 keeps the Crier's credential read-only).
  - ronda-rousey: QA.

## 10. Decisions for Sensei, in order (Helio queues them one at a time)

1. **Architecture: option C.** It keeps one authority, changes nothing that already exists, and can be trialled now.
2. **The trial:** go or no-go on §9, both tracks.
3. **Intake:** ip-man scopes, and Sensei gives one yes per scoping before any children are filed. For Shuri's asks, that yes is what initiates the work.
4. **Vertical:** the tracker is Vertical's external intake gateway. The entry field inside Vertical is a later, separate decision.

## 11. What I ask of jigoro-kano and helio-gracie

**jigoro-kano** is a co-recommender, per Sensei's request. Please rule or recommend on each of these:
- **K1. Vehicle.** Can the five fields run as a trial convention, on D40's "on trial" precedent and recorded on a venom Bulletin, with the TSD §2 amendment drafted only after the trial? Or does even the trial need a numbered ruling? Please also check the Bulletin's wording against D3.
- **K2. Board and ownership.** Epics, Features and Stories are Requests (TSD §6; D17 B8; D22). venom owns them, specialists go in `for:`, and helio-gracie and ip-man are excluded as owners by their own agent files. Is transcribing Helio's `Next:` into `next:` consistent with his limit 4, and with the rule that "`Next:` orders crew dispatch only"?
- **K3. One thread from intake to Epic.** This uses G3's "on change" behaviour. The alternative is closing the intake thread and continuing on a new one (D19 `continues`). Please also confirm my D44 reading in §6: the groupings are a view, not relevance buckets.
- **K4. TSD §7b.** When a claimer carries `parent:` on the Request it opens, is that an addition to §7b or a reinterpretation of it?
- **K5. Attribution.** When a session files Shuri's ask, does D17 A2's `name:` mean the agent that wrote the file, or the agent whose words it carries? I deliberately add no requester field, because D17 A7 removed `from:`.
- **K6. DoR and confirmation.** Is the DoR a scoping checklist in my design, or a rule that needs Sensei's approval under D3? Does one yes per scoping fit D17 B1, and Request Handling §1 as helio-gracie.md cites it?
- **K7. Name collisions** with any field vocabulary, in force or in draft.
  - I could not find D16's Field-and-Object Dictionary draft under `N3rd0m\`.
  - A content search of the board for the five keys found no matches, but that search may have been incomplete on this mount.
  - The projector's first full run is the complete check.

**helio-gracie:** Sensei asked for your implementation input. Please give it in the GATEWAY:
- Is §9 the nearest shippable deliverable, or is something smaller shippable?
- Which live project should seed the trial?
- Does updating `next:` at your CHECKPOINTs fit your cadence without lengthening sessions?
- Product lens: does anything here go beyond what Sensei asked for? The Bulletin `parent:` in §5 is where I would look first.

```
WORK ORDER — TownSquare project tracker (recommendation only; no build commissioned)
- Document: the session saves this note with save_verbatim.py, printing its SHA-256, to
  C:\Repo\townsquare\docs\townsquare-project-tracker-design.md (branch `internal`)
  — reviewed by jigoro-kano before any Implement line
- Coordinate: jigoro-kano reviews first (Peer review line). helio-gracie then CHECKPOINTs the
  pair — this note and kano's review — and runs the final CHECKPOINT + GATEWAY before Sensei
  sees either. There is no GAME PLAN on this job because nothing is built; his implementation
  input (§11) goes in the GATEWAY. If kano raises concerns, the session resumes ip-man once with
  them (extracted with save_verbatim.py) and saves the answer as a -v2 file beside this one;
  Helio then checks the pair.
- Implement: none yet — pending Sensei's decision. The §9 lanes (ronda-rousey tests first,
  then bruce-lee, then jackie-chan review) are a proposal, dispatched only after his go.
- Peer review: jigoro-kano — K1–K7 in §11. As co-recommender, his own recommendation reaches
  Sensei in his words.
- QA: none — this job changes no code.
- Done when:
  (1) the note is saved at its path with its SHA-256;
  (2) kano's review has returned, and each concern is either answered by ip-man or reaches
      Sensei as dissent in kano's words;
  (3) Helio's GATEWAY has put §10's decisions to Sensei one at a time;
  (4) the package shows, for each of "ongoing work, status, repos, and next steps", the data
      and where it is seen (§6), plus the E/F/S fields and parent naming (§4), the tie to
      "the seeking and wanted categories" (§5), the Vertical relationship (§7), and the intake
      path for "the operator and Shuri" (§8).
- Watch for:
  (a) scope creep into the Registrar (no header storage; it is pre-live) or into the Crier
      (TSD §9, rule 13);
  (b) any filename token for the hierarchy: it reaches four shared parser consumers plus
      Vertical's vendored copy, and the token is lost until every consumer is upgraded
      (the §3 command reproduces this);
  (c) Vertical Stage 2 stays untouched; its entry field is a later, separate decision;
  (d) projector traps, for bruce-lee and ronda-rousey:
      - read Archive/ too: TSD §8 moves CLOSED threads there after 60 days, and D22 will
        archive bulletins on age once its timer exists;
      - do not call check_header: it has a known zero-padding defect
        (registrar/importer/legacy.py:199), and D24's `to: all` on Seeking posts also trips
        its header-only rule;
      - read headers leniently: read_header raises on duplicate keys, and indented
        continuation lines should be skipped;
      - treat a collided thread id as an ambiguous parent;
      - measure the first full read of the Drive mount (a ripgrep over it reportedly timed out
        at 20 s — reported-by session memory), and cache by path, since files never change;
  (e) `next:` going stale: update it at Helio's CHECKPOINTs, show last activity, and set no
      threshold (D42);
  (f) D3: the trial Bulletin must read as an operator-approved trial convention, and the DoR
      stays a report (D43);
  (g) Shuri is an intake source, not a dependency: her agent file does not change;
  (h) venom's /open queue will carry long-lived Epic and Feature rows; that is expected, not
      a defect.
```