import datetime
import threading


view = None
mutex = threading.Lock()


def init(_view):
    global view
    view = _view


def now():
    return datetime.datetime.now().strftime('%H:%M:%S')


def make_message(msg):
    if view:
        return "[Hostname: {0} {1}] {2}".format(view.hostname, now(), msg)
    return "[{0}] {1}".format(now(), msg)


def print_message(message):
    item = make_message(message)
    if view:
        mutex.acquire()
        view.listen_message_event(item + '\n')
        mutex.release()
    print(item)


def print_log(log):
    item = make_message(log)
    if view:
        mutex.acquire()
        view.listen_log_event(item + '\n')
        mutex.release()
    print(item)
