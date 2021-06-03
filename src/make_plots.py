# Makes some plots! Also see the Jupyter Notebook for more exploration

from os.path import join

import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge, Lasso
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np

DATA_DIR = "/Users/garrick/code/cs229/proj/src/data"
gambit_matches = "gambit.csv"
all_matches = "all.csv"

df_all = pd.read_csv(join(DATA_DIR, all_matches), index_col=0, parse_dates=["period"])


activityCounts = Counter()
for aname in df_all["director_activity_name"]:
    activityCounts[aname] += 1

COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
pin_activities = [
    "Nightfall: Master",
    "Gambit",
    "Control",
    "The Shattered Throne",
    "Prophecy",
    "Pit of Heresy: Normal",
    "Nightfall: Legend",
    "Nightfall: Hero",
    "Nightfall: Grandmaster",
    "Garden of Salvation",
    "Deep Stone Crypt",
]


def histogram():
    x, y = zip(*activityCounts.most_common())
    bar_colors = [COLORS[0] if a not in pin_activities else COLORS[1] for a in x]
    plt.bar(np.arange(len(x)), y, color=bar_colors)
    plt.show()
    plt.clf()


def top_and_bottom():
    plt.figure(figsize=(6.4 * 2, 4.8))
    plt.subplot(1, 2, 1)

    x, y = zip(*activityCounts.most_common(10))
    bar_colors = [COLORS[0] if a not in pin_activities else COLORS[1] for a in x]
    plt.bar(np.arange(len(x)), y, tick_label=x, color=bar_colors)
    plt.xticks(rotation=45, ha="right")  # ha - horizontal align
    plt.title("Top 10 Activities")

    plt.subplot(1, 2, 2)

    x, y = zip(*activityCounts.most_common()[-10:])
    bar_colors = [COLORS[0] if a not in pin_activities else COLORS[1] for a in x]
    plt.bar(np.arange(len(x)), y, tick_label=x, color=bar_colors)
    plt.xticks(rotation=45, ha="right")  # ha - horizontal align
    plt.title("Bottom 10 Activities")
    plt.show()
    plt.clf()


def histogram_pinned():
    pins = [(aname, activityCounts[aname]) for aname in pin_activities]
    pins = sorted(pins, key=lambda t: t[1])[
        ::-1
    ]  # Sort according to 2nd entry of tuple
    x, y = zip(*pins)
    plt.bar(np.arange(len(x)), y, tick_label=x, color=COLORS[1])
    plt.xticks(rotation=45, ha="right")  # ha - horizontal align
    plt.show()
    plt.clf()
