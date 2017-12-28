class Neighbors:
    def __init__(self, transport, dispatcher):
        self.neighbors = {}
        self.transport = transport

    def receive(self, data):
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
        update neighbor cost of `hostname` to `cost`
        """
        pass

    def delete(self, hostname: str):
        """
        delete neighbor named `hostname`
        Returns:
            bool: true if a successful deletion, false otherwise
        """
        pass

    def get(self):
        """
        get a copy of the neighbor table:
        Returns:
            Dict[str, int]: a dictionary mapping host name to cost
        """
        return self.neighbors
