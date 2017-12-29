class DataDispatcher:
    def __init__(self):
        self.dispatcher = {}

    def register(self, t, receiver):
        """
        Registers receiver for each type of data
        """
        self.dispatcher[t] = receiver

    def dispatch(self, t, source, data):
        """
        Dispatch certain type data to proper receiver
        Returns:
            bool: True if type specified by `t` has a receiver, False if not
        """
        receiver = self.dispatcher.get(t)
        if receiver is None:
            return False
        receiver.receive(source, data)
        return True
