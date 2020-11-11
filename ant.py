from random import random

class Ant(object):
    """
    The Ant class represent an agent within the aco algorithm
    """
    def __init__(self, instance, start_node):
        self.instance = instance
        self.path = [start_node]


    def sum_others(self, i, j, avail_nodes):
        """
        Returns the denominator of the state traversal equation
        """
        set_copy = avail_nodes.copy()
        set_copy.remove(j)
        sum = 0
        for j in set_copy:
            sum += (self.instance.pheromones[i][j] ** self.instance.alpha) * (self.instance.distances[i][j] ** -self.instance.beta)

        return sum


    def nodes_traversed(self):
        """
        Returns list of edges traversed by the ant
        """
        length = len(self.path)
        return [tuple(sorted((self.path[i], self.path[(i + 1) % length]), reverse=True)) for i in range(length)]

    def get_distance(self, instance):
        """
        Returns distance traveled by the ant
        """
        return instance.get_path_distance(self.path)

    def get_probability(self, i, j, avail_nodes):
        """
        Returns the probability of the ant choosing node j as its next traversal.
        """
        return ((self.instance.pheromones[i][j] ** self.instance.alpha)
                * (self.instance.distances[i][j] ** -self.instance.beta)/self.sum_others(i, j, avail_nodes))

    def traverse(self, instance, avail_nodes):
        """
        An ant chooses a node to travel to based on a probability formula using
        user supplied params, pheromone trail levels and distances
        """

        # If on the last node available, just travel to it
        if len(avail_nodes) == 1:
            self.path.append(avail_nodes.pop())
            return

        # Initialise running total of probabilities
        total = 0
        probabilities = {}

        # Get the probabilities of each available node
        for node_index in avail_nodes:
            probabilities[node_index] = self.get_probability(self.path[-1], node_index, avail_nodes)
            total += probabilities[node_index]

        # IMPROVEMENT added randomness to picking nodes
        threshold = random()
        probability = 0

        # For each available node, the probability that it is chosen is based on
        # its calculated probability and a random threshold being below this
        # probability value, thus a node with a large probability of being chosen
        # will add a large number onto the probability thus increasing the chance of
        # the threshold being below it and it then being chosen.
        for node_index in avail_nodes:
            probability += probabilities[node_index] / total
            if threshold < probability:
                self.path.append(node_index)
                return
        self.path.append(avail_nodes.pop())

    def perform_tour(self, instance):
        """
        Make the ant perform a traversal of the nodes.
        """
        # Initialise a set of number ranging from 0 to the amount of instance nodes -1
        all_nodes = set(range(len(instance.nodes)))

        # Remove starting node
        avail_nodes = all_nodes - set(self.path)

        # Traverse through nodes whilst they are available
        while avail_nodes:
            self.traverse(instance, avail_nodes)
            avail_nodes = all_nodes - set(self.path)
