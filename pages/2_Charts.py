import plotly.express as px
import streamlit as st

from utils import (load_data, sidebar_filters, year_table, slice_data, countries_only,
                   get_selected, title_block)

st.set_page_config(page_title="Charts - NEET", layout="wide")

df = load_data()
f = sidebar_filters(df)
t = year_table(df, f)
title_block("Charts", f)

all_geo = sorted(df.loc[df["status"] == f["status"], "country"].unique())
sel = get_selected(all_geo)
default = [c for c in [sel, "EU27", "Italy", "Romania", "Sweden"] if c in all_geo]
tab1, tab2, tab3 = st.tabs(["Trends", "Women vs men", "Age groups"])

with tab1:
    picks = st.multiselect("Countries / aggregates", all_geo, default=default[:5])
    d = slice_data(df, status=f["status"], sex=f["sex"], age=f["age"])
    d = d[d["country"].isin(picks)]
    if d.empty:
        st.info("Pick at least one country.")
    else:
        fig = px.line(d, x="year", y="value", color="country", markers=True,
                      labels={"value": "% of age group", "year": ""})
        fig.update_layout(height=480, hovermode="x unified")
        st.plotly_chart(fig)
        st.caption("Breaks in series and low-reliability flags exist in the raw data; see the Statistics page.")

with tab2:
    d = countries_only(df[(df["status"] == f["status"]) & (df["age"] == f["age"])
                          & (df["year"] == f["year"]) & (df["sex"] != "Total")])
    if d.empty:
        st.info("No data.")
    else:
        order = d.groupby("country")["value"].mean().sort_values(ascending=False).index
        fig = px.bar(d, x="country", y="value", color="sex", barmode="group",
                     category_orders={"country": list(order)},
                     color_discrete_map={"Females": "#e84393", "Males": "#0984e3"},
                     labels={"value": "% of age group", "country": ""})
        fig.update_layout(height=500)
        st.plotly_chart(fig)

with tab3:
    geo = st.selectbox("Country", sorted(countries_only(df)["country"].unique()) + ["EU27"],
                       index=0 if not sel else (sorted(countries_only(df)["country"].unique()) + ["EU27"]).index(sel))
    d = df[(df["country"] == geo) & (df["status"] == f["status"]) & (df["year"] == f["year"])
           & (df["sex"] == f["sex"])]
    if d.empty:
        st.info("No data for this country/year.")
    else:
        d = d.assign(k=d["age"].map(lambda a: int(a.split("-")[1]))).sort_values("k")
        fig = px.bar(d, x="age", y="value", text="value", labels={"value": "%", "age": "Age group"})
        fig.update_traces(texttemplate="%{text:.1f}%", marker_color="#e67e22")
        st.plotly_chart(fig)
        st.caption("Age groups are cumulative (15-29 includes 15-24, etc.), so they are not additive.")
