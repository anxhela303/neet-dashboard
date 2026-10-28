import streamlit as st

from utils import (load_data, sidebar_filters, year_table, benchmark, render_kpis, europe_map,
                   handle_map_click, country_selector, get_selected, tier, title_block)

st.set_page_config(page_title="Map - NEET", layout="wide")

df = load_data()
f = sidebar_filters(df)
t = year_table(df, f)
if t.empty:
    st.warning("No data for this combination of filters.")
    st.stop()

title_block("Interactive Europe map", f)
st.markdown("**Click any country.** Everything updates automatically.  "
            "🟢 Low · 🟡 Medium · 🔴 High")

country_selector(t, container=st.sidebar)          # before the map so it can reset stale clicks
render_kpis(t, f, benchmark(df, f))

map_col, info_col = st.columns([3, 1])
with map_col:
    event = europe_map(t, f, get_selected(t["country"]))
handle_map_click(event, t)
sel = get_selected(t["country"])

with info_col:
    if sel is None:
        st.info("Click a country on the map to see its details here.")
    else:
        row = t[t["country"] == sel].iloc[0]
        rank = int(t.index[t["country"] == sel][0]) + 1
        eu = benchmark(df, f)
        st.subheader(sel)
        st.metric("Value", f"{row['value']:.1f}%")
        st.metric("Rank (1 = highest)", f"{rank} / {len(t)}")
        st.metric("Level", tier(row["value"], t))
        if eu == eu:
            st.metric("Difference vs EU27", f"{row['value'] - eu:+.1f} pp", delta_color="off")
        if "u" in row["flag"]:
            st.warning("Eurostat flags this value as low reliability.")

        by_sex = df[(df["country"] == sel) & (df["status"] == f["status"]) & (df["age"] == f["age"])
                    & (df["year"] == f["year"]) & (df["sex"] != "Total")]
        if len(by_sex) == 2:
            fm = by_sex.set_index("sex")["value"]
            st.caption(f"Women {fm['Females']:.1f}% · Men {fm['Males']:.1f}% "
                       f"(gap {fm['Females'] - fm['Males']:+.1f} pp)")
