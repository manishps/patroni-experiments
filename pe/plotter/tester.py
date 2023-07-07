from pe.runner.experiment import Experiment

if __name__ == "__main__":
    experiment = Experiment("config/topology.local.yml", is_local=True)
    old_node = [node for node in experiment.topology.nodes if node.config.name == "pe1"][0]
    new_node = [node for node in experiment.topology.nodes if node.config.name == "pe2"][0]
    experiment.analyze(old_node, new_node)

