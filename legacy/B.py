import router
import time

def main():
    routerA = router.RouterCtrl('A', '127.0.0.1', 8888)
    routerA.configure_mapping_table({'A':('127.0.0.1', 8888), 'B':('127.0.0.1', 8889), 'C':('127.0.0.1', 8890), 'D':('127.0.0.1', 8891), 'E':('127.0.0.1', 8892)})
    routerA.init(router.RouterCtrl.CENTRAL_LS, 10, 80)
    routerA.set_controller('E')
    routerA.add_neighbor('B', 2)
    routerA.add_neighbor('C', 1)
    routerA.add_neighbor('E', 1)
    routerA.run()

    routerB = router.RouterCtrl('B', '127.0.0.1', 8889)
    routerB.configure_mapping_table({'A':('127.0.0.1', 8888), 'B':('127.0.0.1', 8889), 'C':('127.0.0.1', 8890), 'D':('127.0.0.1', 8891), 'E':('127.0.0.1', 8892)})
    routerB.init(router.RouterCtrl.CENTRAL_LS, 10, 80)
    routerB.set_controller('E')
    routerB.add_neighbor('A', 2)
    routerB.add_neighbor('C', 1)    
    routerB.add_neighbor('D', 3)
    routerB.add_neighbor('E', 1)
    routerB.run()

    routerC = router.RouterCtrl('C', '127.0.0.1', 8890)
    routerC.configure_mapping_table({'A':('127.0.0.1', 8888), 'B':('127.0.0.1', 8889), 'C':('127.0.0.1', 8890), 'D':('127.0.0.1', 8891), 'E':('127.0.0.1', 8892)})
    routerC.init(router.RouterCtrl.CENTRAL_LS, 10, 80)
    routerC.set_controller('E')
    routerC.add_neighbor('A', 1)
    routerC.add_neighbor('B', 1)
    routerC.add_neighbor('D', 7)
    routerC.add_neighbor('E', 1)
    routerC.run()
    count = 0
    # while count < 6:
    # 	print('C ready to send message')
    # 	routerC.send(routerC.get_self_name(), 'B', 0, 'hello world')
    # 	count = count + 1
    # 	time.sleep(10)

    routerD = router.RouterCtrl('D', '127.0.0.1', 8891)
    routerD.configure_mapping_table({'A':('127.0.0.1', 8888), 'B':('127.0.0.1', 8889), 'C':('127.0.0.1', 8890), 'D':('127.0.0.1', 8891), 'E':('127.0.0.1', 8892)})
    routerD.init(router.RouterCtrl.CENTRAL_LS, 10, 80)
    routerD.set_controller('E')
    routerD.add_neighbor('B', 3)
    routerD.add_neighbor('C', 7)
    routerD.add_neighbor('E', 1)
    routerD.run()

    routerE = router.RouterCtrl('E', '127.0.0.1', 8892)
    routerE.configure_mapping_table({'A':('127.0.0.1', 8888), 'B':('127.0.0.1', 8889), 'C':('127.0.0.1', 8890), 'D':('127.0.0.1', 8891), 'E':('127.0.0.1', 8892)})
    routerE.init(router.RouterCtrl.CENTRAL_LS, 10, 80)
    routerE.add_neighbor('A', 1)
    routerE.add_neighbor('B', 1)
    routerE.add_neighbor('C', 1)
    routerE.add_neighbor('D', 1)
    routerE.run(True)

    time.sleep(60)
    print('routerA shutdown')
    routerA.shutdown()

    # time.sleep(300)
    # print('link B/C update cost')
    # routerB.update_neighbor('C', 5)
    # routerC.update_neighbor('B', 5)

    time.sleep(300)
    print('routerA restarting.')
    routerA.run()

if __name__ == '__main__':
    main()