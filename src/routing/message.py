from .io import print_message


def pm(src, message):
    print_message("[Message] from {0}: {}".format(src, message))


class Message:
    """A module used for sending and receiving message"""
    TYPE = 'Message'

    def __init__(self, transport, dispather):
        self._transport = transport
        self._dispather = dispather
        self._dispather.register(Message.TYPE, self)

    def send(self, destination, message):
        """ Send message to destination
        Args:
            destination: str, destination hostname
            message: str, text message only
        """
        self._transport.send()
        data = {
            'type': Message.TYPE,
            'data': message
        }
        self._transport.send(destination, data)

    def receive(self, src, data):
        """ Receive hns data
          Args:
            data: str
        """
        pm(src, data)
