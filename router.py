import threading
import time
import copy
import socket
import json

class RouterCtrl:
  """Router Control Module.
  
  Routing Algorithms:
    1. global routing algorithm
      a. RouterCtrl.LS
      b. RouterCtrl.CENTRAL_LS
    2. decentralized routing alorithm
      a. RouterCtrl.DV
  """
  
  LS = 1
  DV = 2
  CENTRAL_LS = 3

  METHOD = (
    LS, DV, CENTRAL_LS
  )

  def __init__(self, name_, ip_, port_, hns_ip, hns_port):
    """Initialize

    This method set the listen port and create a new thread to listen the port. 

    Args:
      name_: name of local host,
      ip_: ip to be listened,
      port_: port to be listened

    Returns:

    Raises:
      ValueError
    """
    self.name, self.address, self.mapping_table = name_, (ip_, port_), {}
    self.hns_address = (hns_ip, hns_port)
    self.mapping_lock = threading.Lock()
    self.debug = True

    if (type(port_) is not int):
      raise ValueError("port must be integer")

    #create a new thread and listen to specified address
    self.thread_listen = threading.Thread(target = self._listen, args = ())
    self.thread_listen.start()
    self._query_hns()

  def _get_self_name(self):
    return self.name

  def init(self, method, interval=60, overtime=300):
    """select routing algorithm and set update interval time.

    Args:
      method: could only be "RouterCtrl.LS", "RouterCtrl.DV" or "RouterCtrl.CENTRAL_LS"

    Raise:
      ValueError: method does not exist，interval is not positive
      TypeError: interval is not integer
    """

    if method not in RouterCtrl.METHOD:
      raise ValueError('method must be "RouterCtrl.LS", "RouterCtrl.DV" or "RouterCtrl.CENTRAL_LS"')

    if not isinstance(interval, int):
      raise TypeError('interval must be positive integer')
    elif interval < 1:
      raise ValueError('interval must be positive integer')

    self._method = method
    self._interval = interval
    self._overtime = overtime
    self._timer_thread = None
    self._running = False
    self._controller_hostname = None
    self._controller_hostname_lock = threading.Lock()

    # manulally set, structure
    #
    # self._neighbor_table = {
    #   'destination': cost
    # }
    self._neighbor_table = {}
    self._neighbor_table_lock = threading.Lock()

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
      self.name: {
        'next': self.name,
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
    #   "host_2": {
    #     "other_host3": cost_2_1,
    #     "other_host4": cost_2_2,
    #     ...
    #   }
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

  def add_neighbor(self, hostname, cost):
    """add neighbor router.

    hostname must be unique

    Args:
      hostname: hostname of neighbor router
      cost: cost of attached links

    Raise:
      ValueError: hostname duplicate, cost is not positive
      TypeError: hostname is not string, cost is not integer
    """

    if not isinstance(cost, int):
      raise TypeError('cost must be positive integer')
    elif cost < 1:
      raise ValueError('cost must be positive integer')

    if not isinstance(hostname, str):
      raise TypeError('hostname must be string')
    elif hostname in self._neighbor_table:
      raise ValueError('hostname already exists')

    self._neighbor_table_lock.acquire()
    try:
      self._neighbor_table[hostname] = cost
    finally:
      self._neighbor_table_lock.release()

    self._routing_table_lock.acquire()
    try:
      self._routing_table[hostname] = {
        'next':hostname,
        'cost':cost
      }
    finally:
      self._routing_table_lock.release()

  def update_neighbor(self, hostname, cost):
    """update neighbor router.

    Args:
      hostname: hostname of neighbor router
      cost: cost of attached links

    Raise:
      ValueError: hostname does not exist, cost is not positive
      TypeError: hostname is not string, cost is not integer
    
    Returns:
      bool: if modified
    """

    if not isinstance(cost, int):
      raise TypeError('cost must be positive integer')
    elif cost < 1:
      raise ValueError('cost must be positive integer')

    if not isinstance(hostname, str):
      raise TypeError('hostname must be string')
    elif hostname not in self._neighbor_table:
      raise ValueError('hostname does not exist')

    if self._neighbor_table[hostname] == cost:
      return False
    else:
      self._neighbor_table_lock.acquire()
      try:
        self._neighbor_table[hostname] = cost
      finally:
        self._neighbor_table_lock.release()
      return True

  def remove_neighbor(self, hostname):
    """remove neighbor router.

    Args:
      hostname: hostname of neighbor router

    Raise:
      ValueError: hostname does not exist
      TypeError: hostname is not string
    """

    if not isinstance(hostname, str):
      raise TypeError('hostname must be string')
    elif hostname not in self._neighbor_table:
      raise ValueError('hostname does not exist')

    self._neighbor_table_lock.acquire()
    try:
      self._neighbor_table.pop(hostname)
    finally:
      self._neighbor_table_lock.release()

    self._routing_table_lock.acquire()
    try:
      for key in self._routing_table:
        if self._routing_table[key]['next'] == hostname:
          self._routing_table.pop(key)
    finally:
      self._routing_table_lock.release()

  def set_controller(self, hostname):
    """set LS routing algorithm controller.

    Members of LS routing algorithm must call the function
    to specify the hostname of controller
    
    Args:
      hostname: hostname of controller
    
    Raise:
      TypeError: hostname is not string
    """

    if not isinstance(hostname, str):
      raise TypeError('hostname must be string')
    else:
      self._controller_hostname_lock.acquire()
      try:
        self._controller_hostname = hostname
      finally:
        self._controller_hostname_lock.release()

  def run(self, is_controller=False):
    """Running routing algorithms.

    Begin to exchange routing table

    Args:
      is_controller: for LS routing algorithm to indicate whether it is the controller
    
    Raise:
      RuntimeError: LS controller is not specified
    """

    if self._running is False:
      self._is_controller = is_controller

      if self._method == RouterCtrl.DV:
        self._dv_interval(self._interval)
      elif self._method == RouterCtrl.LS:
        self._ls_interval(self._interval)
      elif is_controller is True:
        self._central_ls_controller(self._interval)
      elif self._controller_hostname is None:
        raise RuntimeError('controller hostname is not specified')
      else:
        self._central_ls_member(self._interval)

      self._running = True
    
  def shutdown(self):
    """Stop routing algorithms.
    """

    self._running = False

    if self._timer_thread is not None:
      self._timer_thread.cancel()
      self._timer_thread = None
  
  def _ls_interval(self, interval):
    """Begin to exchange routing table to neighbor router periodically.

    Only for LS routing algorithms

    Args:
      interval: interval time, seconds
    
    Raise:
      RuntimeError: selected routing algorithm is not LS
    """

    if self._method != RouterCtrl.LS:
      raise RuntimeError('selected method is not "RouterCtrl.LS"')

    self._neighbor_table_lock.acquire()
    self._alive_table_lock.acquire()
    try:
      data = {
        'neighbor': copy.deepcopy(self._neighbor_table),
        'alive': copy.deepcopy(self._alive_table)
      }
    finally:
      self._alive_table_lock.release()
      self._neighbor_table_lock.release()

    self_hostname = self._get_self_name()
    if self.debug:
      print('%s sending router table' % self.name)
    self._send(self_hostname, self_hostname, 3, data, [])

    self._timer_thread = threading.Timer(interval, RouterCtrl._ls_interval, args=(self, interval))
    self._timer_thread.start()

  def _dv_interval(self, interval):
    """Begin to exchange routing table to neighbor router periodically.

    Only for DV routing algorithms

    Args:
      interval: interval time, seconds
    
    Raise:
      RuntimeError: selected routing algorithm is not DV
    """

    if self._method != RouterCtrl.DV:
      raise RuntimeError('selected method is not "RouterCtrl.DV"')

    self._neighbor_table_lock.acquire()
    self._routing_table_lock.acquire()
    try:
      data = copy.deepcopy(self._routing_table)
      neighbor_hosts = list(self._neighbor_table.keys())
    finally:
      self._routing_table_lock.release()
      self._neighbor_table_lock.release()

    self_hostname = self._get_self_name()
    for hostname in neighbor_hosts:
      self._send(self_hostname, hostname, 1, data, [])

    self._timer_thread = threading.Timer(interval, RouterCtrl._dv_interval, args=(self, interval))
    self._timer_thread.start()

  def _central_ls_controller(self, interval):
    """Begin to exchange routing table to neighbor router periodically.

    Only for controller of LS routing algorithms

    Args:
      interval: interval time, seconds
    
    Raise:
      RuntimeError: selected routing algorithm is not CENTRAL_LS
    """

    if self._method != RouterCtrl.CENTRAL_LS:
      raise RuntimeError('selected method is not "RouterCtrl.CENTRAL_LS"')
    
    self._alive_table_lock.acquire()
    self._link_state_lock.acquire()
    try:
      current_time = time.time()
      data = copy.deepcopy(self._link_state)
      alive_hosts = [hostname
        for hostname in self._alive_table
        if current_time - self._alive_table[hostname] <= self._overtime
      ]
    finally:
      self._link_state_lock.release()
      self._alive_table_lock.release()

    self_hostname = self._get_self_name()
    for hostname in alive_hosts:
      self._send(self_hostname, hostname, 2, data, [])

    self._timer_thread = threading.Timer(interval, RouterCtrl._central_ls_controller, args=(self, interval))
    self._timer_thread.start()

  def _central_ls_member(self, interval):
    """Begin to exchange routing table to neighbor router periodically.

    Only for members of CENTRAL_LS routing algorithms

    Args:
      interval: interval time, seconds
    
    Raise:
      RuntimeError: selected routing algorithm is not CENTRAL_LS
    """

    if self._method != RouterCtrl.CENTRAL_LS:
      raise RuntimeError('selected method is not "RouterCtrl.CENTRAL_LS"')

    self._controller_hostname_lock.acquire()
    self._neighbor_table_lock.acquire()
    try:
      data = copy.deepcopy(self._neighbor_table)
      self._send(self._get_self_name(), self._controller_hostname, 2, data, [])
    finally:
      self._neighbor_table_lock.release()
      self._controller_hostname_lock.release()

    self._timer_thread = threading.Timer(interval, RouterCtrl._central_ls_member, args=(self, interval))
    self._timer_thread.start()

  def update(self, source, data):
    """update routing table.

    Different routing algorithms and different role has different data structure
    
    LS routing algorithms:
      data = ...
    
    DV routing algorithms:
      data = ...

    CENTRAL_LS routing algorithms:
      controller:
        data = source._neighbor_table = {
          "destination": cost,
          ...
        }

      member:
        data = source._link_state = {
          "host_1": {
            "other_host1": cost_1_1,
            "other_host2": cost_1_2,
            ...
          },
          ...
        }

    Args:
      source: sender hostname
      data: received data
    """

    # LS routing algorithms
    if self.debug:
      print('%s: updating router table' % self.name)
    if self._method == RouterCtrl.LS:
      self._ls_receive(source, data)
    elif self._method == RouterCtrl.DV:
      self._dv_receive(source, data)
    elif self._is_controller is True:
      self._central_ls_controller_receive(source, data)
    else:
      self._central_ls_member_receive(source, data)

  def _ls_receive(self, source, data):
    """Received data handler for LS routing algorithms.

    Args:
      source: sender hostname
      data: received data
    """
    if self.debug:
      print('%s: receive other routing table' % self.name)
    dead_hostnames = []

    self._alive_table_lock.acquire()
    try:
      current_time = time.time()
      self._alive_table[self._get_self_name()] = current_time
      # update alive table
      for hostname in data['alive']:
        if hostname not in self._alive_table:
          self._alive_table[hostname] = data['alive'][hostname]
        elif data['alive'][hostname] > self._alive_table[hostname]:
          self._alive_table[hostname] = data['alive'][hostname]
      
      # collect dead hostnames
      for hostname in self._alive_table:
        if current_time - self._alive_table[hostname] > self._overtime:
          dead_hostnames.append(hostname)
    finally:
      self._alive_table_lock.release()

    self._neighbor_table_lock.acquire()
    self._routing_table_lock.acquire()
    self._link_state_lock.acquire()
    try:
      self._link_state[self.name] = self._neighbor_table
      for hostname in self._neighbor_table:
        if hostname not in self._link_state:
          self._link_state[hostname] = {}

      self._link_state[source] = data['neighbor']
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
      if self.debug:
        print('%s received data from %s:' % (self.name, source), data)
        print('%s link state:' % self.name, self._link_state)
        print('%s prev_table:' % self.name, prev_table)
        print('%s routing table:' % self.name, self._routing_table)
    finally:
      self._link_state_lock.release()
      self._routing_table_lock.release()
      self._neighbor_table_lock.release()

  def _dijkstra(self):
    """Dijkstra algorithm

    update routing table

    must be wrapped with the link state lock

    Returns:
      prev_table: shortest path table
    """

    self_hostname = self._get_self_name()
    visited = [self_hostname]
    prev_table = {
      self_hostname: {
        'prev': None,
        'cost': 0
      }
    }
    
    for hostname in self._link_state[self_hostname]:
      prev_table[hostname] = {
        'prev': self_hostname,
        'cost': self._link_state[self_hostname][hostname]
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
            prev_table[hostname]['cost'] > nearest_cost + self._link_state[nearest_hostname][hostname])):
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

    self_hostname = self._get_self_name()

    self._routing_table.clear()
    self._routing_table[self.name] = {
      'next': self.name,
      'cost': 0
    }
    for destination in prev_table:
      last_hop = destination

      if prev_table[last_hop]['prev'] is None:
        continue
      while prev_table[last_hop]['prev'] != self_hostname:
        last_hop = prev_table[last_hop]['prev']

      self._routing_table[destination] = {
        'next': last_hop,
        'cost': prev_table[destination]['cost']
      }

  def _dv_receive(self, source, data):
    """Received data handler for DV routing algorithms.

    Args:
      source: sender hostname
      data: received data
    """
    
    modified = False
    dead_hostnames = []

    self._alive_table_lock.acquire()
    try:
      current_time = time.time()
      self._alive_table[self.name] = current_time
      self._alive_table[source] = current_time
      dead_hostnames = [hostname
      for hostname in self._alive_table
        if current_time - self._alive_table[hostname] > self._overtime]
      if self.debug:
        print('%s received data from %s at %f:' % (self.name, source, current_time), data)
        print('%s alive table:' % self.name, self._alive_table)
    finally:
      self._alive_table_lock.release()

    self._routing_table_lock.acquire()
    try:
      if len(set(self._routing_table.keys()) & set(dead_hostnames)) > 0:
        modified = True

      self._routing_table = {
        k: v for k, v in self._routing_table.items()
             if k not in dead_hostnames and v['next'] not in dead_hostnames
      }

      data = {
        k: v for k, v in data.items()
             if k not in dead_hostnames and v['next'] not in dead_hostnames
      }

      for destination in data:
        indirect_cost = self._routing_table[source]['cost'] + data[destination]['cost']
        if destination not in self._routing_table:
          self._routing_table[destination] = {
            'next': source,
            'cost': indirect_cost
          }
          modified = True
        elif self._routing_table[destination]['cost'] > indirect_cost:
          self._routing_table[destination]['next'] = source
          self._routing_table[destination]['cost'] = indirect_cost
          modified = True
      if self.debug:
        print('%s received data from %s at %f:' % (self.name, source, current_time), data)
        print('%s routing table:' % self.name, self._routing_table)
    finally:
      self._routing_table_lock.release()
    
    if modified is True:
        self._neighbor_table_lock.acquire()
        self._routing_table_lock.acquire()
        try:
          send_data = copy.deepcopy(self._routing_table)
          neighbor_hosts = list(self._neighbor_table.keys())
        finally:
          self._routing_table_lock.release()
          self._neighbor_table_lock.release()

        self_hostname = self._get_self_name()
        for hostname in neighbor_hosts:
          self._send(self_hostname, hostname, 1, send_data)

  def _central_ls_controller_receive(self, source, data):
    """Received data handler for controller of
        centralized LS routing algorithms.

    Args:
      source: sender hostname
      data: received data
    """

    dead_hostnames = []

    self._alive_table_lock.acquire()
    try:
      current_time = time.time()
      self._alive_table[source] = current_time
      dead_hostnames = [hostname
        for hostname in self._alive_table
        if current_time - self._alive_table[hostname] > self._overtime]
      if self.debug:
        print('%s received data from %s at %f:' % (self.name, source, current_time), data)
        print('%s alive table:' % self.name, self._alive_table)
    finally:
      self._alive_table_lock.release()

    dead_hostnames.append(self.name)
    self._link_state_lock.acquire()
    try:
      self._link_state[source] = data
      for hostname in data:
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

      if self.debug:
        print('%s received data from %s at %f:' % (self.name, source, current_time), data)
        print('%s link state:' % self.name, self._link_state)
    finally:
      self._link_state_lock.release()

  def _central_ls_member_receive(self, source, data):
    """Received data handler for members of
        centralized LS routing algorithms.

    Args:
      source: sender hostname
      data: received data
    """
    
    current_time = time.time()

    self._controller_hostname_lock.acquire()
    self._neighbor_table_lock.acquire()
    try:
      controller_hostname = self._controller_hostname
      controller_cost = self._neighbor_table[controller_hostname]
    finally:
      self._neighbor_table_lock.release()
      self._controller_hostname_lock.release()

    self._routing_table_lock.acquire()
    self._link_state_lock.acquire()
    try:
      self._link_state = data
      if self.debug:
        print('%s received data from %s at %f:' % (self.name, source, current_time), data)

      prev_table = self._dijkstra()
      self._update_routing(prev_table)
      self._routing_table[controller_hostname] = {
        'next': controller_hostname,
        'cost': controller_cost
      }

      if self.debug:
        # print('%s received data from %s at %f:' % (self.name, source, current_time), data)
        print('%s link state:' % self.name, self._link_state)
        print('%s routing table:' % self.name, self._routing_table)
    finally:
      self._link_state_lock.release()
      self._routing_table_lock.release()

  def search(self, hostname):
    """search for next-hop router.

    Args:
      hostname: destination router
    
    Returns:
      next_hostname: hostname of next-hop router
    
    Raise:
      TypeError: hostname is not string
      ValueError: hostname unreachable
    """

    if not isinstance(hostname, str):
      raise TypeError('hostname must be string')

    if self._get_self_name() == hostname:
      next_hostname = hostname
    else:
      self._routing_table_lock.acquire()
      try:
        next_hostname = self._routing_table[hostname]['next']
      except KeyError:
        raise ValueError('hostname unreachable')
      finally:
        self._routing_table_lock.release()
    
    return next_hostname

  #######################################################################
  #                                                                     #
  #    data transfer module                                             #
  #                                                                     #
  #######################################################################
  def _listen(self):
    """ Start server

    Create a server socket and listen to specified address. 
    When comes the new data, create a new thread to handle the data.
    """
    print("Server listenning at %s:%d" % self.address)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(self.address)
    while True:
      data, addr = s.recvfrom(10240)
      if not self._running:
        continue
      print('%s receive data\n' % self.name)
      t = threading.Thread(target = self._parse, args = (data.decode(),))
      t.start()
    s.close()

  def _query_hns(self):
    self._send(self.name, 'hns', 4, 'sb', [])
    self.thread_query_hns = threading.Timer(10, RouterCtrl._query_hns, args = (self,))
    self.thread_query_hns.start()

  def _send(self, source, destination, type = 0, data = 'default data', visited = []):
    """ Send data to destination

    Send data, which can be normal data or router table, to destination.

    Args:
      source: str, name of source host, if it is self, call self._get_self_name()
      destination: str, the name of destination host
      type: 0 is for normal data, 1 for dv, 2 for center-ls, 3 for no-center-ls 
      data: original data or router table

    Raises:
      TypeError: source and destination must be string
      ValueError: type must be 0, 1, 2 or 3
    """
    if (not isinstance(source, str)) or (not isinstance(destination, str)):
      raise TypeError('source and destination must be string')
    if (not isinstance(type, int)) or (type < 0 or type > 4):
      raise ValueError('type must be 0, 1, 2, 3, 4')

    visited.append(self.name)

    try:
      if type == 4:
        next_address = self.hns_address
        next_name = 'sb'
      else:
        next_address = self._get_next_address(destination)
        next_name = self._get_next_name(destination)
    except ValueError:
      print('%s: error occur when sending' % self.name)
      return

    # make a packet
    pkt = {
    'last_address': self.address,
    'last_name': self.name,
    'next_address': next_address,
    'next_name': next_name,
    'src_name': source,
    'dest_name': destination,
    'type': type,
    'visited': visited,
    'data': data,
      }

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 3 : send with broadcasting---sending to all neighbors
    if type == 3:
      # get neighbors
      neighbors = list(self._neighbor_table.keys())

      if self.debug:
        print(self.name, neighbors, pkt['visited'])

      # send to all neighbors that are not visited
      for n in neighbors:
        if (n not in pkt['visited']):

          if self.debug:
            print('%s sending to %s' % (self.name, n))

          try:
            next_address = self._get_next_address(n)
            next_name = self._get_next_name(n)
          except ValueError:
            print('%s: error occur when sending' % self.name)
            next_name = None
          if next_name is None:
            continue

          pkt['next_address'] = next_address
          pkt['next_name'] = next_name
          pkt['dest_name'] = next_name
          s.sendto(json.dumps(pkt).encode(), pkt['next_address'])

          if self.debug:
            print('%s: succeed sending to %s' % (self.name, pkt['next_name']))
    
    # other situation : just sending
    else:  
      s.sendto(json.dumps(pkt).encode(), pkt['next_address'])
      if self.debug:
        print('%s: succeed sending to %s' % (self.name, pkt['next_name']))
    
    s.close()

  def send(self, destination, data):
    """ Send data to destination

    Send normal data, using _send

    Args:
      destination: str, the name of destination host 
      data: original data or router table
    """ 
    self._send(_get_self_name, destination, 0, data, [])
    

  #######################################################################
  #                                                                     #
  #    data parse module                                                #
  #                                                                     #
  #######################################################################
  def _parse(self, data):
    """ Parse the received data

    Parse the received data according to its type

    Args:
      data: the received data

    Raises:
      ValueError
    """
    if self.debug:
      print('%s: parsing...' % self.name)

    data = json.loads(data)

    # if here is destination
    if (data['dest_name'] == self.name):

      # 0 : normal data
      if (data['type'] == 0): 
        self._handle_normal(data)

      # 1,2,3 : router data
      elif (data['type'] == 1 or data['type'] == 2 or data['type'] == 3):
        self._handle_router(data['src_name'], data['data'])
        # 3 : non-central router need broadcasting
        if (data['type'] == 3):
          self._handle_broadcast(data)

      # 4 : hns data
      elif (data['type'] == 4):
        self._handle_mapping_table(data['data'])
      else:
        raise ValueError('undefined data type %d' % data['type'])

    # if just pass by
    else:
      self._handle_sending(data)

    if self.debug:
      print('parsing finished')


  #######################################################################
  #                                                                     #
  #    data control module                                              #
  #                                                                     #
  #######################################################################
  def _get_next_address(self, dst_name):
    """ Get next host address according to dst_name

    Get next host address according to dst_name, router module and mapping table

    Args:
      dst_name: str, destination host name

    Returns:
      next_address: next host address

    Raises:
      TypeError: dst_name must be string
    """
    if not isinstance(dst_name, str):
      raise TypeError('dst_name must be string')

    
    try:
      next_name = self._get_next_name(dst_name)
    except ValueError:
      raise ValueError('hostname not found')

    if next_name not in self.mapping_table.keys():
      raise ValueError('no such host name as %s' % next_name)

    return self.mapping_table[next_name]

  def _get_next_name(self, dst_name):
    """Get next host name according to dst_name

    Get next host name according to dst_name and router module

    Args:
      dst_name: destination host name

    Returns:
      next_name: next host name
    """  
    try:
      next_name = self.search(dst_name)
    except (KeyError, ValueError):
      raise ValueError('hostname not found')

    return next_name

  def _configure_mapping_table(self, mt):
    """ Configure mapping table

    Configure mapping table at first, please call this method before sending anything

    Args:
      mt: a dictionary, whose key is neighbor's name and whose value is (str(ip), int(port))
    """
    self.mapping_lock.acquire()
    try: 
      self.mapping_table.update(mt)
      if self.debug:
        print('%s: mapping table config' % self.name, self.mapping_table)
    finally:
      self.mapping_lock.release()

  def _handle_normal(self, data):
    """ Handle normal data

    Handle normal data, just print them all

    Args:
      data: a dict, json-like data
    """
    print('Receive data from %s: %s ' % (data['src_name'], data['data']))

  def _handle_router(self, src, data):
    """ Handle router table

    Handle router table according to its type

    Args；
      src: source host name
      data: data from source
    """
    self.update(src, data)


  def _handle_sending(self, data):
    """Redirect the data to destination
    
    Send data to its destination, current host acts as a router

    Args:
      data: data to be sended
    """
    print('Receive data from %s, and send it to %s' % (data['src_name'], data['dest_name']))
    self._send(data['src_name'], data['dest_name'], data['type'], data['data'])

  def _handle_broadcast(self, data):
    """Broadcast the data to all the neighbor
    
    Broadcast the data to all the neighbor

    Args:
      data: data to be sended
    """
    print('%s Broadcasting...' % self.name)
    self._send(data['src_name'], self.name, data['type'], data['data'], data['visited'])

  def _handle_mapping_table(self, data):
    mt = {}
    for key in data:
      mt[key] = (data[key][0], data[key][1])
    self._configure_mapping_table(mt)

  def stop_query():
    if self.thread_query_hns is not None:
      self.thread_query_hns.cancel()
      self.thread_query_hns = None