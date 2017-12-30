import transport

class Router:
    def __init__(self, config):

        self._running = False

        # Transport(self, name, ip, port, hns_ip, hns_port, 
        #                routing_table, dispather, neighbor, io)
        # transport_module = transport.Transport(config.hostname, config.self_addr.ip,
        #                         config.self_addr.port, None, None, None, None)

    def run(self):
        """
        start the router, if the router has already started, do nothing
        """
        if not self._running:
            self._running = True
            transport_module.run()

    def stop(self):
        """
        stop the working router, it no longer receiving or forwarding messages,
        if the router has stopped, do nothing
        """
        if self._running:
            self._running = False
            transport_module.stop()

    def send(destination, message):
        """
        send message
        Args:
            destination(str): hostname for the receiver
            message(str): message to send
        """
        # data = {
        #     'type': ...
        #     'data': message
        # }
        # transport_module.send(destination, data)

    def get_alive(self):
        """
        get living hosts on this router's perspective
        Returns:
            list<str>: a list of the living hosts
        """
        pass

    def update_neighbor(self, name, cost):
        """
        add new neighbor to this router or update the cost of a neighbor
        """
        pass

    def remove_neighbor(self, name):
        """
        remove a neighbor with specified hostname
        """
        pass