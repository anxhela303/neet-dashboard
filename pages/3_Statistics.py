import numpy as np
import plotly.express as px
import streamlit as st

from utils import (load_data, sidebar_filters, year_table, slice_data, countries_only,
                   render_kpis, benchmark, title_block, get_selected)

st.set_page_config(page_title="Statistics - NEET", layout="wide")

df = load_data()
f = sidebar_filters(df)
t = year_table(df, f)
title_block("Statistics", f)
if t.empty:
    st.warning("No data for this combination of filters.")
    st.stop()

render_kpis(t, f, benchmark(df, f))
st.divider()

# ------------------------------------------------------------------ descriptive statistics
st.subheader("Descriptive statistics")
v = t["value"]
desc = {
    "Countries": v.count(), "Mean": v.mean(), "Median": v.median(),
    "Std. deviation (sample, n-1)": v.std(ddof=1), "Min": v.min(), "Q1 (25%)": v.quantile(.25),
    "Q3 (75%)": v.quantile(.75), "Max": v.max(), "Range (max - min)": v.max() - v.min(),
    "Coefficient of variation (%) = std / mean x 100": v.std(ddof=1) / v.mean() * 100,
}
st.dataframe({"Statistic": list(desc), "Value": [round(float(x), 2) for x in desc.values()]},
             hide_index=True, width=620)
st.caption("Computed across countries only; EU27 and Euro area aggregates are excluded.")

# ------------------------------------------------------------------ composition of NEET
st.divider()
st.subheader("What is behind the inactive NEET?")

base = dict(sex=f["sex"], age=f["age"], year=f["year"])
get = lambda s: countries_only(slice_data(df, status=s, **base)).set_index("country")["value"]
A = get("Inactive")                              # persons outside the labour force
B = get("Inactive - do not want to work")        # persons do not want to work
D = get("Unemployed")
E = get("Not employed (total NEET)")
comp = (A.to_frame("A").join(B.rename("B")).join(D.rename("D")).join(E.rename("E"))).dropna()

if comp.empty:
    st.info("Not enough indicators for this selection.")
    st.stop()

raw_c = comp["A"] - comp["B"]
comp["C"] = raw_c.clip(lower=0)
comp["share"] = comp["A"] / comp["E"] * 100
comp["check"] = comp["A"] + comp["D"] - comp["E"]
n_clipped = int((raw_c < 0).sum())

with st.expander("How each group is calculated", expanded=True):
    st.markdown(
        f"""
All values come from Eurostat table **edat_lfse_20** and are **percentages of the whole
age group's population** (for example, % of all people aged {f['age']}), not counts of people and not
percentages of the NEET. Sex = **{f['sex']}**, year = **{f['year']}**.

**Series taken directly from Eurostat (no calculation)**

| Letter | Group | Eurostat label |
|---|---|---|
| A | Inactive NEET | Persons outside the labour force |
| B | Inactive who do **not** want to work | Persons do not want to work |
| D | Unemployed NEET | Unemployed persons |
| E | Total NEET | Not employed persons |

**Groups calculated in this dashboard**

| Group | Formula | Meaning |
|---|---|---|
| C - Inactive but **would like** to work | `C = A - B` | Outside the labour force, not searching, but would take a job (a hidden labour reserve) |
| Inactive share of NEET (%) | `A / E x 100` | How much of the total NEET group is inactive rather than unemployed |

**Consistency checks**
- Total NEET is made up of the unemployed and the inactive, so `A + D` should be approximately `E`.
  The column *Check* shows `A + D - E`; values near 0 (never more than 0.1 pp in this dataset) come from rounding to one decimal.
- Eurostat's "would like to work" series includes the unemployed, so `would like to work - D` should be
  close to `C`. This confirms the subtraction `A - B` is a sound way to isolate the inactive who want a job.
- Because every figure is rounded to 1 decimal, differences of up to 0.1 pp are expected.
- If `A - B` came out negative from rounding it is set to 0 ({n_clipped} of {len(comp)} countries in this selection).
"""
    )

# worked example
names = list(comp.sort_values("share", ascending=False).index)
sel = get_selected(names)
ex_country = st.selectbox("Show the working for", names, index=names.index(sel) if sel else 0)
r = comp.loc[ex_country]
st.markdown(
    f"**Worked example: {ex_country}, {f['sex'].lower()}, {f['age']}, {f['year']}**\n\n"
    f"1. Inactive (A) = **{r['A']:.1f}%**\n"
    f"2. Inactive who do not want to work (B) = **{r['B']:.1f}%**\n"
    f"3. Inactive but would like to work: C = A - B = {r['A']:.1f} - {r['B']:.1f} = **{r['C']:.1f}%**\n"
    f"4. Unemployed (D) = **{r['D']:.1f}%**, total NEET (E) = **{r['E']:.1f}%**\n"
    f"5. Check: A + D = {r['A']:.1f} + {r['D']:.1f} = {r['A'] + r['D']:.1f}, "
    f"versus E = {r['E']:.1f} (difference {r['check']:+.1f} pp)\n"
    f"6. Inactive share of NEET = A / E x 100 = {r['A']:.1f} / {r['E']:.1f} x 100 = **{r['share']:.0f}%**"
)

k1, k2, k3 = st.columns(3)
k1.metric("Median inactive share of NEET", f"{comp['share'].median():.0f}%")
top = comp["share"].idxmax()
k2.metric("Highest inactive share", top, f"{comp.loc[top, 'share']:.0f}% of NEET", delta_color="off")
k3.metric("Median C (inactive, would like to work)", f"{comp['C'].median():.1f}%")

order = comp.assign(s=comp["D"] + comp["A"]).sort_values("s", ascending=False).index
m = comp.reset_index().rename(columns={
    "D": "Unemployed (D)", "C": "Inactive, would like to work (C = A - B)",
    "B": "Inactive, do not want to work (B)"})
groups = ["Unemployed (D)", "Inactive, would like to work (C = A - B)", "Inactive, do not want to work (B)"]
m = m.melt(id_vars="country", value_vars=groups, var_name="Group", value_name="value")
fig = px.bar(m, x="country", y="value", color="Group", category_orders={"country": list(order)},
             color_discrete_map={groups[0]: "#f1c40f", groups[1]: "#e67e22", groups[2]: "#c0392b"},
             labels={"value": "% of age group", "country": ""})
fig.update_layout(height=480, barmode="stack", legend=dict(orientation="h", y=-0.25))
st.plotly_chart(fig)

table = comp.rename(columns={
    "A": "Inactive (A)", "B": "Do not want to work (B)", "C": "Would like to work (C = A - B)",
    "D": "Unemployed (D)", "E": "Total NEET (E)", "share": "Inactive share of NEET % (A / E x 100)",
    "check": "Check (A + D - E)"})
st.dataframe(table.round(1).sort_values("Inactive share of NEET % (A / E x 100)", ascending=False))

# ------------------------------------------------------------------ change over time
st.divider()
st.subheader("Change over time")
a, b = st.columns(2)
d = countries_only(slice_data(df, status=f["status"], sex=f["sex"], age=f["age"]))
years = sorted(d["year"].unique())
y0 = a.selectbox("From", years, index=0)
y1 = b.selectbox("To", years, index=len(years) - 1)
ch = (d[d["year"] == y1].set_index("country")["value"] - d[d["year"] == y0].set_index("country")["value"]).dropna()
if y0 >= y1 or ch.empty:
    st.info("Choose two different years (From < To) with data.")
else:
    ch = ch.sort_values().rename("pp change").reset_index()
    fig = px.bar(ch, x="pp change", y="country", orientation="h", color="pp change",
                 color_continuous_scale=["#2ecc71", "#f1c40f", "#e74c3c"], color_continuous_midpoint=0)
    fig.update_layout(height=max(400, 22 * len(ch)), coloraxis_showscale=False)
    st.plotly_chart(fig)
    st.caption("Percentage-point change; green = fell, red = rose. Series breaks (flag 'b') may affect comparisons.")

# ------------------------------------------------------------------ data quality
st.divider()
st.subheader("Data quality flags")
fl = countries_only(slice_data(df, status=f["status"], sex=f["sex"], age=f["age"], year=f["year"]))
st.write(f"{(fl['flag'] != '').sum()} of {len(fl)} values carry a Eurostat flag "
         "(u = low reliability, b = break in time series, d = definition differs).")
st.dataframe(fl[fl["flag"] != ""][["country", "value", "flag"]], hide_index=True)
