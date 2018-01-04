import threading
from .io import print_log

def log(message):
    print_log("[NeighborTable] {0}".format(message))

def info(message):
    log("[INFO] {0}".format(message))

def warning(message):
    log("[WARNING] {0}".format(message))

def error(message):
    log("[ERROR] {0}".format(message))

class NeighborTable:
    def __init__(self):
        self.table = dict()
        self.table_lock = threading.Lock()
        self.observers = list()

    def on_update(self, observer):
        self.observers.append(observer)

    def get(self):
        return self.table.copy()

    def get_cost(self, hostname):
        return self.table.get(hostname)

    def update(self, hostname, cost):
        self.__update(hostname, cost)
        self.__notify_all()

    def timeout(self, hostname):
        self.remove(hostname)

    def remove(self, hostname):
        with self.table_lock:
            self.remove(hostname)
        self.__notify_all()

    def __update(self, hostname, cost):
        info("set host '{0}' to cost '{1}'".format(hostname, cost))
        self.table[hostname] = cost

    def __remove(self, hostname):
        if self.get_cost(hostname) is None:
            info("host '{0}' doesn't exists in local table".format(hostname))
            return
        del self.table[hostname]
        info("host '{0}' deleted from local table".format(hostname))


    def __notify_all(self):
        for observer in self.observers:
            observer(self.get())
