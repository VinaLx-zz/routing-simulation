import threading
import copy
import time
from .io import print_log

ALGORITHM_TYPE = "algorithm"


def log(message):
    print_log("[Algorithm] {0}".format(message))


def info(message):
    log("[INFO] {0}".format(message))


def error(message):
    log("[ERROR] {0}".format(message))


class Algorithm(object):
    def __init__(self, hostname, transport, routing_table, neighbor,
                 dispatcher, update_interval=30, timeout=180):
        self._hostname = hostname
        self._interval = update_interval
        self._timeout = timeout

        self._transport = transport
        self._routing = routing_table
        self._neighbor = neighbor

        self._timer_thread = None
        self._check_alive_thread = None

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

        # Link-State
        #
        # self._link_state = {
        #   "host_1": {
        #     "other_host1": cost_1_1,
        #     "other_host2": cost_1_2,
        #     ...
        #   },
        #   ...
        # }
        #
        self._link_state = {}
        self._link_state_lock = threading.Lock()

        # Alive-state
        #
        # self._alive_table = {
        #   "hostname": time,
        #   ...
        # }
        self._alive_table = {}
        self._alive_table_lock = threading.Lock()

        dispatcher.register(ALGORITHM_TYPE, self)
        self._neighbor.on_update(self._neighbor_update)
        self._check_timeout()

    def receive(self, src, data):
        pass

    def run(self):
        pass

    def stop(self):
        if self._timer_thread is not None:
            self._timer_thread.cancel()
            self._timer_thread = None

        if self._check_alive_thread is not None:
            self._check_alive_thread.cancel()
            self._check_alive_thread = None

    def _push_to_routing_model(self, lock=True):
        if lock is True:
            with self._routing_table_lock:
                self._routing.update(self._routing_table)
        else:
            self._routing.update(self._routing_table)

    def _neighbor_update(self, neighbor_table):
        log('new neighbor table: {}'.format(neighbor_table))
        with self._routing_table_lock:
            for hostname in neighbor_table:
                if neighbor_table[hostname] != -1:
                    self._routing_table[hostname] = {
                        'next': hostname,
                        'cost': neighbor_table[hostname]
                    }
                    self._routing.update_one(hostname, hostname, neighbor_table[hostname])

    def _neighbor_timeout(self, dead_hostnames):
        for hostname in dead_hostnames:
            self._neighbor.timeout(hostname)

    def _check_timeout(self):
        pass

class DV(Algorithm):
    def __init__(self, hostname, transport, routing_table, neighbor,
                 dispatcher, update_interval=30, timeout=180):
        super(DV, self).__init__(hostname,
                                 transport,
                                 routing_table,
                                 neighbor,
                                 dispatcher,
                                 update_interval,
                                 timeout)
        self._neighbor_routing = {}
        self._neighbor_routing_lock = threading.Lock()

    def receive(self, src, data):
        if self._have_timeout(data) is True:
            info('Discard data for timeout hostname in routing table')
            return

        log('receive routing data from {}: {}'.format(src,
                                                      data['routing']))
        dead_hostnames = self._update_alive_get_dead(data['alive'])

        with self._routing_table_lock:
            with self._neighbor_routing_lock:
                self._update_neighbor_routing(src, data['routing'])
                destinations = self._get_destinations()

                info('neighbor routing: {}'.format(self._neighbor_routing))

                for dest_host in destinations:
                    min_next, min_cost = None, -1

                    for neighbor in self._neighbor_routing:
                        if dest_host in self._neighbor_routing[neighbor]:
                            indirect_cost = self._neighbor_routing[self._hostname][neighbor]['cost'] + \
                                            self._neighbor_routing[neighbor][dest_host]['cost']

                            if min_next is None or indirect_cost < min_cost:
                                min_cost = indirect_cost
                                min_next = neighbor if neighbor != self._hostname else dest_host

                    self._routing_table[dest_host] = {
                        'next': min_next,
                        'cost': min_cost
                    }


            log('routing table: {}'.format(self._routing_table))

        self._push_to_routing_model()

    def run(self):
        self._notice_neighbor()

        self._timer_thread = threading.Timer(self._interval, DV.run, args=(self,))
        self._timer_thread.start()

    def _neighbor_update(self, neighbor_table):
        log('new neighbor table: {}'.format(neighbor_table))

    def _have_timeout(self, data):
        current_time = time.time()
        dead_hostnames = []

        for hostname in data['alive']:
            if current_time - data['alive'][hostname] > self._timeout:
                dead_hostnames.append(hostname)

        for hostname in data['routing']:
            if hostname in dead_hostnames:
                return True

        return False

    def _update_alive_get_dead(self, alive_table):
        dead_hostnames = []
        current_time = time.time()

        with self._alive_table_lock:
            self._alive_table[self._hostname] = current_time
            for hostname in alive_table:
                if hostname not in self._alive_table:
                    self._alive_table[hostname] = alive_table[hostname]
                elif alive_table[hostname] > self._alive_table[hostname]:
                    self._alive_table[hostname] = alive_table[hostname]

            dead_hostnames = [hostname
                              for hostname in self._alive_table
                              if current_time - self._alive_table[hostname] > self._timeout]

        return dead_hostnames

    def _get_destinations(self):
        destinations = set()

        for neighbor in self._neighbor_routing:
            destinations.add(neighbor)
            for hostname in self._neighbor_routing[neighbor]:
                destinations.add(hostname)

        return list(destinations)

    def _update_neighbor_routing(self, src, neighbor_routing):
        self._neighbor_routing[src] = neighbor_routing
        self._neighbor_routing[self._hostname] = {
            self._hostname: {
                'next': self._hostname,
                'cost': 0
            }
        }

        neighbor_table = self._neighbor.get()

        for hostname in neighbor_table:
            self._neighbor_routing[self._hostname][hostname] = {
                'next': hostname,
                'cost': neighbor_table[hostname]
            }

    def _notice_neighbor(self):
        current_time = time.time()
        dead_hostnames = []

        send_data = {
            'type': ALGORITHM_TYPE,
            'data': {}
        }

        with self._alive_table_lock:
            self._alive_table[self._hostname] = time.time()

            for hostname in self._alive_table:
                if current_time - self._alive_table[hostname] > self._timeout:
                    dead_hostnames.append(hostname)

            send_data['data']['alive'] = self._alive_table

        self._neighbor_routing_timeout(dead_hostnames)

        with self._routing_table_lock:
            if len(dead_hostnames) != 0:
                log('dead hostnames: {}'.format(dead_hostnames))
                self._neighbor_timeout(dead_hostnames)
                self._reset_default_routing()
                self._push_to_routing_model(False)

            send_data['data']['routing'] = copy.deepcopy(self._routing_table)

        for hostname in list(self._neighbor.get().keys()):
            self._transport.send(hostname, send_data, True)
            log('send routing data to {}: {}'.format(hostname, send_data['data']['routing']))

    def _reset_default_routing(self):
        self._routing_table = {
            self._hostname: {
                'next': self._hostname,
                'cost': 0
            }
        }
        neighbor_table = self._neighbor.get()

        for hostname in neighbor_table:
            self._routing_table[hostname] = {
                'next': hostname,
                'cost': neighbor_table[hostname]
            }

    def _neighbor_routing_timeout(self, dead_hostnames):
        with self._neighbor_routing_lock:
            for hostname in dead_hostnames:
                if hostname in self._neighbor_routing:
                    self._neighbor_routing.pop(hostname)

class LS(Algorithm):
    def receive(self, src, data):
        dead_hostnames = []
        neighbor_table = self._neighbor.get()

        with self._alive_table_lock:
            current_time = time.time()
            self._alive_table[self._hostname] = current_time
            # update alive table
            for hostname in data['alive']:
                if hostname not in self._alive_table:
                    self._alive_table[hostname] = data['alive'][hostname]
                elif data['alive'][hostname] > self._alive_table[hostname]:
                    self._alive_table[hostname] = data['alive'][hostname]

            # collect dead hostnames
            for hostname in self._alive_table:
                if current_time - self._alive_table[hostname] > self._timeout:
                    dead_hostnames.append(hostname)

            for hostname in dead_hostnames:
                self._alive_table.pop(hostname)

        if len(dead_hostnames) != 0:
            log('dead hostnames: {}'.format(dead_hostnames))
            self._neighbor_timeout(dead_hostnames)

        self._routing_table_lock.acquire()
        self._link_state_lock.acquire()
        try:
            self._link_state[self._hostname] = neighbor_table
            for hostname in neighbor_table:
                if hostname not in self._link_state:
                    self._link_state[hostname] = {}

            self._link_state[data['source']] = data['neighbor']
            for hostname in data['neighbor']:
                if hostname not in self._link_state:
                    self._link_state[hostname] = {}

            for hostname in dead_hostnames:
                if hostname in self._link_state:
                    self._link_state.pop(hostname)

            for hostname in self._link_state:
                self._link_state[hostname] = {
                    k: v for k, v in self._link_state[hostname].items()
                    if k not in dead_hostnames
                }

            prev_table = self._dijkstra()
            self._update_routing(prev_table)
            self._routing.update(copy.deepcopy(self._routing_table))

            log('receive routing data from {}: {}'.format(data['source'],
                                                          data['neighbor']))
            log('update routing table: {}'.format(self._routing_table))
        finally:
            self._link_state_lock.release()
            self._routing_table_lock.release()

        self._push_to_routing_model()

    def run(self):
        neighbor_table = self._neighbor.get()

        with self._alive_table_lock:
            send_data = {
                'type': ALGORITHM_TYPE,
                'data': {
                    'source': self._hostname,
                    'neighbor': neighbor_table,
                    'alive': copy.deepcopy(self._alive_table)
                }
            }

        self._transport.broadcasting(send_data)
        log('send neighbor information: {}'.format(send_data['data']['neighbor']))

        self._timer_thread = threading.Timer(self._interval, LS.run, args=(self,))
        self._timer_thread.start()

    def _dijkstra(self):
        """Dijkstra algorithm

        update routing table

        must be wrapped with the link state lock

        Returns:
            prev_table: shortest path table
        """

        visited = [self._hostname]
        prev_table = {
            self._hostname: {
                'prev': None,
                'cost': 0
            }
        }

        for hostname in self._link_state[self._hostname]:
            prev_table[hostname] = {
                'prev': self._hostname,
                'cost': self._link_state[self._hostname][hostname]
            }

        for hostname in self._link_state:
            if hostname not in prev_table:
                prev_table[hostname] = {
                    'prev': None,
                    'cost': -1
                }

        while True:
            nearest_hostname = None
            nearest_cost = -1

            # find w not in visited that D(w) is a minimum
            for hostname in prev_table:
                if hostname not in visited and \
                                prev_table[hostname]['cost'] != -1 and \
                        (nearest_cost == -1 or
                                 prev_table[hostname]['cost'] < nearest_cost):
                    nearest_hostname = hostname
                    nearest_cost = prev_table[hostname]['cost']

            if nearest_hostname is None:
                break

            visited.append(nearest_hostname)
            for hostname in self._link_state[nearest_hostname]:
                if hostname not in prev_table or \
                        (hostname not in visited and \
                                 (prev_table[hostname]['cost'] == -1 or
                                          prev_table[hostname]['cost'] > nearest_cost + \
                                              self._link_state[nearest_hostname][hostname])):
                    prev_table[hostname] = {
                        'prev': nearest_hostname,
                        'cost': nearest_cost + self._link_state[nearest_hostname][hostname]
                    }

        return prev_table

    def _update_routing(self, prev_table):
        """update routing table

        must be wrapped with the routing table lock

        Args:
            prev_table: calculated by _dijkstra
        """

        self._routing_table.clear()
        self._routing_table[self._hostname] = {
            'next': self._hostname,
            'cost': 0
        }

        for destination in prev_table:
            last_hop = destination

            if prev_table[last_hop]['prev'] is None:
                continue
            while prev_table[last_hop]['prev'] != self._hostname:
                last_hop = prev_table[last_hop]['prev']

            self._routing_table[destination] = {
                'next': last_hop,
                'cost': prev_table[destination]['cost']
            }

    def _check_timeout(self):
        dead_hostnames = []
        neighbor_table = self._neighbor.get()

        with self._alive_table_lock:
            current_time = time.time()
            self._alive_table[self._hostname] = current_time

            # collect dead hostnames
            for hostname in self._alive_table:
                if current_time - self._alive_table[hostname] > self._timeout:
                    dead_hostnames.append(hostname)

            for hostname in dead_hostnames:
                self._alive_table.pop(hostname)

        if len(dead_hostnames) != 0:
            log('dead hostnames: {}'.format(dead_hostnames))
            self._neighbor_timeout(dead_hostnames)

        self._routing_table_lock.acquire()
        self._link_state_lock.acquire()
        try:
            self._link_state[self._hostname] = neighbor_table
            for hostname in neighbor_table:
                if hostname not in self._link_state:
                    self._link_state[hostname] = {}

            for hostname in dead_hostnames:
                if hostname in self._link_state:
                    self._link_state.pop(hostname)

            for hostname in self._link_state:
                self._link_state[hostname] = {
                    k: v for k, v in self._link_state[hostname].items()
                    if k not in dead_hostnames
                }

            prev_table = self._dijkstra()
            self._update_routing(prev_table)
            self._routing.update(copy.deepcopy(self._routing_table))

            log('update routing table: {}'.format(self._routing_table))
        finally:
            self._link_state_lock.release()
            self._routing_table_lock.release()

        self._push_to_routing_model()
        self._check_alive_thread = threading.Timer(self._timeout, LS._check_timeout, args=(self,))
        self._check_alive_thread.start()

class CentralizedMember(LS):
    def __init__(self, central_hostname, hostname, transport, routing_table,
                 neighbor, dispather, update_interval=30, timeout=180):
        super(CentralizedMember, self).__init__(hostname,
                                                transport,
                                                routing_table,
                                                neighbor,
                                                dispather,
                                                update_interval,
                                                timeout)

        self._central_hostname = central_hostname

    def receive(self, src, data):
        neighbor_table = self._neighbor.get()

        central_cost = neighbor_table[self._central_hostname]
        log('receive routing data from {}: {}'.format(src, data))

        for hostname in data['dead']:
            if hostname in neighbor_table:
                self._neighbor.timeout(hostname)

        self._routing_table_lock.acquire()
        self._link_state_lock.acquire()
        try:
            self._link_state = data['link']

            prev_table = self._dijkstra()
            self._update_routing(prev_table)
            self._routing_table[self._central_hostname] = {
                'next': self._central_hostname,
                'cost': central_cost
            }

            log('update routing table: {}'.format(self._routing_table))
        finally:
            self._link_state_lock.release()
            self._routing_table_lock.release()

        self._push_to_routing_model()

    def run(self):
        send_data = {
            'type': ALGORITHM_TYPE,
            'data': {
                'neighbor': self._neighbor.get()
            }
        }

        self._transport.send(self._central_hostname, send_data)
        log('send neighbor information to {}: {}'.format(self._central_hostname, send_data['data']['neighbor']))

        self._timer_thread = threading.Timer(self._interval, CentralizedMember.run, args=(self,))
        self._timer_thread.start()

    def _check_timeout(self):
        pass

class CentralizedController(Algorithm):
    def receive(self, src, data):
        dead_hostnames = []
        current_time = time.time()

        log('receive routing data from {}: {}'.format(src, data))
        with self._alive_table_lock:
            self._alive_table[src] = current_time
            dead_hostnames = [hostname
                              for hostname in self._alive_table
                              if current_time - self._alive_table[hostname] > self._timeout]

        if len(dead_hostnames) != 0:
            log('dead hostnames: {}'.format(dead_hostnames))
            self._neighbor_timeout(dead_hostnames)

        dead_hostnames.append(self._hostname)
        with self._link_state_lock:
            self._link_state[src] = data['neighbor']
            for hostname in data['neighbor']:
                if hostname not in self._link_state:
                    self._link_state[hostname] = {}

            for hostname in dead_hostnames:
                if hostname in self._link_state:
                    self._link_state.pop(hostname)

            for hostname in self._link_state:
                self._link_state[hostname] = {
                    k: v for k, v in self._link_state[hostname].items()
                    if k not in dead_hostnames
                }

    def run(self):
        current_time = time.time()

        with self._alive_table_lock:
            alive_hosts = [hostname
                           for hostname in self._alive_table
                           if current_time - self._alive_table[hostname] <= self._timeout]
            info('alive_hosts: {}'.format(alive_hosts))
            dead_hosts = list(set(self._alive_table.keys()) - set(alive_hosts))

        with self._link_state_lock:
            send_data = {
                'type': ALGORITHM_TYPE,
                'data': {
                    'link': copy.deepcopy(self._link_state),
                    'dead': dead_hosts
                }
            }

        self._neighbor_timeout(dead_hosts)
        for hostname in alive_hosts:
            self._transport.send(hostname, send_data, True)

        log('send routing data: {}'.format(send_data['data']['link']))

        self._timer_thread = threading.Timer(self._interval, CentralizedController.run, args=(self,))
        self._timer_thread.start()
