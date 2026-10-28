# NEET Dashboard

An interactive Streamlit dashboard that shows the real size of **inactive NEET youth** in Europe:
young people who are *Not in Employment, Education or Training* **and** are outside the labour force
(not working and not looking for work). Headline NEET figures often hide this group behind the
unemployment rate; this dashboard puts it in front.

Data source: Eurostat, table **edat_lfse_20** (young people neither in employment nor in education
and training, by sex, age and labour status). Values are **percentages of the age group's population**.

## Features

- **Key figures:** highest country, lowest country, number of countries, standard deviation and median,
  with the median compared against the EU27 value.
- **Interactive Europe map:** click any country and the details update. Colour gradient:
  green = low, yellow = medium, red = high.
- **Interactive ranking:** search by country and sort ascending or descending.
- **Charts:** trends over time, women vs men, and age groups.
- **Statistics:** descriptive statistics, a breakdown of what is behind the inactive NEET
  (with every formula and a worked example), change over time, and data quality flags.
- **Global filters** (sidebar): indicator, age group, sex and year, shared across all pages.

## Project structure

```
NEET Dashboard/
├── app.py                 Home: key figures and ranking
├── data.csv               Cleaned dataset used by the app
├── prepare_data.py        Rebuilds data.csv from the raw Eurostat exports
├── utils.py               Data loading, filters, KPI cards, map and ranking components
├── requirements.txt
├── assets/
│   └── logo.png           Placeholder logo, replace with your own
└── pages/
    ├── 1_Map.py           Interactive Europe map
    ├── 2_Charts.py        Trends, women vs men, age groups
    └── 3_Statistics.py    Statistics and methodology
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Requires Python 3.9+ and Streamlit 1.40 or newer. The map needs an internet connection,
because Plotly loads the country outlines from its CDN.

## Updating the data

1. Download the table from Eurostat (edat_lfse_20) as CSV, linear format.
2. Put the file(s) in a local `raw/` folder (it is git-ignored).
3. Run:

   ```bash
   python prepare_data.py raw/edat_lfse_20_defaultview_linear.csv
   ```

   You can pass several files; duplicates are removed.

`prepare_data.py` keeps the five labour-status indicators, drops empty values, shortens labels,
adds ISO-3 country codes for the map and marks the EU27 and Euro area rows as aggregates.

## Indicators and methodology

| Letter | Group | Eurostat label | Source |
|---|---|---|---|
| A | Inactive NEET | Persons outside the labour force | Eurostat |
| B | Inactive, do not want to work | Persons do not want to work | Eurostat |
| D | Unemployed NEET | Unemployed persons | Eurostat |
| E | Total NEET | Not employed persons | Eurostat |
| C | Inactive but would like to work | | Calculated: `C = A - B` |
| | Inactive share of NEET | | Calculated: `A / E x 100` |

Checks run on all 3,860 country/year/sex/age combinations in the data:
`A + D` matches `E`, and `C` matches Eurostat's "would like to work" minus `D`, both within 0.1
percentage points (rounding). The Statistics page shows these checks and a worked example per country.

## Notes and limitations

- All figures are **percentages of the age group**, not headcounts, and age groups overlap
  (15-29 includes 15-24), so they cannot be added together.
- Eurostat quality flags are kept in the data: **u** low reliability, **b** break in time series,
  **d** definition differs. Low-reliability values are marked in the ranking.
- EU27 and Euro area values are used only as benchmarks and are excluded from country statistics.
- Not every country has data for every year (for example, the UK stops after 2019, Montenegro after 2020,
  and Bosnia and Herzegovina starts in 2021).
- Statistics such as the median and standard deviation are computed across the countries shown for the
  selected filters, unweighted by population.

## License and data terms

Add a license for the code of your choice. Eurostat data may be reused with attribution to Eurostat.
