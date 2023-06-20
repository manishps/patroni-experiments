# Patroni Experiments

This repository contains code that lets us run fully automated tests to benchmark failover in a real HA deployment in Patroni. It produces results like the below, where key events during initialization, failover, and recovery can be seen in a clear linear timeline.


![Basic Results](docs/images/Preliminary.png)

## Goals

1. Create an easy-to-use, consistent experiment runner which can record failover metrics for arbitrary configurations.
2. Develop intuition about core steps during a failover.
3. Document this system so it can be used by others.

## Docs

Docs are split up into files in the `docs` folder for readability. There you'll find information on...

### [Setup](docs/setup.md)

How to run these experiments on your own

### [Architecture](docs/architecture.md)

Diagrams and explanations describing the system and how it delivers clean, consistent results.

### [Results](docs/results.md)

A summary of important observations regarding failover latency, especially as it relates to key configuration parameters.
