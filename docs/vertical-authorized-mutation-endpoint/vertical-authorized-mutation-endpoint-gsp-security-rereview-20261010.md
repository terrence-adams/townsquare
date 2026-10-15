# GSP focused security rereview — Vertical authorized mutation endpoint MVP

**Verdict: APPROVAL-READY**  
Date: 2026-10-10  
Reviewer: GSP  
Scope: correction of SEC-001 and specified regressions only. No code, ledger, credential, deployment, ACL, or other system state was changed.

## Hash-pinned inputs verified

| Artifact | SHA-256 |
| --- | --- |
| `vertical-authorized-mutation-endpoint-mvp-design-20261010.md` | `f95fbbf39306cf334f7dd53b40ce821d8366540c2035980c6d178e29cff077f8` |
| `vertical-authorized-mutation-endpoint-draft-work-items-20261010.md` | `41f8e279e2513c55453a12a0decab4f652da35f1a6e5bccca454a243098efe36` |
| `vertical-authorized-mutation-endpoint-work-order-20261010.md` | `ce3359108f532b9803ca6bdc1915f90747c29ffb9bb2cb9c4556280f8078bf7d` |

## Rereview result

SEC-001 is remediated.

- `project` is server-resolved and forbidden in every caller location, with `422 CALLER_PROJECT_FORBIDDEN`; the caller no longer must both provide and omit it.
- `authority_ref` has one exact three-field top-level form. Alternate or nested forms are forbidden with `422 AUTHORITY_REF_DUPLICATE`.
- The typed payload is an exact eight-field schema with explicit null/empty-map rules. The design pins semantic-payload, canonical-request, idempotency-key, and permit-binding hashes, and requires equal canonical request bytes and all four hashes at issuance and execution.
- Authority coverage is validated at issuance and revalidated immediately before append. Exact committed replay lookup precedes mutable-state checks; non-exact reuse fails without a write.
- S2 and S4 now require zero-write fixtures for caller project, duplicate/alternate authority, payload/hash mismatches, authority coverage changes, and permit lifecycle behavior.
- Eddie/Venom remains limited to operator decision/receipt relay. Logan/Wolverine remains a facilitator without self-approval, sole review, endpoint authority, administration, or credentials. Iron Curtain remains reference-only.

No regression against the bounded MVP acceptance boundary was found. The correction is a contract/test clarification, not production-hardening or a new persistence, IAM, ACL, or deployment requirement.

## Release condition

The design package is security **APPROVAL-READY** for the documented Dojo review/intake gate. This is a design verdict only; implementation, live ledger intake, credentials, deployment, cutover, and consumer transactions still require their separately documented gates and approvals.

Model/cost: current focused review; measured token or currency cost unavailable.
