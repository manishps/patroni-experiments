from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

def plot_client_perspective(client_times: list[datetime]) -> tuple[datetime, datetime]:
    # Plots the line showing interruption from the client's perspective
    biggest_gap = -1
    gap_ix = -1
    for ix in range(len(client_times) - 1):
        this_time = client_times[ix]
        next_time = client_times[ix + 1]
        this_gap = (next_time - this_time).seconds
        if this_gap > biggest_gap:
            biggest_gap = this_gap
            gap_ix = ix 
    
    result = (client_times[gap_ix], client_times[gap_ix + 1])

    fig, ax = plt.subplots(figsize=(8.8, 4), layout="constrained")
    # ax.set(title="Events observered during failover")

    ax.vlines(client_times, 0, [0 for thing in client_times], color="tab:red")  # The vertical stems.
    ax.plot(client_times, np.zeros_like(client_times), "-o",
            color="k", markerfacecolor="w", label="Writes that made it to the Database")

    # Hand draw label for client gap
    ax.annotate(f"Downtime observed by client\n{biggest_gap} seconds", xy=(client_times[gap_ix] + timedelta(seconds=biggest_gap / 2), 0),
                    xytext=(0,50), textcoords="offset points",
                    weight="bold",
                    fontsize=10,
                    horizontalalignment="center",
                    verticalalignment="top")

    ax.legend()

    # remove y-axis and spines
    ax.yaxis.set_visible(False)
    ax.spines[["left", "top", "right"]].set_visible(False)

    # Shade in the region with client downtime
    ax.axvspan(result[0], result[1], alpha=0.12, facecolor="r")

    ax.margins(y=0.1)

    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.xaxis.set_major_locator(mdates.SecondLocator(interval=1))
    
    plt.show()

    return result