import datetime
import threading
from threading import Lock

view = None
mutex = threading.Lock()


def init(_view):
    global view
    view = _view


def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def print_message(message):
    if view:
        mutex.acquire()
        view.listen_message_event("[%s] %s\n" % (now(), message))
        mutex.release()
    print("[%s] %s" % (now(), message))


def print_log(log):
    if view:
        mutex.acquire()
        view.listen_log_event("[%s] %s\n" % (now(), log))
        mutex.release()
    print("[%s] %s" % (now(), log))
