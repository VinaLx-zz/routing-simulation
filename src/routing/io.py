import datetime

view = None


def init(_view):
    global view
    view = _view


def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def print_message(message):
    if view:
        view.add_message("[%s] %s \n" % (now(), message))
    else:
        print("[%s] %s \n" % (now(), message))


def print_log(log):
    if view:
        view.add_log("[%s] %s \n" % (now(), log))
    else:
        print("[%s] %s \n" % (now(), log))
