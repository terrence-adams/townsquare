# Governance source snapshots and evidence gaps — 2026-10-07

**status:** REVIEW EVIDENCE — NOT AUTHORITY — NOT AN ADOPTION RECORD

## Candidate 6 exact byte identity

| Item | Immutable identity |
|---|---|
| Git commit | `084d236fa06084c94ce1eefc2fac194e8ecc8360` |
| Git blob | `f77dedd0239f2188737e41e7c4aa8accab9caac6` |
| raw blob SHA-256 | `93A511C3679A0C6DD6531CF52C91515C6F2EFC84B72EA2072B0B44F78C21EFA8` |
| raw blob bytes / line ending | 6,592 bytes / LF only |
| current working-byte SHA-256 | `93A511C3679A0C6DD6531CF52C91515C6F2EFC84B72EA2072B0B44F78C21EFA8` |
| reviewer pin | the raw blob identity and SHA-256 above |

## Available named source snapshots

| Source | Locator | Immutable revision | working-byte SHA-256 | Relationship / conflict treatment |
|---|---|---|---|---|
| Charter 2.0 Part C | `C:\Repo\Agentic\docs\charter-2.0-part-c.md` | Agentic commit `9a35d124449b1a7df7d3349def59b74296a37700`, blob `87a9128ab0f9e681d1a7925deaee0907d8e685a6` | `7E846C10DE2EC35201C805A5BD6087A7A1BF0EE5C9DBA595A43735EA81FFEF00` | external adopted charter; candidate 6 does not amend it. Its operator-override and recognition language is compatible in stated scope; a conflict is escalated, never silently ranked. |
| Charter 2.0 Part D | `C:\Repo\Agentic\docs\charter-2.0-part-d.md` | Agentic commit `9a35d124449b1a7df7d3349def59b74296a37700`, blob `1596a5b208a119b56b2b9e8c7bb80c13fe6563d8` | `A1A91037CD7A1FC2B36D93CF9CA3E8C1C411D9DAFB409678D4916925D23CB3B2` | external charter component; candidate 6 does not amend it. Any material overlap requires an operator-scoped adjudication. |

## Evidence gaps that block adoption review

| Required source | Search/result | Missing immutable facts | Consequence |
|---|---|---|---|
| Decisions register `BB-20260911-forge-001` (D1–D49, S1–S8) | No register snapshot/event corpus is present in this worktree or the searched local repositories. Secondary references are not substitutes. | canonical event content, immutable snapshot identity, sequence/watermark, exact digest, retrieval time | Per-decision map remains provisional; no adoption recommendation. |
| Agentic Operating Charter | No locally readable canonical artifact was found under the searched Agentic repository. Secondary mentions do not establish current text. | canonical locator, revision/digest, retrieval time, scope | Relationship/conflict mapping remains incomplete; no adoption recommendation. |
| Bedrock Doctrine | No locally readable canonical artifact was found under the searched repositories. | canonical locator, revision/digest, retrieval time, scope | Relationship/conflict mapping remains incomplete; no adoption recommendation. |

The stale-input check is mechanical: reject a claimed source snapshot if any of its identity, watermark, digest, or retrieval time is absent; if the live source has a later watermark; or if its recomputed digest differs. These gaps do not delete, supersede, or weaken any source; they prevent this candidate package from claiming its review evidence is complete.
