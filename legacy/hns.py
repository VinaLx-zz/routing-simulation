import threading
import copy
import json
import socket
import transport
import threading

class HNS():
  """Hostname Server

  A Hostname Server, which can transfer a hostname to an address(ip, port)
  """
  def __init__(self, ip, port):
    """Initialize this hns

    Args:
      ip: str, specify the server's ip
      port: int, specify the port to be listened by server
    """
    #
    # mapping_table: {
    #  name: (ip, port)
    #  }
    #
    self.address = (ip, port)
    self._mapping_table = {'hns':self.address}
    self._mapping_lock = threading.Lock()
    self.transport_module = transport.Transport()
    self.transport_module.init('hns', ip, port, ip, port)

  def run(self):
    """ Run the server
    """
    #create a new thread and listen to specified address
    self.thread_listen = threading.Thread(target = self._listen, args = ())
    self.thread_listen.start()

  def _listen(self):
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
      t = threading.Thread(target = self._response, args = (data.decode(),))
      t.start()
    s.close()

  def _response(self, data):
    """Response to others' request

    Args:
      data: {..., 'src_name': src, ...}
    """
    data = json.loads(data)
    data = data['datagram']['data']['data']
    self._mapping_lock.acquire()
    self._mapping_table.update(data)
    self._mapping_lock.release()

    self._send_update()

  def _send_update(self):
    """ When the table is updated, send it to all hosts
    """
    self._mapping_lock.acquire()
    mt = copy.deepcopy(self._mapping_table)
    self._mapping_lock.release()
    data = {
      'type': transport.Transport.TYPE,
      'data': mt
    }
    self.transport_module.receive(mt)

    for key in mt:
      if key != 'hns':
        self.transport_module.send(key, data, True)