#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""
Town Registrar viewer — entry point and navigation.

A read-only window onto the Registrar's read API. It holds no database
connection and calls no write endpoint; see registrar_client.py.
"""
import streamlit as st

from registrar_client import BASE_URL, health

st.set_page_config(
    page_title="Town Registrar viewer",
    page_icon=":material/local_library:",
    layout="wide",
)

page = st.navigation(
    [
        st.Page(
            "app_pages/overview.py",
            title="Overview",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page("app_pages/posts.py", title="Posts", icon=":material/table_rows:"),
        st.Page("app_pages/threads.py", title="Threads", icon=":material/forum:"),
        st.Page(
            "app_pages/reconciliation.py",
            title="Reconciliation",
            icon=":material/rule:",
        ),
        st.Page("app_pages/aliases.py", title="Aliases", icon=":material/link:"),
        st.Page(
            "app_pages/assignments.py",
            title="Assignments",
            icon=":material/assignment_ind:",
        ),
    ],
    position="top",
)

# Connection state is app-level, not page-level: it is the same answer on every
# page and it is the first thing worth knowing when a panel looks wrong.
with st.sidebar:
    st.subheader("Registrar")
    status = health()
    if status["ok"]:
        st.badge("Ready", icon=":material/check_circle:", color="green")
        st.caption(f"Schema version {status['detail'].get('schema_version', '?')}")
    else:
        st.badge("Not ready", icon=":material/error:", color="red")
        st.caption(str(status["detail"]))
    st.caption(BASE_URL)

    if st.button("Refresh", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(
        "Read-only view. This app calls only the Registrar's GET endpoints "
        "with a `post:read` credential — it has no write path and no direct "
        "database access."
    )

st.title(page.title, icon=page.icon)
page.run()
