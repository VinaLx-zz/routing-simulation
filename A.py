import router
import time

def main():
	routerA = router.RouterCtrl('A', '127.0.0.1', 8888)
	routerA.configure_mapping_table({'A':('127.0.0.1', 8888), 'C':('127.0.0.1', 8890), 'B':('127.0.0.1', 8889)})
	routerA.init(router.RouterCtrl.LS, 10, 80)
	routerA.add_neighbor('B', 2)
	routerA.add_neighbor('C', 1)
	routerA.run()

	routerB = router.RouterCtrl('B', '127.0.0.1', 8889)
	routerB.configure_mapping_table({'A':('127.0.0.1', 8888), 'B':('127.0.0.1', 8889), 'D':('127.0.0.1', 8891)})
	routerB.init(router.RouterCtrl.LS, 10, 80)
	routerB.add_neighbor('A', 2)
	routerB.add_neighbor('D', 3)
	routerB.run()

	routerC = router.RouterCtrl('C', '127.0.0.1', 8890)
	routerC.configure_mapping_table({'A':('127.0.0.1', 8888), 'C':('127.0.0.1', 8890), 'D':('127.0.0.1', 8891)})
	routerC.init(router.RouterCtrl.LS, 10, 80)
	routerC.add_neighbor('A', 1)
	routerC.add_neighbor('D', 4)
	routerC.run()
	count = 0
	# while count < 6:
	# 	print('C ready to send message')
	# 	routerC.send(routerC.get_self_name(), 'B', 0, 'hello world')
	# 	count = count + 1
	# 	time.sleep(10)

	routerD = router.RouterCtrl('D', '127.0.0.1', 8891)
	routerD.configure_mapping_table({'D':('127.0.0.1', 8891), 'B':('127.0.0.1', 8889), 'C':('127.0.0.1', 8890)})
	routerD.init(router.RouterCtrl.LS, 10, 80)
	routerD.add_neighbor('B', 3)
	routerD.add_neighbor('C', 4)
	routerD.run()

	time.sleep(60)
	print('routerA shutdown')
	routerA.shutdown()

if __name__ == '__main__':
	main()