from routing import router
from routing import config

def test_dv():
    hns_addr = config.Address('127.0.0.1', 8888)
    self_addr = config.Address('127.0.0.1', 8889)
    c = config.Config(config.Algorithm.DV, 'A', self_addr, hns_addr, 30, 5)
    r = router.Router(c)
    r.run()

    import time
    time.sleep(3)
    r.update_neighbor('B', 2)
    r.update_neighbor('C', 1)

def test_ls():
    hns_addr = config.Address('127.0.0.1', 8888)
    self_addr = config.Address('127.0.0.1', 8889)
    c = config.Config(config.Algorithm.LS, 'A', self_addr, hns_addr, 30, 5)
    r = router.Router(c)
    r.run()

    import time
    time.sleep(3)
    r.update_neighbor('B', 2)
    r.update_neighbor('C', 1)

def test_centralized():
    hns_addr = config.Address('127.0.0.1', 8888)
    self_addr = config.Address('127.0.0.1', 8889)
    c = config.Config(config.Algorithm.LS_CENTRALIZE, 'A', self_addr, hns_addr, 30, 5, 'E')
    r = router.Router(c)
    r.run()

    import time
    time.sleep(3)
    r.update_neighbor('E', 1)
    r.update_neighbor('B', 2)
    r.update_neighbor('C', 1)
    r.update_neighbor('D', 4)

if __name__ == '__main__':
    test_dv()
