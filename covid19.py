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
    "China",
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


def add_days_since_10_deaths(x):
    country = x.Country
    ten_days_date = ten_days[ten_days.Country == country].Date
    return np.int((x.Date - ten_days_date).dt.days)


df["DaySince10Deaths"] = df.apply(add_days_since_10_deaths, axis=1)
df


df["Diff"] = 0
for country in countries:
    df.update(
        pd.DataFrame(
            {"Diff": df[df.Country == country].Deaths.diff().fillna(0.0).astype(np.int)}
        )
    )
df


df["DeathsPerWeek"] = 0
for country in countries:
    df.update(
        pd.DataFrame(
            {
                "DeathsPerWeek": df[df.Country == country]
                .Diff.rolling(min_periods=1, window=7)
                .sum()
                .fillna(0.0)
                .astype(np.float)
            }
        )
    )
df


df["DeathsPerDay"] = np.round(df["DeathsPerWeek"] / 7.0, decimals=1)


three_deaths_per_day = df.loc[df.DeathsPerDay >= 3].groupby(["Country"]).head(1)
three_deaths_per_day


def add_days_since_3_deaths_per_day(x):
    country = x.Country
    three_deaths_per_day_date = three_deaths_per_day[
        three_deaths_per_day.Country == country
    ].Date
    days = (x.Date - three_deaths_per_day_date).dt.days
    if list(days):
        return np.int(days)
    else:
        return np.nan


df["DaySince3DeathsPerDay"] = df.apply(add_days_since_3_deaths_per_day, axis=1)
df

"""## Plot the Dataset"""


def plot_chart(
    df,
    x_field,
    x_title,
    y_field,
    y_title,
    y_min=10,
    interpolate=None,
    align="left",
    dx=0,
):
    selection = alt.selection_multi(fields=["Country"], bind="legend")

    chart = (
        alt.Chart(df)
        .transform_filter(alt.datum[y_field] >= y_min)
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
            tooltip=[
                "Country",
                "Deaths",
                "DeathsPerDay",
                "DaySince10Deaths",
                "DaySince3DeathsPerDay",
                "Date",
            ],
            opacity=alt.condition(selection, alt.value(1), alt.value(0.12)),
        )
    )

    chart = chart.mark_line(interpolate=interpolate, size=1.7)

    text = (
        alt.Chart(df)
        .mark_text(align=align, baseline="middle", dx=dx)
        .encode(
            x=f"max({x_field})",
            y=alt.Y(y_field, aggregate={"argmax": x_field}),
            text="Country",
        )
    ).transform_filter(selection)

    end_point = (
        alt.Chart(df)
        .mark_point()
        .encode(
            x=f"max({x_field})",
            y=alt.Y(y_field, aggregate={"argmax": x_field}),
            color="Country:N",
            opacity=alt.condition(selection, alt.value(1), alt.value(0.12)),
        )
    ).transform_filter(selection)

    return (
        (chart + end_point + text)
        .add_selection(selection)
        .interactive()
        .properties(width="container", height="container")
    )


charts_template = """
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/vega@{vega_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@{vegalite_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@{vegaembed_version}"></script>
  <style>
    body {{
      padding: 3em;
      font-family: Sans-Serif;
    }}
    div.chart {{
      width: 100%;
      height: 700px;/* 90v; */
    }}
  </style>
</head>
<body">
<h1>COVID-19 Visualizations</h1>
<p>
Made by <a href="https://twitter.com/tomhe">@tomhe</a> with data from <a href="https://github.com/CSSEGISandData/COVID-19">Johns Hopkins CSSE</a> and inspired by <a href="https://www.ft.com/coronavirus-latest">Financial Times' Coronavirus tracker</a> by <a href="https://twitter.com/jburnmurdoch">John Burn-Murdoch</a> et al.
</p>
<p>Hint: The countries in the "Country" legends to the right of the charts can be "shift clicked" to select only a few countries (or a single country).</p>

<h2>Cumulative Deaths by Date</h2>
<p>This chart shows the cumulative number of deaths by date.</p>
<div class="chart" id="vis1"></div>

<h2>Cumulative Deaths by Same Day of Outbreak</h2>
<p>This chart shows the cumulative number of deaths by number of days since 10th death.</p>
<p>
The lines for each country are the same as in the chart directly above, but aligned
horizontally to roughly match the point in time when the outbreak reached 10 accumulated
deaths.</p>
<div class="chart" id="vis2"></div>

<h2>Deaths per Day by Date</h2>
<p>This chart shows the number deaths per day (7-day rolling average) by date.</p>
<div class="chart" id="vis3"></div>

<h2>Deaths per Day by Same Day of Outbreak</h2>
<p>This chart shows the number deaths per day (7-day rolling average) by number of days since 3 deaths per day.</p>
<p>
The lines for each country are the same as in the chart directly above, but aligned
horizontally to roughly match the point in time when the outbreak reached 3 deaths per day (7-day rolling average).</p>
<div class="chart" id="vis4"></div>


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
    df=df,
    x_field="Date",
    x_title="Date",
    y_field="Deaths",
    y_title="Total deaths",
    interpolate="monotone",
    align="right",
    dx=-5,
)
chart2 = plot_chart(
    df=df[df.DaySince10Deaths >= 0],
    x_field="DaySince10Deaths",
    x_title="Number of days since ~10th death",
    y_field="Deaths",
    y_title="Total deaths",
    interpolate="monotone",
    align="left",
    dx=5,
)
chart3 = plot_chart(
    df=df[df.DaySince3DeathsPerDay >= 0],
    x_field="Date",
    x_title="Date",
    y_field="DeathsPerDay",
    y_title="Deaths per day (7-day rolling average)",
    y_min=1,
    interpolate="monotone",
    align="right",
    dx=-5,
)
chart4 = plot_chart(
    df=df[df.DaySince3DeathsPerDay >= 0],
    x_field="DaySince3DeathsPerDay",
    x_title="Number of days since 3 deaths per day",
    y_field="DeathsPerDay",
    y_title="Deaths per day (7-day rolling average)",
    y_min=1,
    interpolate="monotone",
    align="left",
    dx=5,
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
