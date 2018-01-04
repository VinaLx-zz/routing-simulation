from .transport import Transport
from .routing_table import RoutingTable
from .dispatcher import DataDispatcher
from .algorithm import DV, LS, CentralizedMember, CentralizedController
from .neighbors import Neighbors
from .config import Algorithm
from .message import Message
from .neighbor_table import NeighborTable


class Router:
    def __init__(self, config):

        self._running = False
        self.hostname = config.hostname

        self.routing_table = RoutingTable(config.hostname)
        self.dispatcher = DataDispatcher()

        self.neighbor_table = NeighborTable()
        self.transport = Transport(
            config.hostname, config.self_addr.ip, config.self_addr.port,
            config.hns_addr.ip, config.hns_addr.port,
            self.routing_table, self.dispatcher, self.neighbor_table)
        self.neighbors = Neighbors(
            self.transport, self.dispatcher, self.neighbor_table)

        self.algorithm = self.__get_algorithm(config)

        self.message = Message(self.transport, self.dispatcher)

    def __get_algorithm(self, config):
        if config.algorithm == Algorithm.LS_CENTRALIZE:
            return CentralizedMember(
                config.controller,
                config.hostname,
                self.transport,
                self.routing_table,
                self.neighbor_table,
                self.dispatcher,
                config.update_interval,
                config.dead_timeout)
        else:
            return {
                Algorithm.DV: DV,
                Algorithm.LS: LS,
                Algorithm.LS_CONTROL: CentralizedController}[
                config.algorithm](
                config.hostname,
                self.transport,
                self.routing_table,
                self.neighbor_table,
                self.dispatcher,
                config.update_interval,
                config.dead_timeout)

    def run(self):
        """
        start the router, if the router has already started, do nothing
        """
        if not self._running:
            self._running = True
            self.transport.run()
            self.algorithm.run()

    def stop(self):
        """
        stop the working router, it no longer receiving or forwarding messages,
        if the router has stopped, do nothing
        """
        if self._running:
            self._running = False
            self.transport.stop()
            self.algorithm.stop()

    def send(self, destination, message):
        """
        send message
        Args:
            destination(str): hostname for the receiver
            message(str): message to send
        """
        self.message.send(destination, message)

    def get_alive(self):
        """
        get living hosts on this router's perspective
        Returns:
            list<str>: a list of the living hosts
        """
        return self.routing_table.get_alive()

    def update_neighbor(self, name, cost):
        """
        add new neighbor to this router or update the cost of a neighbor
        """
        self.neighbors.update(name, cost)

    def remove_neighbor(self, name):
        """
        remove a neighbor with specified hostname
        """
        self.neighbors.delete(name)

    def get_routing_table(self):
        """
        get routing table on this routers' perspective
        Returns:
            dict: {
                destination: {
                    next: str,
                    cost: int
                }
            }
        """
        return self.routing_table.get_all()

    def get_neighbor_table(self):
        """
        get neighbor of this router
        Returns:
            dict[str, int]: a mapping maps hostname of neighbor to the cost to it
        """
        return self.neighbor_table.get()
