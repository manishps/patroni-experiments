# pylint: disable=missing-module-docstring
import os
import shutil
import time
from threading import Thread
from typing import Union
import click
from datetime import timedelta
from tqdm import tqdm
import jsonpickle

from pe.runner.agent import Node
from pe.runner.topology import Topology
from pe.data_generator.data_generator import DataGenerator
from pe.log_scraper.log_scraper import HAProxyScraper, PatroniScraper, PostgresScraper
from pe.plotter.plot_client_perspective import plot_client_perspective
from pe.plotter.plot_events import plot_events, plot_proxy_events
from pe.utils import ROOT_DIR


class Experiment:
    """
    A class to manage the experiment
    """

    def __init__(self, config_file: str, is_local: bool):
        self.config_file = config_file
        self.is_local = is_local
        self.topology = Topology(self.config_file, is_local=self.is_local)
        # pylint: disable-next=invalid-name
        self.dg: Union[DataGenerator, None] = None

    def clear_data(self):
        """
        Clears the data folders so that we can start writing fresh again.
        """
        shutil.rmtree(f"{ROOT_DIR}/data", ignore_errors=True)
        os.mkdir(f"{ROOT_DIR}/data")
        os.mkdir(f"{ROOT_DIR}/data/etcd")
        os.mkdir(f"{ROOT_DIR}/data/haproxy")
        os.mkdir(f"{ROOT_DIR}/data/patroni")
        os.mkdir(f"{ROOT_DIR}/data/postgres")

    def analyze(
        self, old_leader_node: Node, new_leader_node: Node, after_the_fact=False
    ):
        """
        Given the old leader and new leader, does the work of marshalling
        their logs locally and scraping them into events. Then plots.
        """
        # Do all the scraping
        get_patroni_log_path = lambda name: f"pe/data/patroni/{name}/patroni.log"
        get_postgres_log_path = lambda name: f"pe/data/postgres/{name}/logs"
        get_proxy_log_path = lambda: "pe/data/haproxy/proxy.log"

        old_patroni_scraper = PatroniScraper(
            get_patroni_log_path(old_leader_node.config.name), old=True
        )
        if not after_the_fact:
            old_patroni_scraper.recreate_locally(old_leader_node.api)
        old_patroni_events = old_patroni_scraper.scrape()

        old_postgres_scraper = PostgresScraper(
            get_postgres_log_path(old_leader_node.config.name), old=True
        )
        if not after_the_fact:
            old_postgres_scraper.recreate_locally(old_leader_node.api)
        old_postgres_events = old_postgres_scraper.scrape()

        new_patroni_scraper = PatroniScraper(
            get_patroni_log_path(new_leader_node.config.name), old=False
        )
        if not after_the_fact:
            new_patroni_scraper.recreate_locally(new_leader_node.api)
        new_patroni_events = new_patroni_scraper.scrape()

        new_postgres_scraper = PostgresScraper(
            get_postgres_log_path(new_leader_node.config.name), old=False
        )
        if not after_the_fact:
            new_postgres_scraper.recreate_locally(new_leader_node.api)
        new_postgres_events = new_postgres_scraper.scrape()

        proxy_scraper = HAProxyScraper(
            get_proxy_log_path(),
            old_leader_node.config.name,
            new_leader_node.config.name,
        )
        if not after_the_fact:
            proxy_scraper.recreate_locally(self.topology.proxy.api)
        proxy_events = proxy_scraper.scrape()
        initial_proxy_events = []
        failover_proxy_events = []
        is_in_initial = True
        for event in proxy_events:
            if is_in_initial:
                initial_proxy_events.append(event)
            else:
                failover_proxy_events.append(event)
            if event.readable == "Old leader marked as UP":
                is_in_initial = False

        # Find the client-perceived outage and plot it
        if not after_the_fact:
            assert self.dg is not None
            client_times = self.dg.get_successful_writes()
            raw_client_times = jsonpickle.encode(client_times)
            with open("client_times.out", "w") as fout:
                fout.write(raw_client_times)
            outage = plot_client_perspective(client_times)
        else:
            with open("client_times.out", "r") as fin:
                client_times = jsonpickle.decode(fin.read())
            outage = plot_client_perspective(client_times)

        # Set the basetime for numbering axes
        base_time = outage[0] + timedelta(seconds=-12)

        # Plot Patroni, then Postgres, then HAProxy
        plot_events(
            old_events=old_patroni_events,
            new_events=new_patroni_events,
            title="Patroni",
            outage=outage,
            base_time=base_time,
        )
        plot_events(
            old_events=old_postgres_events,
            new_events=new_postgres_events,
            title="Postgres",
            outage=outage,
            base_time=base_time,
        )
        plot_proxy_events(
            initial_events=initial_proxy_events,
            failover_events=failover_proxy_events,
            outage=outage,
            base_time=base_time,
        )

    def run(self):
        """
        Runs the experiment and returns the name of the old and new leader
        :return tuple[str, str]: representing (old_leader_name, new_leader_name)
        """
        self.clear_data()
        self.topology.boot(verbose=True)
        write_time = 10

        def show_bar():
            for _ in tqdm(range(write_time)):
                time.sleep(1)

        print("Waiting for leadership...")
        old_leader, _ = self.topology.nodes[0].get_roles()
        old_leader_node = [
            node for node in self.topology.nodes if node.config.name == old_leader
        ][0]

        self.dg = DataGenerator(
            self.topology.config.proxy.host, self.topology.config.proxy.proxy_port
        )

        print("Writing to DB...")
        self.dg.reset()
        self.dg.start_writing()
        show_bar()

        print("Issuing failover...")
        _, replicas = old_leader_node.get_roles()
        new_leader = replicas[0]
        new_leader_node = [
            node for node in self.topology.nodes if node.config.name == new_leader
        ][0]
        old_leader_node.failover(new_leader)
        new_leader_node.get_roles()
        print("Roles reestablished")

        print("Writing some more...")
        bar_thread = Thread(target=show_bar)
        bar_thread.start()
        self.dg.write_for_x_seconds_then_stop(10)
        bar_thread.join()

        self.analyze(old_leader_node, new_leader_node)

        print("Done writing")
        input("Enter anything to stop")
        self.topology.stop()


@click.command()
@click.argument("config-file")
@click.option("--is-local/--is-remote", default=False)
def experiment(config_file, is_local):
    """
    The logic behind the command line argument which runs the experiment
    """
    exp = Experiment(config_file=config_file, is_local=is_local)
    exp.run()
