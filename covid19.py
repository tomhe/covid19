# -*- coding: utf-8 -*-
"""covid19.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PpCf3ylFKFFzec0amQOMVV4BdoFrymgg

# COVID-19 Deaths for Some Selected Countries

This notebook uses the data provided by [Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19).
"""

import pandas as pd
import numpy as np
import requests
import altair as alt

"""## Get Data from GitHub"""

url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/" \
      "csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"

df = pd.read_csv(url)
df.sample(5)

"""## Clean Up Data

Remove columns that are not needed.
"""

df = df.drop(["Province/State", "Lat", "Long"], axis=1)
df = df.rename(columns={"Country/Region": "Country"})
df.sample(5)

"""Some countries like UK and US show up on multiple lines (as data is presented for each region), so group all lines by country and sum all values."""

df = df.groupby(["Country"], as_index=False).sum()
df.sample(5)

"""Filter the data set on a small set of countries."""

countries = ["Sweden", "Norway", "Denmark", "Finland", "Italy", "Spain", "Germany", "France", "US", "United Kingdom", "Belgium", "Netherlands"]
df = df[df["Country"].isin(countries)]
df

"""The Altair library that is used for visualization works best with "long" data, so melt our dataset to long format."""

df = df.melt("Country", var_name="Date", value_name="Deaths")
df

"""Finally, fix the date column to be a proper datetime type."""

df["Date"] = pd.to_datetime(df["Date"])
df

"""## Align Countries around Days Since 10th Death
Create a dataframe that holds the date close to 10th death.
"""

ten_days = df.loc[df.Deaths >= 8].groupby(["Country"]).head(1)
ten_days

"""Add "Day" column, that holds "days since 10th death", to dataframe."""

def add_days_since_10(x):
    country = x.Country
    ten_days_date = ten_days[ten_days.Country == country].Date
    return np.int((x.Date - ten_days_date).dt.days)

df["Day"]= df.apply(add_days_since_10 , axis=1)
df

"""## Plot the Dataset"""

def plot_chart(field, x_title):
    domain = (10, int(df.Deaths.max()))

    selection = alt.selection_multi(fields=["Country"], bind="legend")

    chart = alt.Chart(df).transform_filter(
        alt.datum.Deaths >= 10
    ).mark_line(point=True, interpolate="monotone").encode(
        alt.X(f"{field}:{field == 'Date' and 'T' or 'Q'}", axis=alt.Axis(title=x_title)),
        alt.Y("Deaths:Q", scale=alt.Scale(type="log", domain=domain)),
        alt.Color("Country:N"),
        shape=alt.Shape("Country"),
        tooltip=["Country", "Deaths", field],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.12))
    ).add_selection(
        selection
    ).interactive().configure_point(
        size=95
    ).properties(
        width="container",
        height=700
    )

    return chart


two_charts_template = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/vega@{vega_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@{vegalite_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@{vegaembed_version}"></script>
</head>
<body style="padding:3em">

<div id="vis1" style="width:100%"></div>
<div id="vis2" style="width:100%"></div>

<script type="text/javascript">
  vegaEmbed('#vis1', {spec1}).catch(console.error);
  vegaEmbed('#vis2', {spec2}).catch(console.error);
</script>
</body>
</html>
"""


chart1 = plot_chart("Date", "Date")
chart2 = plot_chart("Day", "Number of days since ~10th death")

with open("docs/index.html", "w") as f:
    f.write(two_charts_template.format(
        vega_version=alt.VEGA_VERSION,
        vegalite_version=alt.VEGALITE_VERSION,
        vegaembed_version=alt.VEGAEMBED_VERSION,
        spec1=chart1.to_json(indent=None),
        spec2=chart2.to_json(indent=None),
    ))
