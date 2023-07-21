from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from pe.log_scraper.log_scraper import Event, PatroniScraper, PostgresScraper

ZERO_TIME = datetime(2023, 1, 1, 0, 0, 0, 0)


def plot_events(
    old_events: list[Event],
    new_events: list[Event],
    title: str,
    outage: tuple[datetime, datetime],
    base_time: datetime,
):
    """
    Plots a series of events relating to one of the underlying technologies
    :param list[Event] old_events: The events (time, readable, raw) observed by the old leader
    :param list[Event] new_events: The events (time, readable, raw) observed by the new leader
    :param str title: The title of the graphs
    :param tuple[datetime, datetime] outage: The timestamped window of when the client lost data
    :param datetime base_time: When writing ticks, the basetime (0), so things are reasonable
        magnitude and consistent
    """
    plt.style.use("seaborn-pastel")
    # First extract the information from the events and generate the staggers
    old_staggers = [x for x in range(1, 8)]
    old_labels = [event.readable for event in old_events]
    old_levels = [old_staggers[ix % len(old_staggers)] for ix in range(len(old_labels))]
    old_times = [e.timestamp for e in old_events]
    new_staggers = [x for x in range(1, 8)]
    new_labels = [event.readable for event in new_events]
    new_levels = [new_staggers[ix % len(new_staggers)] for ix in range(len(new_labels))]
    new_times = [e.timestamp for e in new_events]
    # Package into "chunks" (to be iterated over and graphed)
    old_chunks = sorted(zip(old_labels, old_levels, old_times), key=lambda e: e[2])
    new_chunks = sorted(zip(new_labels, new_levels, new_times), key=lambda e: e[2])

    # Generate the axes
    fig, [old_ax, new_ax] = plt.subplots(
        2,
        1,
        figsize=(8, 6),
        layout="constrained",
        dpi=300,
        gridspec_kw=dict(
            left=0.1, bottom=0.12, right=0.95, top=0.93, wspace=0.4, hspace=0.6
        ),
    )
    fig.tight_layout()
    fig.subplots_adjust(wspace=0, hspace=0.5)

    # Decide on the ticks
    min_x = min(old_times + new_times + list(outage))
    max_x = max(old_times + new_times + list(outage))
    ticks: list[datetime] = []
    padding = 0.9
    granularity = 0.3
    tick = min_x + timedelta(seconds=-padding)
    while tick <= max_x + timedelta(seconds=padding):
        ticks.append(tick)
        tick += timedelta(seconds=granularity)

    # TLDR: Basically just uses the packaged chunks and separate axes to repeat the same plotting
    # Process for the graphs of the two nodes
    for chunks, ax, title in [
        (old_chunks, old_ax, f"{title} Events In the Old Leader Node"),
        (new_chunks, new_ax, f"{title} Events In the New Leader Node"),
    ]:
        # Generate the circles, lines, and labels
        levels = [e[1] for e in chunks]
        times = [e[2] for e in chunks]
        ax.scatter(times, levels, marker="<")
        ax.vlines(times, 0, levels)
        ax.plot(times, np.zeros_like(times), "-o", color="k", markerfacecolor="w")
        for ix, (r, l, d) in enumerate(chunks):
            ax.annotate(
                f"{ix}. {r}",
                xy=(d, l),
                xytext=(-5.0, -5.0),
                textcoords="offset points",
                horizontalalignment="right",
                verticalalignment="bottom",
            )
        # Shade in the region with client downtime
        ax.axvspan(
            outage[0],
            outage[1],
            alpha=0.12,
            facecolor="r",
            label="Outage from\nClient's Perspective",
        )
        # Consistent times and pretty-ness
        ax.set_xlim(min_x, max_x)
        ax.set_xticks(ticks)
        ax.set_xticklabels(
            [(ZERO_TIME + (time - base_time)).strftime("%S.%f")[:-4] for time in ticks]
        )
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        # Remove y-axis and spines
        ax.yaxis.set_visible(False)
        ax.spines[["left", "top", "right"]].set_visible(False)
        ax.margins(y=0.1)
        # Shrink current axis by 20% (to make room for legend on right side)
        box = ax.get_position()
        ax.set_position([box.x0 + box.width * 0.2, box.y0, box.width * 0.8, box.height])
        font = {"size": 15}
        ax.set_title(title, fontdict=font)
        ax.set_xlabel("Time(s)")

    # All done! Display to user
    handles, labels = new_ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="center left")
    fname = title.replace(" ", "_")
    plt.savefig(f"{fname}.png")


def plot_proxy_events(
    initial_events: list[Event],
    failover_events: list[Event],
    outage: tuple[datetime, datetime],
    base_time: datetime,
):
    """
    Plots a series of events relating to one of the underlying technologies
    :param list[Event] old_events: The events (time, readable, raw) observed by the old leader
    :param list[Event] new_events: The events (time, readable, raw) observed by the new leader
    :param str title: The title of the graphs
    :param tuple[datetime, datetime] outage: The timestamped window of when the client lost data
    :param datetime base_time: The basetime (0) on x-axis for reasonable magnitude and consistency
    """
    plt.style.use("seaborn-pastel")
    # First extract the information from the events and generate the staggers
    initial_staggers = [x for x in range(1, 8)]
    initial_labels = [event.readable for event in initial_events]
    initial_levels = [
        initial_staggers[ix % len(initial_staggers)]
        for ix in range(len(initial_labels))
    ]
    initial_times = [e.timestamp for e in initial_events]
    failover_staggers = [x for x in range(1, 8)]
    failover_labels = [event.readable for event in failover_events]
    failover_levels = [
        failover_staggers[ix % len(failover_staggers)]
        for ix in range(len(failover_labels))
    ]
    failover_times = [e.timestamp for e in failover_events]
    # Package into "chunks" (to be iterated over and graphed)
    initial_chunks = sorted(
        zip(initial_labels, initial_levels, initial_times), key=lambda e: e[2]
    )
    failover_chunks = sorted(
        zip(failover_labels, failover_levels, failover_times), key=lambda e: e[2]
    )

    # TLDR: Basically just uses the packaged chunks and separate axes to repeat the same plotting
    # Process for the graphs of the two nodes
    for chunks, title in [
        (initial_chunks, f"Initial Proxy Events"),
        (failover_chunks, f"Proxy Events During Failover"),
    ]:
        fig, ax = plt.subplots(
            1,
            1,
            figsize=(8, 3),
            layout="tight",
            dpi=300,
            gridspec_kw=dict(
                left=0.12, bottom=0.25, right=0.95, top=0.85, wspace=0.2, hspace=0.2
            ),
        )
        # Generate the circles, lines, and labels
        levels = [e[1] for e in chunks]
        times = [e[2] for e in chunks]

        # Decide on the ticks
        min_x = min(times)
        max_x = max(times)
        if "Failover" in title:
            min_x = min(min_x, outage[0])
            max_x = max(max_x, outage[1])

        ticks: list[datetime] = []
        padding = 1.2
        granularity = 0.6
        tick = min_x + timedelta(seconds=-padding)
        while tick <= max_x + timedelta(seconds=padding):
            ticks.append(tick)
            tick += timedelta(seconds=granularity)

        ax.scatter(times, levels, marker="<")
        ax.vlines(times, 0, levels)
        ax.plot(times, np.zeros_like(times), "-o", color="k", markerfacecolor="w")
        for ix, (r, l, d) in enumerate(chunks):
            ax.annotate(
                f"{ix}. {r}",
                xy=(d, l),
                xytext=(-5.0, -5.0),
                textcoords="offset points",
                horizontalalignment="right",
                verticalalignment="bottom",
            )
        # Shade in the region with client downtime
        ax.axvspan(
            outage[0],
            outage[1],
            alpha=0.12,
            facecolor="r",
            label="Outage from\nClient's Perspective",
        )
        # Consistent times and pretty-ness
        ax.set_xlim(min_x, max_x)
        ax.set_xticks(ticks)
        ax.set_xticklabels(
            [(ZERO_TIME + (time - base_time)).strftime("%S.%f")[:-4] for time in ticks]
        )
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        # Remove y-axis and spines
        ax.yaxis.set_visible(False)
        ax.spines[["left", "top", "right"]].set_visible(False)
        ax.margins(y=0.1)
        # Shrink current axis by 20% (to make room for legend on right side)
        box = ax.get_position()
        ax.set_position([box.x0 + box.width * 0.2, box.y0, box.width * 0.8, box.height])
        font = {"size": 15}
        ax.set_title(title, fontdict=font)
        ax.set_xlabel("Time(s)")

        # All done! Display to user
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper left")
        fig.savefig(f"{title.replace(' ', '_')}.png")


if __name__ == "__main__":
    # pylint: disable-next=unnecessary-lambda-assignment
    get_patroni_log_path = lambda name: f"pe/data/patroni/{name}/patroni.log"
    # pylint: disable-next=unnecessary-lambda-assignment
    get_postgres_log_path = lambda name: f"pe/data/postgres/{name}/logs"

    old_patroni_scraper = PatroniScraper(get_patroni_log_path("pe1"), old=True)
    old_patroni_events = old_patroni_scraper.scrape()

    old_postgres_scraper = PostgresScraper(get_postgres_log_path("pe1"), old=True)
    old_postgres_events = old_postgres_scraper.scrape()

    new_patroni_scraper = PatroniScraper(get_patroni_log_path("pe2"), old=False)
    new_patroni_events = new_patroni_scraper.scrape()

    new_postgres_scraper = PostgresScraper(get_postgres_log_path("pe2"), old=False)
    new_postgres_events = new_patroni_scraper.scrape()

    default_outage = old_patroni_events[1].timestamp, old_patroni_events[-1].timestamp

    plot_events(
        old_patroni_events,
        new_patroni_events,
        "Patroni",
        default_outage,
        datetime.now(),
    )
