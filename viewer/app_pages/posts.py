#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Posts — browsable, filterable table over `GET /v1/posts`."""
import streamlit as st

import views
from registrar_client import (
    ASSIGNMENT_ROLES,
    REGISTRATION_STATES,
    RegistrarError,
    sweep_posts,
)

ANY = "any"

# The filter set the API actually supports. Anything not in this list has to be
# applied client-side after the sweep, and is labelled as such.
with st.container(border=True):
    st.markdown("**Filters** — applied by the Registrar, not in the browser")
    with st.container(horizontal=True):
        registration_state = st.selectbox(
            "Registration state",
            (ANY, *REGISTRATION_STATES),
            key="posts_registration_state",
            bind="query-params",
        )
        board = st.text_input(
            "Board",
            placeholder="e.g. open",
            key="posts_board",
            bind="query-params",
        )
        state = st.text_input(
            "State",
            placeholder="e.g. decided",
            key="posts_state",
            bind="query-params",
        )
    with st.container(horizontal=True):
        root = st.text_input(
            "Thread ID",
            placeholder="root thread_id",
            key="posts_root",
            bind="query-params",
        )
        assigned_to = st.text_input(
            "Assigned to",
            placeholder="agent id",
            key="posts_assigned_to",
            bind="query-params",
        )
        role = st.selectbox(
            "Role",
            (ANY, *ASSIGNMENT_ROLES),
            key="posts_role",
            help="Only meaningful together with an agent id.",
            bind="query-params",
        )

table_slot = st.container()
detail_slot = st.container()

with table_slot.skeleton(height=560):
    try:
        rows, saturated = sweep_posts(
            assigned_to=assigned_to or None,
            role=None if role == ANY else role,
            state=state or None,
            board=board or None,
            registration_state=None if registration_state == ANY else registration_state,
            root=root or None,
        )
    except RegistrarError as exc:
        rows, saturated = [], []
        views.error(exc)

    with table_slot.container():
        st.caption(
            f"{len(rows)} post(s). Ordered by (created_at, post_uid), the "
            "Registrar's own immutable sort key. Select a row for its full record."
        )
        selected = views.posts_table(rows, key="posts_table")
        views.truncation_warning(saturated)
        views.download(rows, "registrar-posts.csv", key="posts_csv")

with detail_slot:
    if selected:
        with st.container(border=True):
            st.subheader(f"{selected.get('thread_id')} · post {selected.get('post_no')}")
            if selected.get("drive_url"):
                st.link_button(
                    "Open in Drive",
                    selected["drive_url"],
                    icon=":material/open_in_new:",
                )
            views.record(selected)
