#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Overview — Registrar health and headline corpus counts."""
import streamlit as st

import views
from registrar_client import (
    BASE_URL,
    RECONCILIATION_STATUSES,
    RegistrarError,
    health,
    live,
    reconciliation,
    reconciliation_rows,
    sweep_posts,
)

st.caption(
    "Everything below is read through the Registrar's API. The viewer holds no "
    "database handle and calls no write endpoint."
)

# ---------------------------------------------------------------- health
status = health()
with st.container(border=True):
    st.subheader("Service health")
    with st.container(horizontal=True):
        st.metric(
            "Readiness",
            "ready" if status["ok"] else "not ready",
            border=True,
            icon=":material/health_and_safety:",
        )
        st.metric(
            "Liveness",
            "live" if live() else "unreachable",
            border=True,
            icon=":material/monitor_heart:",
        )
        st.metric(
            "Schema version",
            str(status["detail"].get("schema_version", "—")) if status["ok"] else "—",
            border=True,
            icon=":material/schema:",
        )
    if status["ok"]:
        st.caption(
            f"`{BASE_URL}` — `/health/ready` passed, which means the Registrar's "
            "SQLite pragmas (foreign_keys, WAL, synchronous=FULL) are all as the "
            "design requires and the migration table answered."
        )
    else:
        st.error(str(status["detail"]), icon=":material/cloud_off:")
        st.caption(
            "`/health/ready` returns 503 when a pragma drifts, so a red badge "
            "here is a storage-integrity signal, not just a network one."
        )
        st.stop()

# ---------------------------------------------------------------- corpus
st.subheader("Corpus")
corpus_slot = st.container()
with corpus_slot.skeleton(height=320):
    try:
        rows, saturated = sweep_posts()
    except RegistrarError as exc:
        rows, saturated = [], []
        views.error(exc)

    threads = {r.get("thread_id") for r in rows if r.get("thread_id")}
    boards = {r.get("board") for r in rows if r.get("board")}
    legacy = sum(1 for r in rows if r.get("source") == "legacy_import")

    with corpus_slot.container(horizontal=True):
        st.metric("Posts", len(rows), border=True, icon=":material/description:")
        st.metric("Threads", len(threads), border=True, icon=":material/forum:")
        st.metric("Boards", len(boards), border=True, icon=":material/dashboard:")
        st.metric(
            "Legacy imports",
            legacy,
            border=True,
            icon=":material/inventory_2:",
            help="Posts with source=legacy_import.",
        )
    with corpus_slot.container(border=True):
        st.markdown("**Posts by registration state**")
        views.counts_chart(rows, "registration_state", "registration state")

views.truncation_warning(saturated)

# ---------------------------------------------------------------- reconciliation
st.subheader("Reconciliation")
st.caption("Counts only — the Reconciliation page has the rows behind each one.")
with st.container(horizontal=True):
    for name in RECONCILIATION_STATUSES:
        try:
            count = len(reconciliation_rows(reconciliation(name)))
            st.metric(name, count, border=True)
        except RegistrarError as exc:
            st.metric(name, "error", border=True, help=str(exc))
