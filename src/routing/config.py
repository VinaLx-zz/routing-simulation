from enum import Enum


class Address:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port


class Algorithm(Enum):
    DV = 1
    LS = 2
    LS_CENTRALIZE = 3
    LS_CONTROL = 4


class Config:

    def __init__(
            self,
            algorithm, hostname, self_addr, hns_addr,
            dead_timeout=180, update_interval=30):

        self.algorithm = algorithm
        self.hostname = hostname
        self.self_addr = self_addr
        self.hns_addr = hns_addr
        self.dead_timeout = dead_timeout
        self.update_interval = update_interval
