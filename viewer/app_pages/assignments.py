#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Assignments — what one agent is on the hook for."""
import streamlit as st

import views
from registrar_client import RegistrarError, get_assignments, sweep_posts

st.caption(
    "`GET /v1/assignments/{agent_id}` lists the post/role pairs bound to an "
    "agent. A post can carry several roles for the same agent; `responsible` "
    "is the one publication is gated on."
)

# Agent IDs come from the swept corpus (author_agent), so the picker offers
# names that actually exist rather than an empty box. Free text still wins.
try:
    rows, _ = sweep_posts()
    known = sorted({r["author_agent"] for r in rows if r.get("author_agent")})
except RegistrarError as exc:
    known = []
    views.error(exc)

with st.container(border=True):
    with st.container(horizontal=True):
        picked = st.selectbox(
            "Agent",
            known,
            index=None,
            placeholder="Search an agent id",
            key="assignment_picked",
        )
        typed = st.text_input(
            "Or enter an agent id",
            placeholder="exact agent_id",
            key="agent_id",
            bind="query-params",
        )
    active = st.segmented_control(
        "Assignments",
        ["active", "inactive"],
        default="active",
        key="assignment_active",
    )

agent_id = (typed or picked or "").strip()
if not agent_id:
    st.info("Pick or enter an agent id.", icon=":material/search:")
    st.stop()

try:
    assignments = get_assignments(agent_id, active=(active != "inactive"))
except RegistrarError as exc:
    views.error(exc)
    st.stop()

if not assignments:
    st.info(
        f"No {active or 'active'} assignments for `{agent_id}`.",
        icon=":material/search_off:",
    )
    st.stop()

with st.container(horizontal=True):
    st.metric("Assignments", len(assignments), border=True)
    st.metric(
        "Responsible for",
        sum(1 for a in assignments if a.get("role") == "responsible"),
        border=True,
    )

st.dataframe(
    views.frame(assignments, columns=("post_uid", "role", "active")),
    hide_index=True,
)
views.download(assignments, f"{agent_id}-assignments.csv", key="assignments_csv")

# The posts themselves, server-filtered. This is the same data from the other
# direction and it is what makes the page useful: role names alone do not say
# which thread is waiting on this agent.
st.subheader("Posts assigned to this agent")
try:
    assigned, saturated = sweep_posts(assigned_to=agent_id)
except RegistrarError as exc:
    assigned, saturated = [], []
    views.error(exc)

selected = views.posts_table(assigned, key="assignment_posts", height=400)
views.truncation_warning(saturated)
if selected:
    views.record(selected, title=f"Post {selected.get('post_no')}")
