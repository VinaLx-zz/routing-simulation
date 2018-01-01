import threading
import copy
import json
import socket
from routing import transport
from .io import print_log


def log(message):
    print_log("[HNS] {0}".format(message))

def info(message):
    log("[INFO] {0}".format(message))


def error(message):
    log("[ERROR] {0}".format(message))


class HNS:
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
        self._address = (ip, port)
        self._mapping_table = {'hns': self._address}
        self._mapping_lock = threading.Lock()
        self._transport_module = transport.Transport('hns', ip, port, ip, port, None, None, None)

    def run(self):
        """ Run the server
        """
        # create a new thread and listen to specified address
        self.thread_listen = threading.Thread(target=self._listen, args=())
        self.thread_listen.start()

    def _listen(self):
        """ Start server

        Create a server socket and listen to specified address.
        When comes the new data, create a new thread to handle the data.
        """
        info("Server listenning at {} : {}".format(self._address[0],
                                                   self._address[1]))
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(self._address)
        while (True):
            data, addr = s.recvfrom(10240)
            info('Receive data')
            t = threading.Thread(target=self._response, args=(data.decode(),))
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
        self._transport_module.receive('noname', mt)

        for key in mt:
            if key != 'hns':
                self._transport_module.send(key, data, True)
