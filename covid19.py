# -*- coding: utf-8 -*-
"""covid19.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PpCf3ylFKFFzec0amQOMVV4BdoFrymgg

# COVID-19 Deaths for Some Selected Countries

This notebook uses the data provided by [Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19).
"""

import datetime
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
    # "Australia",
    "Austria",
    "Belgium",
    "Canada",
    "Denmark",
    # "Finland",
    "France",
    "Germany",
    "Italy",
    "Norway",
    "Spain",
    "Sweden",
    "United Kingdom",
    "US",
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


def plot_chart(df, x_field, x_title, y_field, y_title, y_min=10):
    selection = alt.selection_multi(fields=["Country"], bind="legend")

    if x_field == "Date":
        today = datetime.datetime.now()
        today_plus_5 = today + datetime.timedelta(days=5)
        domain = ["2020-02-25", str(today_plus_5).split()[0]]
        x = alt.X(
            f"{x_field}:T",
            axis=alt.Axis(title=x_title),
            scale=alt.Scale(domain=domain),
        )
    else:
        domain = [0, int(df[x_field].max() + 2)]
        x = alt.X(
            f"{x_field}:Q",
            axis=alt.Axis(title=x_title, tickMinStep=1),
            scale=alt.Scale(domain=domain),
        )

    chart = (
        alt.Chart(df)
        .transform_filter(alt.datum[y_field] >= y_min)
        .encode(
            x,
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

    chart = chart.mark_line(size=1.7)

    text = (
        alt.Chart(df)
        .mark_text(align="left", baseline="middle", dx=6)
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
    ).configure_legend(orient="bottom", columns=4)


with open("docs/covid19_template.html") as f:
    charts_template = f.read()

chart1 = plot_chart(
    df=df, x_field="Date", x_title="Date", y_field="Deaths", y_title="Total deaths",
)
chart2 = plot_chart(
    df=df[df.DaySince10Deaths >= 0],
    x_field="DaySince10Deaths",
    x_title="Number of days since ~10th death",
    y_field="Deaths",
    y_title="Total deaths",
)
chart3 = plot_chart(
    df=df[df.DeathsPerDay >= 0],
    x_field="Date",
    x_title="Date",
    y_field="DeathsPerDay",
    y_title="Deaths per day (7-day rolling average)",
    y_min=1,
)
chart4 = plot_chart(
    df=df[df.DaySince3DeathsPerDay >= 0],
    x_field="DaySince3DeathsPerDay",
    x_title="Number of days since 3 deaths per day",
    y_field="DeathsPerDay",
    y_title="Deaths per day (7-day rolling average)",
    y_min=1,
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
