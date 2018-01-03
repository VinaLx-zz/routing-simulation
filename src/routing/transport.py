from routing import parse
import json
import threading
import socket
from .io import print_log


def log(message):
    print_log("[Transport] {0}".format(message))


def info(message):
    log("[INFO] {0}".format(message))


def error(message):
    log("[ERROR] {0}".format(message))


class Transport:
    """
    Transport module, used for sending and reveiving message
    """
    TYPE = 'Transport'

    def __init__(self, name, ip, port, hns_ip, hns_port,
                 routing_table, dispather, neighbor):
        """Initialize
        Set the listen port and create a new thread to listen the port.
        Args:
          name: name of local host,
          ip: ip to be listened,
          port: port to be listened
          hns_ip, hns_port: hns' address,
                            data should be sent to (hns_ip, hns_port)
          routing_table, dispather, neighbor: dependcy module
        """
        self._name, self._address = name, (ip, port)
        self._hns_address = (hns_ip, hns_port)
        self._mapping_table = {'hns': self._hns_address}
        self._mapping_lock = threading.Lock()
        self._debug = True
        self._run_lock = threading.Lock()
        self._running = False
        self._routing_table = routing_table
        self._dispather = dispather
        self._neighbor = neighbor
        self._timer_thread = None

    def run(self):
        """ Run this module
        """
        self._dispather.register(Transport.TYPE, self)
        
        self._run_lock.acquire()
        self._running = True
        self._run_lock.release()

        self._thread_listen = threading.Thread(target=self._listen, args=())
        self._thread_listen.start()

        self._send_to_hns()

    def stop(self):
        """ Stop listening
        """
        self._running = False

        data = {
            'type': Transport.TYPE,
            'data': 'stop'
        }

        self.send(self._name, data, True)
        if self._timer_thread is not None:
            self._timer_thread.cancel()
            self._timer_thread = None

    def _send_to_hns(self):
        """ Send to hns to register itself
        """
        data = {
            'type': Transport.TYPE,
            'data': {
                self._name: self._address
            }
        }
        self.send('hns', data, True)

        self._mapping_lock.acquire()
        if self._name not in self._mapping_table:
            self._timer_thread = threading.Timer(10, self._send_to_hns)
            self._timer_thread.start()
        self._mapping_lock.release()


    def receive(self, src, data):
        """ Receive hns data
          Args:
            data: {
              'data': dict, a mapping table
            }
        """
        if data == 'stop':
            return
        mt = {}
        for key in data:
            mt[key] = (data[key][0], data[key][1])
        self._mapping_lock.acquire()
        self._mapping_table.update(mt)
        self._mapping_lock.release()
        info(str(mt))

    def _listen(self):
        """ Start server
        Create a server socket and listen to specified address.
        """
        info('Server listenning at {} : {}'.format(self._address[0], self._address[1]))
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(self._address)
        while True:
            data, addr = s.recvfrom(10240)

            self._run_lock.acquire()
            if not self._running:
                self._run_lock.release()
                if self._debug:
                    info('Stop...')
                break
            self._run_lock.release()

            info('Receive data')
            data = parse.parse(data)
            self._process(data)
        s.close()

    def _process(self, data):
        """ Process data on transport layer
          Args:
            data: {
              'next_name': str
              'last_name': str
              'broadcasting': bool
              'visited': list
              'datagram': {
                'src': src
                'dest': dest
                'data': {
                  'passed_by': []
                  'type':...
                  'data':...
                }
              }
            }
        """
        # broadcasting
        if data['broadcasting']:
            self.broadcasting({
                'visited': data['visited'],
                'src': data['datagram']['src'],
                'data': data['datagram']['data']
            })

        # dispath to other module
        if data['datagram']['dest'] == self._name:

            self._dispather.dispatch(data['datagram']['data']['type'],
                                     data['datagram']['src'],
                                     data['datagram']['data']['data'])
            if self._debug:
                message = 'Receive data from path: '
                for host in data['datagram']['data']['passed_by']:
                    message = message + host + ' -> '
                message = message + self._name
                info(message)
        # just route to other host
        else:
            if self._debug:
                info('Routing from {} to {} '.format(data['datagram']['src'],
                                                     data['datagram']['dest']))

            self._send(data['datagram']['src'], data['datagram']['dest'],
                        data['datagram']['data'], False)

    def send(self, destination, data, privileged_mode=False):
        """ API send
        """
        data['passed_by'] = []
        self._send(self._name, destination, data, privileged_mode)


    def _send(self, src, destination, data, privileged_mode):
        """ Send data to destination

        Send data, which can be normal data or router table, to destination.

        Args:
          src: str, the source hostname
          destination: str, the name of destination host
          data: dict, {
            'passed_by': []
            'type': ...
            'data': ...
          }
          privileged_mode: if set True, it can send it to destination directly,
                            ignoring the next hop router
          passed_by: router host passed_by, used for printing router message
        """
        if self._debug:
            info('Ready for sending {}'.format(data))
        # update passed_by
        data['passed_by'].append(self._name)

        # make a frame
        datagram = self._make_datagram(src, destination, data)
        frame = self._make_frame(destination, datagram, False, [], privileged_mode)

        if frame is None:
            if self._debug:
                error('Fail to make a frame, canceling sending')
            return

        self._send_by_frame(frame)


    def _send_by_frame(self, frame):
        """ Send a frame to destination
          Args:
            frame: frame, including destination
        """
        # get sending address
        sending_address = self._get_address(frame['next_name'])

        if sending_address is None:
            if self._debug:
                error('{} not in mapping_table, canceling sending'.format(
                    frame['next_name']))
            return

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(json.dumps(frame).encode(), sending_address)
        if self._debug:
            info('Succeed sending {1} to {0}'.format(
                frame['next_name'], frame['datagram']['data']))

        s.close()

    def broadcasting(self, data):
        """ Send to all neighbors
          Args:
            data: {                        {
              'type': ...,        or          'visited': list,
                                              'src': str, source hostname
              'data': ...                     'data': data same as left data
            }                                }
        """
        src = data['src'] if 'src' in data.keys() else self._name
        visited = data['visited'] if 'visited' in data.keys() else []
        data = data['data'] if 'src' in data.keys() else data

        neighbors = list(self._neighbor.get().keys())
        for n in neighbors:
            if n not in visited:
                frame = self._make_frame(n, self._make_datagram(src, n, data),
                                         True, visited, False)
                if frame is None:
                    if self._debug:
                        error('Fail to make a frame, canceling sending')
                    continue

                self._send_by_frame(frame)

    def _make_datagram(self, src, dest, data):
        """ Make a datagram, which just like an ip datagram
          Args:
            src: str, source hostname
            dest: str, destination hostname
            data: data to be encapsulated

          Returns:
            datagram: json-like dict, {
              'src': src
              'dest': dest
              'data': data
            }
        """
        return {
            'src': src,
            'dest': dest,
            'data': data
        }

    def _make_frame(self, dest, datagram, broadcasting, visited, privileged_mode):
        """ Make a frame, which just like link-layer frame
          Args:
            dest: str, destination hostname, used to get next hop router
            data: an datagram
            broadcasting: bool, whether broadcasting
            visited: list, list of visited hostname
            privileged_mode: bool, if set True, it can send it to destination directly,
                          ignoring the next hop router

          Returns:
            frame: if succeed making a frame, then return it, otherwise, return None
              {
                'next_name': str, next hop hostname name
                'last_name': str, always be self name
                'broadcasting': bool
                'visited': list
                'datagram': datagram
              }
        """
        try:
            if privileged_mode or broadcasting:
                next_name = dest
            else:
                next_name = self._routing_table.get(dest)
        except Exception as err:
            log(err)
            return None

        if broadcasting:
            visited.append(self._name)

        return {
            'next_name': next_name,
            'last_name': self._name,
            'broadcasting': broadcasting,
            'visited': visited,
            'datagram': datagram
        }

    def _get_address(self, dest):
        """ Get ip address by name
          Args:
            dest: str, destination hostname
          Returns:
            address: (ip, port) or None
        """
        self._mapping_lock.acquire()
        try:
            address = self._mapping_table[dest]
        except Exception as err:
            address = None
            log(err)
        self._mapping_lock.release()

        return address
