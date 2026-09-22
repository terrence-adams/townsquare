#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""
Shared presentation helpers.

Pages stay as direct scripts; anything two pages both need to draw lives here.
Nothing in this module talks to the Registrar — it only shapes what
registrar_client.py already returned.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

import pandas as pd
import streamlit as st

from registrar_client import POST_COLUMNS, RegistrarError

POST_COLUMN_CONFIG = {
    "thread_id": st.column_config.TextColumn("Thread", pinned=True),
    "post_no": st.column_config.NumberColumn("No.", format="%d", width="small"),
    "legacy_seq": st.column_config.NumberColumn("Legacy seq", format="%d"),
    "registration_state": st.column_config.TextColumn("Registration"),
    "drive_url": st.column_config.LinkColumn("Drive", display_text="open"),
    "content_sha256": st.column_config.TextColumn("Content SHA-256"),
    "author_agent": st.column_config.TextColumn("Author"),
    "created_at": st.column_config.TextColumn("Created"),
}


def frame(rows: Iterable[Mapping[str, Any]], columns: Iterable[str] | None = None):
    """Rows to a DataFrame with a stable, readable column order.

    Unknown keys are appended rather than dropped, so a future migration that
    adds a column shows up here instead of disappearing silently.
    """
    data = pd.DataFrame(list(rows))
    if data.empty:
        return data
    order = POST_COLUMNS if columns is None else columns
    preferred = [c for c in order if c in data.columns]
    return data[preferred + [c for c in data.columns if c not in preferred]]


def posts_table(
    rows: list[Mapping[str, Any]], key: str, height: int | str = 520
) -> dict[str, Any] | None:
    """Render posts and return the selected row, or None.

    Single-row selection rather than a per-row button: the selection is the
    page's ongoing state (the detail panel below reflects it across reruns),
    which is exactly the case the dataframe selection API is for.
    """
    data = frame(rows)
    if data.empty:
        st.info("No posts match these filters.", icon=":material/filter_alt_off:")
        return None
    event = st.dataframe(
        data,
        key=key,
        hide_index=True,
        height=height,
        column_config=POST_COLUMN_CONFIG,
        on_select="rerun",
        selection_mode="single-row",
    )
    picked = event.selection.rows if event and event.selection else []
    return rows[picked[0]] if picked else None


def record(mapping: Mapping[str, Any], title: str | None = None) -> None:
    """A single record as a key/value list. Empty fields are kept and shown as
    an em dash, because "this column is NULL" is itself information here."""
    if title:
        st.markdown(f"**{title}**")
    st.table(
        {str(k): ("—" if v in (None, "") else str(v)) for k, v in mapping.items()},
        border="horizontal",
    )


def counts_chart(rows: list[Mapping[str, Any]], column: str, label: str) -> None:
    """Horizontal bar of row counts for one categorical column."""
    data = frame(rows)
    if data.empty or column not in data.columns:
        return
    tally = (
        data[column]
        .fillna("(unset)")
        .value_counts()
        .rename_axis(label)
        .reset_index(name="posts")
    )
    st.bar_chart(tally, x=label, y="posts", horizontal=True, height=max(160, 44 * len(tally)))


def truncation_warning(saturated: list[str]) -> None:
    """Say out loud when the API's 200-row ceiling hid rows from this view."""
    if not saturated:
        return
    st.warning(
        "Some rows are not shown. The Registrar's `GET /v1/posts` caps at 200 "
        "rows per call and implements no cursor, so these partitions came back "
        "full and may be incomplete: "
        + "; ".join(f"`{s}`" for s in saturated),
        icon=":material/warning:",
    )


def error(exc: RegistrarError) -> None:
    st.error(str(exc), icon=":material/cloud_off:")


def download(rows: list[Mapping[str, Any]], filename: str, key: str) -> None:
    data = frame(rows)
    if data.empty:
        return
    st.download_button(
        "Download CSV",
        data.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        icon=":material/download:",
        key=key,
    )
