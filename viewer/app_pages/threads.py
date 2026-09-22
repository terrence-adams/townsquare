#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Threads — a root record plus the posts that hang off it."""
import streamlit as st

import views
from registrar_client import RegistrarError, get_root, list_posts, sweep_posts

st.caption(
    "A thread is one `roots` row and every `posts` row sharing its `root_uid`. "
    "Numbers are monotonic but not contiguous: abandoned and expired "
    "reservations burn their post number and it is never recycled, so a gap in "
    "the sequence is expected, not a missing record."
)

# The read API has no "list roots" endpoint, so the picker is built from the
# thread IDs the post sweep already returned (that query is cached and usually
# warm from the Posts page). Free text stays available for anything the sweep
# could not see.
try:
    rows, saturated = sweep_posts()
    known = sorted({r["thread_id"] for r in rows if r.get("thread_id")}, reverse=True)
except RegistrarError as exc:
    known, saturated = [], []
    views.error(exc)

with st.container(border=True):
    with st.container(horizontal=True):
        picked = st.selectbox(
            "Thread",
            known,
            index=None,
            placeholder="Search a thread ID",
            key="thread_picked",
        )
        typed = st.text_input(
            "Or enter a thread ID",
            placeholder="exact thread_id",
            key="thread_id",
            bind="query-params",
        )
    if saturated:
        st.caption(
            f"{len(known)} thread(s) discovered by sweep; the list may be short "
            "of the full set — see the Posts page for which partitions truncated."
        )

thread_id = (typed or picked or "").strip()
if not thread_id:
    st.info("Pick or enter a thread ID.", icon=":material/search:")
    st.stop()

root_slot, posts_slot = st.container(), st.container()

with root_slot.skeleton(height=320):
    try:
        root = get_root(thread_id)
    except RegistrarError as exc:
        root = None
        views.error(exc)
    if root:
        with root_slot.container(border=True):
            st.subheader(thread_id)
            with st.container(horizontal=True):
                st.metric("Status", str(root.get("status", "—")), border=True)
                st.metric("Namespace", str(root.get("namespace", "—")), border=True)
                st.metric("Next post no.", root.get("next_post_no", "—"), border=True)
            views.record(root, title="Root record")

with posts_slot.skeleton(height=420):
    try:
        # `root` filters on roots.thread_id server-side; a single thread is well
        # under the 200-row cap, so no sweep is needed here.
        thread_posts = list_posts(root=thread_id)
    except RegistrarError as exc:
        thread_posts = []
        views.error(exc)
    with posts_slot.container(border=True):
        st.markdown(f"**Posts in this thread** — {len(thread_posts)}")
        selected = views.posts_table(thread_posts, key="thread_posts", height=360)
        views.download(thread_posts, f"{thread_id}-posts.csv", key="thread_csv")
        if selected:
            views.record(selected, title=f"Post {selected.get('post_no')}")
