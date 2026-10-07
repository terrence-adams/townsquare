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

from registrar_client import BASE_URL, CANARY_IDENTITY, NATIVE_MVP_PROFILE, VIEWER_PROFILE, health

st.set_page_config(
    page_title="[CANARY] Town Registrar viewer",
    page_icon=":material/local_library:",
    layout="wide",
)

st.markdown(
    """<div role="alert" style="background:#7f1d1d;color:#fff;border:3px solid #facc15;
    padding:0.75rem 1rem;font-size:1.15rem;font-weight:800;text-align:center;">
    CANARY — NON-AUTHORITATIVE — TS-CANARY-NAS1-20261007-A</div>""",
    unsafe_allow_html=True,
)

page = st.navigation(
    [
        st.Page(
            "app_pages/native_ledger.py",
            title="Native ledger",
            icon=":material/verified:",
            default=True,
        ),
    ],
    position="top",
)

# Connection state is app-level, not page-level: it is the same answer on every
# page and it is the first thing worth knowing when a panel looks wrong.
with st.sidebar:
    st.subheader("CANARY — NON-AUTHORITATIVE")
    st.caption("TS-CANARY-NAS1-20261007-A")
    for name,value in CANARY_IDENTITY.as_dict().items():
        st.caption(f"{name}: {value}")
    if VIEWER_PROFILE != NATIVE_MVP_PROFILE:
        st.error("Unsupported Viewer profile. This release is native-ledger-only.")
        st.stop()
    status = health()
    if status["ok"]:
        st.badge("Ready", icon=":material/check_circle:", color="green")
        st.caption(f"Schema version {status['detail'].get('schema_version', '?')}")
    else:
        st.error(f"Blocking canary identity/readiness error: {status['detail']}")
        st.stop()
    st.caption(BASE_URL)

    if st.button("Refresh", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(
        "Read-only native MVP. This app calls only native-ledger GET endpoints "
        "with `status:read`, `post:read`, and `notice:read`; it has no Drive authority, legacy "
        "historical browser, write path, wake control, or direct database access."
    )

st.title(page.title, icon=page.icon)
page.run()
