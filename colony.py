import random
from ant import Ant


class Colony(object):
    """
    The Colony class represents an ant colony with agents represented as ants
    """
    def __init__(self):
        self.ants = []
        self.shortest_path = None
        self.min_distance = None


    def perform_tours(self, instance):
        """
        Initialises ants within colony and makes the ants perform their tours around the tsp instance
        """

        # Create n ants with each one starting on a random node where n is the amount of nodes
        node_range = len(instance.nodes) - 1
        self.ants = [Ant(instance, random.randint(0, node_range)) for _ in range(node_range)]

        # Make each ant perform a tour around the instance
        for ant in self.ants:
            ant.perform_tour(instance)

            # Update pheromones locally
            self.local_update_pheromones(instance, ant.nodes_traversed())


            distance = ant.get_distance(instance)

            # Initialise the minimum distance as infinity if None
            if not(self.min_distance):
                self.min_distance = float('inf')

            # Update the colonys minimum distance and shortest path if the ant has found a shorter distance
            if self.min_distance > distance:

                self.min_distance = distance

                self.shortest_path = ant.path[:]

    def local_update_pheromones(self, instance, nodes_traversed):
        """
        Updates pheromones trails between nodes locally
        """
        # For each traversal, apply the decay onto the pheromone trail then add the local deposit
        for i, j in nodes_traversed:
            instance.pheromones[i][j] *= instance.decay
            instance.pheromones[i][j] += instance.local_deposit
