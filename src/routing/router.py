class Router:
    def __init__(self, config):
        pass

    def run(self):
        """
        start the router, if the router has already started, do nothing
        """
        pass

    def stop(self):
        """
        stop the working router, it no longer receiving or forwarding messages,
        if the router has stopped, do nothing
        """
        pass

    def send(destination, message):
        """
        send message
        Args:
            destination(str): hostname for the receiver
            message(str): message to send
        """
        pass

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