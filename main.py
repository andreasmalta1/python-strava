import json
import pandas as pd
import requests
import time
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from colour import Color

with open("credentials/data.json", "r") as f:
    data = json.loads(f.read())


def get_strava_tokens():
    response = requests.post(
        url="https://www.strava.com/oauth/token",
        data={
            "client_id": data["client_id"],
            "client_secret": data["client_secret"],
            "code": data["access_code"],
            "grant_type": "authorization_code",
        },
    )

    strava_tokens = response.json()

    with open("credentials/strava_tokens.json", "w") as outfile:
        json.dump(strava_tokens, outfile)
    return strava_tokens


def get_activities():
    with open("credentials/strava_tokens.json") as json_file:
        strava_tokens = json.load(json_file)

    if strava_tokens["expires_at"] < time.time():
        response = requests.post(
            url="https://www.strava.com/oauth/token",
            data={
                "client_id": data["client_id"],
                "client_secret": data["client_secret"],
                "grant_type": "refresh_token",
                "refresh_token": strava_tokens["refresh_token"],
            },
        )

        new_strava_tokens = response.json()
        with open("credentials/strava_tokens.json", "w") as outfile:
            json.dump(new_strava_tokens, outfile)
        strava_tokens = new_strava_tokens

    page = 1
    url = "https://www.strava.com/api/v3/activities"
    access_token = strava_tokens["access_token"]

    activities = pd.DataFrame(
        columns=[
            "id",
            "name",
            "start_date_local",
            "type",
            "distance",
            "moving_time",
            "elapsed_time",
            "total_elevation_gain",
            "average_speed",
            "max_speed",
        ]
    )

    while True:
        r = requests.get(
            url
            + "?access_token="
            + access_token
            + "&per_page=200"
            + "&page="
            + str(page)
        )
        r = r.json()

        if not r:
            break

        for x in range(len(r)):
            activities.loc[x + (page - 1) * 200, "id"] = r[x]["id"]
            activities.loc[x + (page - 1) * 200, "name"] = r[x]["name"]
            activities.loc[x + (page - 1) * 200, "start_date_local"] = r[x][
                "start_date_local"
            ].split("T")[0]
            activities.loc[x + (page - 1) * 200, "type"] = r[x]["type"]
            activities.loc[x + (page - 1) * 200, "distance"] = r[x]["distance"]
            activities.loc[x + (page - 1) * 200, "moving_time"] = r[x]["moving_time"]
            activities.loc[x + (page - 1) * 200, "elapsed_time"] = r[x]["elapsed_time"]
            activities.loc[x + (page - 1) * 200, "average_speed"] = r[x][
                "average_speed"
            ]
            activities.loc[x + (page - 1) * 200, "max_speed"] = r[x]["max_speed"]

        page += 1

    activities.to_csv("csv/strava_activities.csv")
    activities = activities[
        (activities["type"] == "Run") & (activities["distance"] > 4900)
    ]
    activities = activities.reset_index()
    activities["moving_time"] = activities["moving_time"] / 60
    activities["moving_time"] = activities["moving_time"].apply(lambda x: round(x, 1))
    activities = activities.round(2)
    return activities


def set_figure(title):
    fig = plt.figure(figsize=(20, 10))
    fig.subplots_adjust(hspace=0.5)
    gs = GridSpec(nrows=1, ncols=1)
    fig.suptitle(f"{title} Runs", fontsize=16)
    return fig, gs


def plot_figure_line(fig, gs, activities):
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(activities["start_date_local"], activities["moving_time"])
    ax.set_title("5k+ Runs")
    ax.set_xlabel("Date")
    ax.set_ylabel("Time in Minutes")


def plot_figure_bar(fig, gs, activities):
    red = Color("green")
    colors = list(red.range_to(Color("red"), len(activities["moving_time"])))
    colors = [color.rgb for color in colors]

    ax = fig.add_subplot(gs[0, 0])
    ax.bar(
        activities["start_date_local"],
        activities["moving_time"],
        color=colors,
        align="edge",
        width=0.3,
    )
    ax.set_title("5k+ Runs")
    ax.set_xlabel("Date")
    ax.set_ylabel("Time in Minutes")

    for index, value in enumerate(activities["moving_time"]):
        ax.text(
            index - 0.3,
            value + 0.1,
            str(value),
            size=8,
            color="blue",
            fontweight="bold",
        )


def save_fig(fig, title):
    plt.xticks(rotation=90)
    fig.savefig(f"images/{title.lower()}_runs.png")


def recent_runs(activities):
    title = "Recent"
    fig, gs = set_figure(title)
    plot_figure_line(fig, gs, activities)
    save_fig(fig, title)


def best_runs(activities):
    title = "Best"
    fig, gs = set_figure(title)
    activities = activities.sort_values("moving_time")
    plot_figure_bar(fig, gs, activities)
    save_fig(fig, title)


def main():
    activities = get_activities()
    recent_runs(activities)
    best_runs(activities)


main()
