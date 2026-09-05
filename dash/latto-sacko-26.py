#! /usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import scienceplots

plt.style.use(["ieee", "no-latex"])

# time, beers, points
tbp = np.array(
    [
        [0, 0, 0],
        [15, 2, 87],
        [22, 3, 128],
        [32, 5, 174],
        [39, 5, 87],
        [47, 6, 88],
        [57, 7, 43],
        [69, 9, 132],
        [84, 10, 98],
        [98, 10, 102],
        [108, 11, 55],
        [115, 11, 90],
        [121, 12, 0],
        [124, 13, 0],
        [126, 13, 73],
        [137, 14, 75],
        [149, 15, 68],
    ]
)

cum_bowl_pts = np.cumsum(tbp[:, 2])
cum_beer_pts = tbp[:, 1] * 50

fig, ax = plt.subplots(figsize=(6, 4))
ax.stackplot(
    tbp[:, 0],
    cum_bowl_pts,
    cum_beer_pts,
    labels=["Cumulative Bowling Points", "Cumulative Beer Points"],
    edgecolor="gray",
    alpha=0.6,
    colors=["green", "gold"],
)
ax.annotate(
    "2044 Points",
    (20, 2044),
    (0, 1800),
    arrowprops=dict(facecolor="black", width=0.5, headwidth=3, headlength=3),
)
ax.annotate(
    "Bowling break, drank 2 beers and listened to Miracle on Ice speech",
    (115, 1090),
    (100, 1000),
    arrowprops=dict(facecolor="black", width=0.5, headwidth=3, headlength=3),
    horizontalalignment="right",
)
ax.legend()
ax.set_xlabel("Time [minutes]")
ax.set_ylabel("Points")
ax.hlines(2044, 0, 149, "red")
fig.tight_layout()
fig.savefig("latto-sacko-26.png")
