#!/usr/bin/env python
# -*- coding: utf-8 -*-
from random import randint
from ant import Ant


class AntColony(object):
    """
    Ant colony representation
    """
    def __init__(self):
        self.ants = []

        self.shortest_path = None
        self.min_distance = float("inf")

    def reset_ants(self, graph):
        """
        reset ants
        """
        nodes = len(graph.nodes) - 1
        self.ants = [Ant(randint(0, nodes)) for _ in range(nodes)]


    def do_cycles(self, graph):
        self.reset_ants(graph=graph)
        for ant in self.ants:
            ant.do_cycle(graph=graph)
            graph.local_update_pheromones(passes=ant.get_passes())
            distance = ant.get_distance(graph=graph)
            if self.min_distance > distance:
                self.min_distance = distance
                self.shortest_path = ant.path[:]
