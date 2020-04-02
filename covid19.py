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
import altair as alt

"""## Get Data from GitHub"""

url = (
    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
    "csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
)

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

countries = [
    "Sweden",
    "Norway",
    "Denmark",
    "Finland",
    "Italy",
    "Spain",
    "Germany",
    "France",
    "US",
    "United Kingdom",
    "Belgium",
    "China"
]
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


df["Day"] = df.apply(add_days_since_10, axis=1)
df


df["Diff"] = 0
for country in countries:
    df.update(
        pd.DataFrame(
            {"Diff": df[df.Country == country].Deaths.diff().fillna(0.0).astype(np.int)}
        )
    )
df


df["OneWeekDeaths"] = 0
for country in countries:
    df.update(
        pd.DataFrame(
            {
                "OneWeekDeaths": df[df.Country == country]
                .Diff.rolling(min_periods=1, window=7)
                .sum()
                .fillna(0.0)
                .astype(np.int)
            }
        )
    )
df

df["Diff"] = df["Diff"][df["Diff"] != 0]

"""## Plot the Dataset"""


def plot_chart(x_field, x_title, y_field, y_title, interpolate=None):
    selection = alt.selection_multi(fields=["Country"], bind="legend")

    chart = (
        alt.Chart(df)
        .transform_filter(alt.datum[y_field] >= 10)
        .encode(
            alt.X(
                f"{x_field}:{x_field == 'Date' and 'T' or 'Q'}",
                axis=x_field == "Date"
                and alt.Axis(title=x_title)
                or alt.Axis(title=x_title, tickMinStep=1),
            ),
            alt.Y(
                f"{y_field}:Q",
                scale=alt.Scale(type="log"),
                axis=alt.Axis(title=y_title),
            ),
            alt.Color("Country:N"),
            #  shape=alt.Shape("Country"),
            tooltip=["Country", y_field, x_field],
            opacity=alt.condition(selection, alt.value(1), alt.value(0.12)),
        )
        .add_selection(selection)
        .interactive()
        #.configure_point(size=95)
        .properties(width="container", height=700)
    )

    if interpolate:
        chart = chart.mark_line(point=True, interpolate=interpolate)
    else:
        chart = chart.mark_line(point=True)

    return chart


charts_template = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/vega@{vega_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@{vegalite_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@{vegaembed_version}"></script>
</head>
<body style="padding:3em;font-family: Sans-Serif;">
<h1>COVID-19 Visualizations</h1>
<p>
Made by <a href="https://twitter.com/tomhe">@tomhe</a> with data from <a href="https://github.com/CSSEGISandData/COVID-19">Johns Hopkins CSSE</a> and inspired by <a href="https://www.ft.com/coronavirus-latest">Financial Times' Coronavirus tracker</a> by <a href="https://twitter.com/jburnmurdoch">John Burn-Murdoch</a> et al.
</p>

<h2>Cumulative Deaths</h2>
<p>This chart shows the cumulative number of deaths by date.</p>
<div id="vis1" style="width:100%"></div>

<h2>Cumulative Deaths Since Same Day of Outbreak</h2>
<p>This chart shows the cumulative number of deaths by number of days since 10th death.</p>
<div id="vis2" style="width:100%"></div>

<h2>Deaths per Week Since Same Day of Outbreak</h2>
<p>This chart shows the number deaths per week by number of days since 10th death.</p>
<div id="vis3" style="width:100%"></div>

<!--
<h2>Deaths per Day</h2>
<p>This chart shows the number deaths per day by number of days since 10th death.</p>
<div id="vis4" style="width:100%"></div>
-->

<script type="text/javascript">
  vegaEmbed('#vis1', {spec1}).catch(console.error);
  vegaEmbed('#vis2', {spec2}).catch(console.error);
  vegaEmbed('#vis3', {spec3}).catch(console.error);
  vegaEmbed('#vis4', {spec4}).catch(console.error);
</script>
</body>
</html>
"""


chart1 = plot_chart(
    x_field="Date", x_title="Date", y_field="Deaths", y_title="Total deaths",
    interpolate="monotone"
)
chart2 = plot_chart(
    x_field="Day",
    x_title="Number of days since ~10th death",
    y_field="Deaths",
    y_title="Total deaths",
    interpolate="monotone"
)
chart3 = plot_chart(
    x_field="Day",
    x_title="Number of days since ~10th death",
    y_field="OneWeekDeaths",
    y_title="Deaths per week",
    interpolate="monotone"
)
chart4 = plot_chart(
    x_field="Day",
    x_title="Number of days since ~10th death",
    y_field="Diff",
    y_title="Deaths per day",
    interpolate="monotone"
)

print("Writing plots")
with open("docs/index.html", "w") as f:
    f.write(
        charts_template.format(
            vega_version=alt.VEGA_VERSION,
            vegalite_version=alt.VEGALITE_VERSION,
            vegaembed_version=alt.VEGAEMBED_VERSION,
            spec1=chart1.to_json(indent=None),
            spec2=chart2.to_json(indent=None),
            spec3=chart3.to_json(indent=None),
            spec4=chart4.to_json(indent=None),
        )
    )
