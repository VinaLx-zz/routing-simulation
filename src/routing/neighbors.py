NEIGHBOR_TYPE = "neighbor"
NEIGHBOR_TIMEOUT = 500

class Neighbors:
    def __init__(self, transport, dispatcher):
        self.neighbors = {}
        self.transport = transport
        dispatcher.register(NEIGHBOR_TYPE, self)

    def receive(self, source, data):
        """
        receive data from Neighbor module of another part
        Args:
            data (Dict): json data
                {
                    // todo
                }
        """
        pass

    def update(self, hostname: str, cost: int):
        """
        asynchronizely update neighbor cost of `hostname` to `cost`
        """
        pass

    def delete(self, hostname: str):
        """
        asynchronizely delete neighbor named `hostname`
        """
        pass

    @classmethod
    def is_ack(cls, data):
        return data == 0

    def __ack(self, to):
        self.__send(to, 0, True)

    def __send(self, to, data, new=False):
        self.transport.send(to, {
            "type": NEIGHBOR_TYPE,
            "data": data
        }, new)

    def get(self):
        """
        get a copy of the neighbor table:
        Returns:
            Dict[str, int]: a dictionary mapping host name to cost
        """
        return self.neighbors
