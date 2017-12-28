import threading

NEIGHBOR_TYPE = "neighbor"
NEIGHBOR_TIMEOUT = 5


def noop():
    pass

def del_with_lock(d, k, l):
    ret = False
    l.acquire()
    if d.get(k) is not None:
        del d[k]
        ret = True
    l.release()
    return ret

class Neighbors:

    def __init__(self, transport, dispatcher):
        dispatcher.register(NEIGHBOR_TYPE, self)

        self.neighbors = dict()
        self.pending = dict()

        self.transport = transport

        self.table_lock = threading.Lock()
        self.pending_lock = threading.Lock()

    def receive(self, source, cost):
        """
        receive data from Neighbor module of another part
        Args:
            cost (int): a integer indicates the cost change
        """
        if not Neighbors.validate(cost):
            return

        if self.pending.get(source) is None:
            self.__send(source, cost)  # ack
        else:
            self.__success(source)
        self.__update_unsafe(source, cost)

    def update(self, hostname: str, cost: int, success=noop, fail=noop):
        """
        asynchronizely update neighbor cost of `hostname` to `cost`
        """
        timer = threading.Timer(
            NEIGHBOR_TIMEOUT, self.__abort, args=(hostname, fail))

        def success_callback():
            timer.cancel()
            success()
        self.pending[hostname] = success_callback
        self.__send(hostname, cost)
        timer.start()

    def delete(self, hostname: str, success=noop, fail=noop):
        """
        asynchronizely delete neighbor named `hostname`
        """
        if self.get_cost(hostname) is None:
            return
        self.update(hostname, -1, success=success, fail=fail)

    def get_cost(self, hostname):
        return self.neighbors.get(hostname)

    def get(self):
        """
        get a copy of the neighbor table:
        Returns:
            Dict[str, int]: a dictionary mapping host name to cost
        """
        return self.neighbors.copy()


    def __abort(self, hostname, fail):
        if not del_with_lock(self.pending, hostname, self.pending_lock):
            return
        fail()

    def __success(self, hostname):
        self.pending_lock.acquire()

        if self.pending.get(hostname):
            self.pending[hostname]()
            del self.pending[hostname]

        self.pending_lock.release()

    def __update_unsafe(self, hostname, cost):
        self.table_lock.acquire()

        if self.get_cost(hostname) is None:
            return
        if cost == -1:
            del self.neighbors[hostname]
        else:
            self.neighbors[hostname] = cost

        self.table_lock.release()

    @classmethod
    def validate(cls, data):
        return isinstance(data, int) and data >= -1

    def __send(self, to, data, new=True):
        self.transport.send(to, {
            "type": NEIGHBOR_TYPE,
            "data": data
        }, new)
