from routing import router
from routing import config

def test_dv():
    hns_addr = config.Address('127.0.0.1', 8888)
    self_addr = config.Address('127.0.0.1', 8890)
    c = config.Config(config.Algorithm.DV, 'B', self_addr, hns_addr, 30, 5)
    r = router.Router(c)
    r.run()

    import time
    time.sleep(3)
    r.update_neighbor('A', 2)
    r.update_neighbor('D', 3)

def test_ls():
    hns_addr = config.Address('127.0.0.1', 8888)
    self_addr = config.Address('127.0.0.1', 8890)
    c = config.Config(config.Algorithm.LS, 'B', self_addr, hns_addr, 30, 5)
    r = router.Router(c)
    r.run()

    import time
    time.sleep(3)
    r.update_neighbor('A', 2)
    r.update_neighbor('D', 3)

def test_centralized():
    hns_addr = config.Address('127.0.0.1', 8888)
    self_addr = config.Address('127.0.0.1', 8890)
    c = config.Config(config.Algorithm.LS_CENTRALIZE, 'B', self_addr, hns_addr, 30, 5, 'E')
    r = router.Router(c)
    r.run()

    import time
    time.sleep(3)
    r.update_neighbor('E', 1)
    r.update_neighbor('A', 2)
    r.update_neighbor('D', 3)
    r.update_neighbor('C', 2)

    time.sleep(20)
    r.stop()
    print('{} b stop'.format(time.ctime()))

    time.sleep(60)
    r.run()
    print('{} b restart'.format(time.ctime()))

if __name__ == '__main__':
    test_dv()
