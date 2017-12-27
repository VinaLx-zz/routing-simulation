# routing-simulation
computer networking final project

![Stary 2017-12-27 at 10.35.52 PM](http://o7d2h0gjo.bkt.clouddn.com/2017-12-27-Stary%202017-12-27%20at%2010.35.52%20PM.png)

# API
## class RouterCtrl:
1. `__init__((str)self_name, (str)self_ip, (int)self_port, (str)hns_ip, (int)hns_port)`

    eg: `routerA = RouterCtrl('A', '127.0.0.1', 8000, '127.0.0.1', '9000')`

2. `send((str)destination, (any type)data)`

    eg: `routerA.send('B', 'Hello World')`

## class hns:
1. `__init__((str)self_ip, (int)self_port)`

    eg: `hns_ = hns.HNS('127.0.0.1', 9000)`

2. `configure_by_name((str)name, (str)ip, (int)port)`

    eg: `hns_.configure_by_name('A', '127.0.0.1', 8000)`

3. `configure_by_dict((dict)mapping_table)`

    eg:
```
hns_.configure_by_dict({
    'A': ('127.0.0.1', 8000),
    'B': ('127.0.0.1', 8001)
})
```
