import streamlit as st

from utils import (load_data, sidebar_filters, year_table, benchmark, render_kpis,
                   ranking_controls_and_table, ranking_chart, title_block)

st.set_page_config(page_title="NEET Dashboard", layout="wide")

df = load_data()
f = sidebar_filters(df)
t = year_table(df, f)

title_block("The real number of inactive NEET youth in Europe", f)
st.markdown(
    "**NEET** = young people *Not in Employment, Education or Training*. Headline figures often "
    "count only the unemployed; this dashboard focuses on the **inactive**: those **outside the "
    "labour force**, who are neither working nor looking for work. Use the sidebar to change "
    "indicator, age group, sex and year; use the pages on the left to explore."
)

if t.empty:
    st.warning("No data for this combination of filters.")
    st.stop()

render_kpis(t, f, benchmark(df, f))

st.divider()
st.subheader("Interactive ranking")
left, right = st.columns([1, 1])
with left:
    r = ranking_controls_and_table(t)
with right:
    if not r.empty:
        ranking_chart(r, t, asc=st.session_state.get("rank_order", "").startswith("Asc"))

st.caption("'low' = Eurostat flags the estimate as low reliability. "
           "Countries with no estimate for the chosen year are not shown.")
