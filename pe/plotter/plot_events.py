from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from pe.log_scraper.log_scraper import Event

def plot_events(
        old_events: list[Event], 
        new_events: list[Event], 
        title: str, 
        outage: tuple[datetime, datetime], 
        new_loc: tuple[datetime, float],
        old_loc: tuple[datetime, float],
    ):
    # Plot an event (presumably from a source)
    old_staggers = [-x for x in range(1,8)]
    old_labels = [event.readable for event in old_events]
    old_levels = [old_staggers[ix % len(old_staggers)] for ix in range(len(old_labels))]
    old_times = [e.timestamp for e in old_events]

    new_staggers = [x for x in range(1,8)]
    new_labels = [event.readable for event in new_events]
    new_levels = [new_staggers[ix % len(new_staggers)] for ix in range(len(new_labels))]
    new_times = [e.timestamp for e in new_events]

    fig, ax = plt.subplots(figsize=(8.8, 4), layout="constrained")
    ax.set(title=title)

    labels = old_labels + new_labels
    levels = old_levels + new_levels
    times = old_times + new_times

    chunks = sorted(zip(labels, levels, times), key=lambda i: i[2])

    ax.vlines(old_times, 0, old_levels, color="tab:blue")
    ax.vlines(new_times, 0, new_levels, color="tab:green")
    # ax.hlines([0], [xticks[0]], [xticks[-1]], linestyles=["dashed"])
    ax.plot(times, np.zeros_like(times), "-o",
            color="k", markerfacecolor="w")
    
    for ix, (r, l, d) in enumerate(chunks):
        ax.annotate(f"{ix}. {r}", xy=(d,l), xytext=(-3, np.sign(l)*3), textcoords="offset points",
                    horizontalalignment="right",
                    verticalalignment="bottom" if l > 0 else "top")
    
    # Shade in the region with client downtime
    ax.axvspan(outage[0], outage[1], alpha=0.12, facecolor="r", label="Outage from Client's Perspective")
    ax.legend()

    # Hand draw above/below labels for clarity
    ax.annotate("New Primary Events", xy=new_loc,
                    xytext=(-3,4), textcoords="offset points",
                    weight="bold",
                    fontsize=16,
                    color="green",
                    horizontalalignment="center",
                    verticalalignment="top")

    ax.annotate("Old Primary Events", xy=old_loc,
                    xytext=(-3,4), textcoords="offset points",
                    weight="bold",
                    fontsize=16,
                    color="blue",
                    horizontalalignment="center",
                    verticalalignment="top")

    # plt.xlim(xticks[0], xticks[-1])
    # ax.set_xticks(xticks)
    # ax.xaxis.set_major_locator(mdates.SecondLocator(interval=1))
    # plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # remove y-axis and spines
    ax.yaxis.set_visible(False)
    ax.spines[["left", "top", "right"]].set_visible(False)

    ax.margins(y=0.1)
    plt.show()