import threading
import copy
import json
import socket

class HNS():
  """Hostname Server

  A Hostname Server, which can transfer a hostname to an address(ip, port)
  """
  def __init__(self, ip_, port_):
    """Initialize this hns

    Args:
      ip: str, specify the server's ip
      port: int, specify the port to be listened by server
  
    Raises:
      ValueError: Args must be right
    """
    #
    # mapping_table: {
    #  name: (ip, port)
    #  }
    #
    self.ip, self.port, self.mapping_table = ip_, port_, {}
    self.mapping_lock = threading.Lock()

    if not isinstance(ip_, str):
      raise ValueError("wrong ip")
    if not isinstance(port_, int):
      raise ValueError("port must be an integer")
    self.address = (ip_, port_)

    #create a new thread and listen to specified address
    self.thread_listen = threading.Thread(target = self.listen, args = ())
    self.thread_listen.start()

  def listen(self):
    """ Start server

    Create a server socket and listen to specified address. 
    When comes the new data, create a new thread to handle the data.
    """
    print("HNS: Server listenning at %s:%d" % self.address)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(self.address)
    while (True):
      data, addr = s.recvfrom(10240)
      print('receive data\n')
      t = threading.Thread(target = self.response, args = (data.decode(),))
      t.start()
    s.close()

  def response(self, data):
    """Response to others' request

    Args:
      data: {..., 'src_name': src, ...}
    """
    data = json.loads(data)
    self.mapping_lock.acquire()
    try:
      mt = copy.deepcopy(self.mapping_table)
    finally:
      self.mapping_lock.release()

    if data['src_name'] in mt:
      pkt = {
        'last_address': self.address,
        'last_name': 'hns',
        'next_address': mt[data['src_name']],
        'next_name': data['src_name'],
        'src_name': 'hns',
        'dest_name': data['src_name'],
        'type': 4,
        'visited': [],
        'data': mt,
          }
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.sendto(json.dumps(pkt).encode(), pkt['next_address'])
      s.close()

  def configure_by_name(self, name, ip, port):
    if isinstance(ip_, str):
      raise ValueError("wrong ip")
    if isinstance(port_, int):
      raise ValueError("port must be an integer")

    self.mapping_lock.acquire()
    try:
      self.mapping_table.update({
        name:(ip, port)
        })
    finally:
      self.mapping_lock.release()

  def configure_by_dict(self, mt):
    self.mapping_lock.acquire()
    try:
      self.mapping_table.update(mt)
    finally:
      self.mapping_lock.release()
