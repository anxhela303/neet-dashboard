"""Build data.csv from the raw Eurostat exports (edat_lfse_20).

Run once:  python prepare_data.py <raw_default_view.csv> [<raw_custom.csv> ...]
The dashboard itself only reads data.csv.
"""
import sys
import pandas as pd

ISO3 = {
    "Austria": "AUT", "Belgium": "BEL", "Bosnia and Herzegovina": "BIH", "Bulgaria": "BGR",
    "Croatia": "HRV", "Cyprus": "CYP", "Czechia": "CZE", "Denmark": "DNK", "Estonia": "EST",
    "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN",
    "Iceland": "ISL", "Ireland": "IRL", "Italy": "ITA", "Latvia": "LVA", "Lithuania": "LTU",
    "Luxembourg": "LUX", "Malta": "MLT", "Montenegro": "MNE", "Netherlands": "NLD",
    "North Macedonia": "MKD", "Norway": "NOR", "Poland": "POL", "Portugal": "PRT",
    "Romania": "ROU", "Serbia": "SRB", "Slovakia": "SVK", "Slovenia": "SVN", "Spain": "ESP",
    "Sweden": "SWE", "Switzerland": "CHE", "Türkiye": "TUR", "United Kingdom": "GBR",
}
STATUS = {
    "Persons outside the labour force": "Inactive",
    "Not employed persons": "Not employed (total NEET)",
    "Unemployed persons": "Unemployed",
    "Persons do not want to work": "Inactive - do not want to work",
    "Persons would like to work (seeking employment or not)": "Would like to work",
}


def build(paths, out="data.csv"):
    raw = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    df = pd.DataFrame({
        "country": raw["geo"].str.replace(r"^European Union.*", "EU27", regex=True)
                             .str.replace(r"^Euro area.*", "Euro area", regex=True),
        "year": raw["TIME_PERIOD"],
        "sex": raw["sex"],
        "age": raw["age"].str.replace("From ", "").str.replace(" to ", "-").str.replace(" years", ""),
        "status": raw["wstatus"].map(STATUS),
        "value": raw["OBS_VALUE"],
        "flag": raw["OBS_FLAG"].fillna(""),
    })
    df["iso3"] = df["country"].map(ISO3)
    df["is_aggregate"] = df["iso3"].isna()
    df = (df.dropna(subset=["value", "status"])
            .drop_duplicates(["country", "year", "sex", "age", "status"])
            .sort_values(["status", "age", "sex", "year", "country"]))
    df.to_csv(out, index=False)
    print(f"{out}: {len(df):,} rows, {df.country.nunique()} geos")


if __name__ == "__main__":
    build(sys.argv[1:])
