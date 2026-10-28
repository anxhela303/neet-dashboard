"""Shared data loading, filters and UI components for the NEET dashboard."""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
LOGO = ROOT / "assets" / "logo.png"

# green -> yellow -> red gradient used everywhere
GRADIENT = [[0.0, "#2ecc71"], [0.5, "#f1c40f"], [1.0, "#e74c3c"]]
SEXES = ["Total", "Females", "Males"]
MAIN_STATUS = "Inactive"          # "Persons outside the labour force"


# ----------------------------------------------------------------- data
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data.csv")
    df["flag"] = df["flag"].fillna("").astype(str)   # empty cells are read as NaN (float)
    return df


def countries_only(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["is_aggregate"]]


def slice_data(df, *, status=MAIN_STATUS, sex="Total", age="15-29", year=None) -> pd.DataFrame:
    """Filter the long table; year=None keeps every year."""
    out = df[(df["status"] == status) & (df["sex"] == sex) & (df["age"] == age)]
    if year is not None:
        out = out[out["year"] == year]
    return out


def year_table(df, f) -> pd.DataFrame:
    """One row per country for the selected filters (aggregates excluded)."""
    return (countries_only(slice_data(df, status=f["status"], sex=f["sex"], age=f["age"], year=f["year"]))
            .sort_values("value", ascending=False).reset_index(drop=True))


def benchmark(df, f, name="EU27"):
    row = slice_data(df, status=f["status"], sex=f["sex"], age=f["age"], year=f["year"])
    row = row[row["country"] == name]
    return float(row["value"].iloc[0]) if len(row) else np.nan


def compute_stats(t: pd.DataFrame) -> dict:
    v = t["value"]
    return {
        "highest": t.loc[v.idxmax()], "lowest": t.loc[v.idxmin()],
        "n": int(v.count()), "std": float(v.std(ddof=1)), "median": float(v.median()),
        "mean": float(v.mean()),
    }


# -------------------------------------------------------------- filters
def sidebar_filters(df: pd.DataFrame) -> dict:
    """Global filters, kept in session_state so every page stays in sync."""
    if LOGO.exists():
        st.sidebar.image(str(LOGO))
    st.sidebar.header("Filters")

    c = countries_only(df)
    status_opts = list(c["status"].unique())
    default_status = status_opts.index(MAIN_STATUS)
    status = st.sidebar.selectbox("Indicator", status_opts, index=default_status, key="f_status",
                                  help="'Inactive' = NEET persons outside the labour force "
                                       "(not working and not looking for work).")
    ages = sorted(c["age"].unique(), key=lambda a: int(a.split("-")[1]))
    age = st.sidebar.selectbox("Age group", ages, index=ages.index("15-29"), key="f_age")
    sex = st.sidebar.radio("Sex", SEXES, horizontal=True, key="f_sex")

    sub = c[(c["status"] == status) & (c["age"] == age) & (c["sex"] == sex)]
    years = sorted(sub["year"].unique())
    year = st.sidebar.select_slider("Year", options=years, value=years[-1], key="f_year") if len(years) > 1 \
        else years[0]
    st.sidebar.caption("Source: Eurostat, edat_lfse_20 - % of the population in the age group.")
    return {"status": status, "age": age, "sex": sex, "year": int(year)}


def get_selected(options) -> str | None:
    sel = st.session_state.get("country")
    return sel if sel in list(options) else None


# ----------------------------------------------------------- components
def title_block(title: str, f: dict):
    st.title(title)
    st.caption(f"**{f['status']}** · ages **{f['age']}** · **{f['sex']}** · **{f['year']}**")


def render_kpis(t: pd.DataFrame, f: dict, eu_value: float = np.nan):
    s = compute_stats(t)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🥇 Highest Country", s["highest"]["country"], f"{s['highest']['value']:.1f}%",
              delta_color="inverse")
    c2.metric("🥉 Lowest Country", s["lowest"]["country"], f"{s['lowest']['value']:.1f}%",
              delta_color="inverse")
    c3.metric("🌍 Number of Countries", s["n"])
    c4.metric("📈 Standard Deviation", f"{s['std']:.2f} pp")
    delta = None if np.isnan(eu_value) else f"{s['median'] - eu_value:+.1f} vs EU27 ({eu_value:.1f}%)"
    c5.metric("📉 Median", f"{s['median']:.1f}%", delta, delta_color="inverse")


def ranking_controls_and_table(t: pd.DataFrame, key="rank"):
    """Search + sort ascending/descending + ranked list. Returns the filtered table."""
    c1, c2 = st.columns([3, 2])
    q = c1.text_input("Search country", key=f"{key}_q", placeholder="e.g. Ital, Rom, Tür")
    order = c2.radio("Sort", ["Descending ↓", "Ascending ↑"], horizontal=True, key=f"{key}_order")
    asc = order.startswith("Asc")

    r = t.sort_values("value", ascending=asc).reset_index(drop=True)
    r.insert(0, "Rank", np.arange(1, len(r) + 1))          # rank follows the chosen order
    if q:
        r = r[r["country"].str.contains(q.strip(), case=False, na=False)]
    if r.empty:
        st.info("No country matches your search.")
        return r

    sel = st.session_state.get("country")
    out = pd.DataFrame({
        "Rank": r["Rank"],
        "Country": np.where(r["country"] == sel, "> " + r["country"], r["country"]),
        "Value (%)": r["value"],
        "Reliability": np.where(r["flag"].str.contains("u", na=False), "low", "ok"),
    })
    vmax = float(t["value"].max())
    st.dataframe(
        out, hide_index=True, height=min(740, 38 + 35 * len(out)),
        column_config={
            "Value (%)": st.column_config.ProgressColumn("Value (%)", format="%.1f%%", min_value=0,
                                                         max_value=vmax),
        },
    )
    return r


def ranking_chart(r: pd.DataFrame, t: pd.DataFrame, asc: bool = False):
    """Horizontal bar ranking coloured with the same green→red gradient."""
    lo, hi = float(t["value"].min()), float(t["value"].max())
    sel = st.session_state.get("country")
    r = r.sort_values("value", ascending=not asc)  # plotly draws bottom→top
    fig = go.Figure(go.Bar(
        x=r["value"], y=r["country"], orientation="h",
        marker=dict(color=r["value"], colorscale=GRADIENT, cmin=lo, cmax=hi,
                    line=dict(color=["#111" if c == sel else "rgba(0,0,0,0)" for c in r["country"]], width=2)),
        text=r["value"].map("{:.1f}%".format), textposition="outside",
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(height=max(320, 22 * len(r) + 60), margin=dict(l=0, r=30, t=10, b=0),
                      yaxis=dict(automargin=True), xaxis=dict(title="% of age group"))
    st.plotly_chart(fig)


def europe_map(t: pd.DataFrame, f: dict, selected: str | None):
    """Choropleth; returns the Streamlit plotly event so the caller can read clicks."""
    lo, hi = float(t["value"].min()), float(t["value"].max())
    fig = go.Figure(go.Choropleth(
        locations=t["iso3"], z=t["value"], text=t["country"], locationmode="ISO-3",
        colorscale=GRADIENT, zmin=lo, zmax=hi,
        marker=dict(line=dict(color="white", width=0.6)),
        colorbar=dict(title="%", thickness=14, len=0.7),
        hovertemplate="<b>%{text}</b><br>%{z:.1f}%<extra></extra>",
    ))
    if selected and selected in set(t["country"]):                 # thick outline on the clicked country
        row = t[t["country"] == selected].iloc[0]
        fig.add_trace(go.Choropleth(
            locations=[row["iso3"]], z=[row["value"]], text=[selected], locationmode="ISO-3",
            colorscale=GRADIENT, zmin=lo, zmax=hi, showscale=False,
            marker=dict(line=dict(color="#111", width=3)),
            hovertemplate="<b>%{text}</b><br>%{z:.1f}%<extra></extra>",
        ))
    fig.update_traces(selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)))
    fig.update_geos(scope="europe", projection_type="natural earth", showframe=False,
                    showcountries=True, countrycolor="#bbb", showland=True, landcolor="#e6e6e6",
                    bgcolor="rgba(0,0,0,0)")
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return st.plotly_chart(fig, on_select="rerun",
                           selection_mode="points",
                           key=f"europe_map_{st.session_state.get('map_nonce', 0)}")


def handle_map_click(event, t: pd.DataFrame):
    """Store the clicked country in session_state (shared across pages)."""
    try:
        pts = event.selection.points
    except Exception:
        pts = []
    if pts:
        iso = pts[0].get("location")
        hit = t.loc[t["iso3"] == iso, "country"]
        if len(hit):
            st.session_state["country"] = hit.iloc[0]


def country_selector(t: pd.DataFrame, container=st):
    """Dropdown complement to map clicks; call it BEFORE the map is drawn.

    Picking a country here also resets the map widget (new key) so an old map click
    can't overwrite the choice on the next rerun.
    """
    names = ["— none —"] + sorted(t["country"])
    cur = get_selected(t["country"])
    choice = container.selectbox("Selected country (click the map or pick here)", names,
                                 index=names.index(cur) if cur else 0, key=f"sel_{cur}")
    new = None if choice == "— none —" else choice
    if new != cur:                                   # changed by the user, not by a map click
        if new:
            st.session_state["country"] = new
        else:
            st.session_state.pop("country", None)
        st.session_state["map_nonce"] = st.session_state.get("map_nonce", 0) + 1


def tier(value: float, t: pd.DataFrame) -> str:
    q1, q3 = t["value"].quantile([1 / 3, 2 / 3])
    return "🟢 Low" if value <= q1 else ("🔴 High" if value >= q3 else "🟡 Medium")
