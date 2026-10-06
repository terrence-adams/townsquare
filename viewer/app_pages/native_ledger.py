#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Read-only discovery and history for authoritative native ledger events."""
from __future__ import annotations

import json

import streamlit as st

import views
from registrar_client import RegistrarError, native_discovery, native_thread


st.caption(
    "Native events have a canonical envelope and verified stored content. "
    "Legacy imports remain historical metadata and are not relabeled here."
)
st.info(
    "A context receipt proves retrieval, currentness, and acknowledgement of "
    "the required context. It does not prove comprehension.",
    icon=":material/info:",
)

try:
    discovery = native_discovery()
except RegistrarError as exc:
    views.error(exc)
    st.stop()

open_work = list(discovery.get("open_work") or [])
history = list(discovery.get("history") or [])
boards = dict(discovery.get("boards") or {})
projects = dict(discovery.get("projects") or {})
registry = dict(discovery.get("registry") or {})
findings = list(discovery.get("findings") or [])

with st.container(border=True):
    st.subheader("Ledger at a glance")
    with st.container(horizontal=True):
        st.metric("Native threads", len(history), border=True)
        st.metric("Open work", len(open_work), border=True)
        st.metric("Boards", len(boards), border=True)
        st.metric("Projects", len(projects), border=True)

st.subheader("Open work")
st.caption("Current native state, excluding logically archived and closed threads.")
if open_work:
    st.dataframe(views.frame(open_work, columns=()), hide_index=True, width="stretch")
else:
    st.info("No open native work is currently projected.", icon=":material/inbox:")

left, right = st.columns(2)
with left:
    st.subheader("Boards")
    if boards:
        rows = [{"board": name, "thread_count": len(set(ids))} for name, ids in boards.items()]
        st.dataframe(views.frame(rows, columns=()), hide_index=True, width="stretch")
    else:
        st.info("No board projection is available.")
with right:
    st.subheader("Projects")
    if projects:
        rows = [{"project": name, "record_count": len(records)} for name, records in projects.items()]
        st.dataframe(views.frame(rows, columns=()), hide_index=True, width="stretch")
        with st.expander("Project context and provenance"):
            st.json(projects)
    else:
        st.info("No project hierarchy is available.")

st.subheader("Dependency and registry health")
if str(registry.get("status", "UNKNOWN")) == "OK":
    st.success("Registry projection is available.", icon=":material/check_circle:")
    agents = list(registry.get("agents") or [])
    if agents:
        st.dataframe(views.frame(agents, columns=()), hide_index=True, width="stretch")
else:
    st.warning(
        "Registry projection is degraded or unavailable. Native ledger history "
        "remains readable; this page does not infer missing registry data.",
        icon=":material/warning:",
    )
if findings:
    st.dataframe(views.frame(findings, columns=()), hide_index=True, width="stretch")

st.subheader("Thread history and provenance")
thread_ids = [str(row.get("thread_id")) for row in history if row.get("thread_id")]
chosen = st.selectbox(
    "Native thread", thread_ids, index=None, placeholder="Select a native thread", key="native_thread_id"
)
if not chosen:
    st.info("Select a thread to inspect its immutable event chain and content.", icon=":material/search:")
    st.stop()

try:
    thread = native_thread(chosen)
except RegistrarError as exc:
    views.error(exc)
    st.stop()

if thread.get("archived"):
    st.warning(
        "This thread is logically archived. It is visible for historical review; "
        "the viewer cannot alter archive state.",
        icon=":material/archive:",
    )

for event in thread.get("events") or []:
    ordinal = event.get("thread_ordinal", "?")
    label = f"#{ordinal} · {event.get('kind', 'event')} · {event.get('state', 'unknown')}"
    with st.expander(label, expanded=ordinal == 0):
        envelope = {key: value for key, value in event.items() if key not in {"content", "metadata_json"}}
        views.record(envelope, title="Canonical envelope and provenance")
        metadata = event.get("metadata_json")
        if metadata:
            try:
                st.json(json.loads(str(metadata)))
            except (TypeError, ValueError):
                views.inert_text(metadata, title="Metadata (unparseable JSON)")
        views.inert_text(event.get("content"), title="Authored content (rendered as plain text)")
        st.caption(
            "Notice intents and delivery attempts are immutable operational records, "
            "but this stable read model does not expose their row-level details. "
            "No delivery outcome is inferred here."
        )
