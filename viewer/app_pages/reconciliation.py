#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Reconciliation — the four `GET /v1/reconciliation?status=...` views."""
import streamlit as st

import views
from registrar_client import RegistrarError, reconciliation, reconciliation_rows

# Each panel needs a plain-language answer to "so what?", because the endpoint
# name alone does not say whether a non-zero count is a problem or a fact.
PANELS = {
    "missing-publication": (
        ":material/hourglass_empty:",
        "Posts still in `registration_state='reserved'` — a number was "
        "allocated but publication was never finalised. Expected transiently "
        "while a writer is mid-flight; a persistent row here is an abandoned "
        "reservation that should be abandoned explicitly so the number is "
        "burned on the record rather than left ambiguous.",
    ),
    "legacy-collision": (
        ":material/call_split:",
        "Imported posts that share a `(root_uid, legacy_seq)` with another "
        "imported post. These are genuine ambiguities in the pre-Registrar "
        "ledger, surfaced rather than silently resolved — the import refuses "
        "to guess which one owns the sequence number.",
    ),
    "unresolved-responsibility": (
        ":material/help:",
        "Import observations whose warnings include "
        "`unresolved_responsibility`: the importer could not determine who is "
        "responsible for the post from the file alone. This is the class "
        "jigoro-kano ruled on — the record keeps the unknown as an explicit "
        "warning instead of inventing an owner.",
    ),
    "artifacts": (
        ":material/attachment:",
        "Every row in `artifacts` — the signature files observed alongside "
        "posts. `verification_state` is `observed` until an independent "
        "verifier with read-only Drive credentials confirms it; nothing here "
        "is proof of a valid signature by itself.",
    ),
}

st.caption(
    "Operational visibility into what the Registrar knows is unfinished, "
    "ambiguous, or merely observed. All four are queries, not actions — "
    "resolving any of them happens elsewhere, with approval."
)

tabs = st.tabs(list(PANELS), on_change="rerun")
for tab, (status, (icon, blurb)) in zip(tabs, PANELS.items()):
    # Tab bodies are only computed when their tab is open: four reconciliation
    # queries on every rerun would be three wasted round trips.
    if not tab.open:
        continue
    with tab:
        st.markdown(f"### {icon} {status}")
        st.caption(blurb)
        try:
            rows = reconciliation_rows(reconciliation(status))
        except RegistrarError as exc:
            views.error(exc)
            continue

        st.metric("Rows", len(rows), border=True, width="content")
        if not rows:
            st.success("Nothing outstanding in this view.", icon=":material/check:")
            continue

        if status in ("missing-publication", "legacy-collision"):
            selected = views.posts_table(rows, key=f"recon_{status}", height=420)
            if selected:
                views.record(selected, title="Selected post")
        else:
            st.dataframe(views.frame(rows, columns=()), hide_index=True, height=420)
        views.download(rows, f"reconciliation-{status}.csv", key=f"recon_csv_{status}")
