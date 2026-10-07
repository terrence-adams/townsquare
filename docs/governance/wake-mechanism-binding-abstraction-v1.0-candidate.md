# Wake-mechanism binding abstraction v1.0 — candidate

**document_id:** `TS-WAKE-BINDING-ABSTRACTION-20261006-CANDIDATE`
**status:** CANDIDATE — NOT ACCEPTED — NOT ENABLED

## Contract

A compliant wake mechanism may alert an active agent or start a dormant agent because durable work exists. It receives only a pointer/opaque reference and delivery metadata. It cannot create, alter, accept, prioritize, assign, or authorize TownSquare work. The awakened agent retrieves current record and policy before acting. Loss, duplication, delay, delivery, or failure of the wake mechanism has no effect on authoritative work state.

## Required binding evidence

- declared trigger, recipient resolution, identity boundary, and least-privilege capability;
- pointer-only payload and secret-free audit record;
- duplicate, lost, delayed, malformed, unauthorized, and restart behavior;
- proof that delivery does not grant authority or bypass receipts;
- proof that the operator can stop/disable the mechanism without being gated;
- recovery/observability and a replacement/migration procedure.

An external implementation such as Revere may be evaluated against this contract, but is neither named by the Doctrine nor authoritative by deployment. Replacing it with another compliant mechanism requires binding review/acceptance, not a Doctrine amendment.
