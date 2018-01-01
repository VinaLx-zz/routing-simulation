import threading
from .io import print_log

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


def log(message):
    print_log("[Neighbors] {0}".format(message))

def info(message):
    log("[INFO] {0}".format(message))


def error(message):
    log("[ERROR] {0}".format(message))


class Neighbors:

    def __init__(self, transport, dispatcher):
        dispatcher.register(NEIGHBOR_TYPE, self)

        self.neighbors = dict()
        self.pending = dict()

        self.transport = transport

        self.table_lock = threading.Lock()
        self.pending_lock = threading.Lock()
        self.observers = list()

    def receive(self, source, cost):
        """
        receive data from Neighbor module of another part
        Args:
            cost (int): a integer indicates the cost change
        """

        info("receiving cost '{0}' from host '{1}'".format(cost, source))
        if not Neighbors.validate(cost):
            return

        if self.pending.get(source) is None:
            self.__send(source, cost)  # ack
        else:
            self.__success(source)
        self.__update_unsafe(source, cost)
        self.__notify_all()

    def on_update(self, callback):
        self.observers.append(callback)

    def update(self, hostname: str, cost: int, success=noop, fail=noop):
        """
        asynchronizely update neighbor cost of `hostname` to `cost`
        """
        info(
            "updating neighbor state, host: '{0}', cost: '{1}'".format(
                hostname,
                cost))

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
        info("deleting host '{0}'".format(hostname))
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

        info("getting neighbor table, content: {0}".format(self.neighbors))
        # return self.neighbors.copy()
        return {h: self.neighbors[h] for h in self.neighbors if self.neighbors[h] != -1}

    def __abort(self, hostname, fail):
        if not del_with_lock(self.pending, hostname, self.pending_lock):
            return
        info("timeout for host '{0}', aborting action".format(hostname))
        fail()

    def __success(self, hostname):
        self.pending_lock.acquire()

        if self.pending.get(hostname):
            info("reply from host '{0}' received".format(hostname))
            self.pending[hostname]()
            del self.pending[hostname]

        self.pending_lock.release()

    def __update_unsafe(self, hostname, cost):
        self.table_lock.acquire()

        if cost == -1:
            if self.get_cost(hostname) is None:
                info("host '{0}' doesn't exists in local table" % hostname)
                return
            del self.neighbors[hostname]
            info("host '{0}' deleted from local table" % hostname)
        else:
            self.neighbors[hostname] = cost
            info("set host '{0}' to cost {1}".format(hostname, cost))

        self.table_lock.release()

    def __notify_all(self):
        for observer in self.observers:
            observer(self.get())

    @classmethod
    def validate(cls, data):
        return isinstance(data, int) and data >= -1

    def __send(self, to, data, new=True):
        info("sending data '{0}' to host '{1}'".format(data, to))
        self.transport.send(to, {
            "type": NEIGHBOR_TYPE,
            "data": data
        }, new)
