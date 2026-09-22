#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Aliases — resolve a human-written name to the record(s) it could mean."""
import streamlit as st

import views
from registrar_client import RegistrarError, get_aliases, get_post, get_root

st.caption(
    "`GET /v1/aliases/{alias}` returns every candidate, not a best guess. More "
    "than one match is reported as ambiguous rather than silently resolved — "
    "an alias that maps to two records is a fact about the ledger, and picking "
    "one for the caller would hide it."
)

alias = st.text_input(
    "Alias",
    placeholder="a legacy name, filename fragment, or shorthand",
    key="alias",
    icon=":material/search:",
    bind="query-params",
).strip()

if not alias:
    st.info("Enter an alias to resolve.", icon=":material/search:")
    st.stop()

try:
    payload = get_aliases(alias)
except RegistrarError as exc:
    views.error(exc)
    st.stop()

matches = payload.get("matches", [])
if payload.get("ambiguous"):
    st.warning(
        f"Ambiguous — `{alias}` resolves to {len(matches)} records.",
        icon=":material/warning:",
    )
elif matches:
    st.success(f"`{alias}` resolves to one record.", icon=":material/check:")
else:
    st.info(f"No record is registered under `{alias}`.", icon=":material/search_off:")
    st.stop()

st.dataframe(views.frame(matches, columns=()), hide_index=True)

# Resolving each match costs one extra GET, so it is opt-in per match rather
# than automatic on a page that may be showing an ambiguous fan-out.
for match in matches:
    kind, uid = match.get("resource_type"), match.get("resource_uid")
    box = st.expander(f"{kind} · {uid}", icon=":material/description:", on_change="rerun")
    if not box.open:
        continue
    with box:
        try:
            if kind == "post":
                views.record(get_post(uid))
            elif kind == "root":
                # A root alias is written as (thread_id, 'root', root_uid), so
                # the alias itself is the thread ID. `GET /v1/roots/{id}` keys
                # on thread_id, not root_uid — look it up by the alias.
                views.record(get_root(alias))
            else:
                st.caption(f"No read endpoint covers resource_type `{kind}`.")
        except RegistrarError as exc:
            views.error(exc)
