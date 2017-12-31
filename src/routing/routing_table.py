import threading


class RoutingTable(object):
    def __init__(self, hostname):
        self._hostname = hostname

        # dynamic update, structure
        #
        # self._routing_table = {
        #   'destination': {
        #     'next': next-hop hostname,
        #     'cost': integer
        #   },
        #   ...
        # }
        self._routing_table = {
            self._hostname: {
                'next': self._hostname,
                'cost': 0
            }
        }
        self._routing_table_lock = threading.Lock()

    def update(self, table):
        self._routing_table_lock.acquire()
        try:
            self._routing_table = table
        finally:
            self._routing_table_lock.release()

    def get(self, destination):
        self._routing_table_lock.acquire()
        try:
            next_hop = self._routing_table[destination]['next']
        except KeyError:
            raise ValueError('hostname unreachable')
        finally:
            self._routing_table_lock.release()

        return next_hop

    def get_alive(self):
        self._routing_table_lock.acquire()
        try:
            alive_list = list(self._routing_table.keys())
        finally:
            self._routing_table_lock.release()

        return alive_list
