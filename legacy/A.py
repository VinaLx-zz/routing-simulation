import router
import time
import hns
import json

def main():
	hns1 = hns.HNS('127.0.0.1', 9999)
	hns1.configure_by_dict({
		'A':('127.0.0.1', 8888),
		'B':('127.0.0.1', 8889),
		'C':('127.0.0.1', 8890),
		'D':('127.0.0.1', 8891)
		})

	routerA = router.RouterCtrl('A', '127.0.0.1', 8888, '127.0.0.1', 9999)
	# routerA.configure_mapping_table({'A':('127.0.0.1', 8888), 'C':('127.0.0.1', 8890), 'B':('127.0.0.1', 8889)})
	routerA.init(router.RouterCtrl.LS, 20, 120)
	routerA.add_neighbor('B', 2)
	routerA.add_neighbor('C', 1)
	routerA.run()

	routerB = router.RouterCtrl('B', '127.0.0.1', 8889, '127.0.0.1', 9999)
	# routerB.configure_mapping_table({'A':('127.0.0.1', 8888), 'B':('127.0.0.1', 8889), 'D':('127.0.0.1', 8891)})
	routerB.init(router.RouterCtrl.LS, 20, 120)
	routerB.add_neighbor('A', 2)
	routerB.add_neighbor('D', 3)
	routerB.run()

	routerC = router.RouterCtrl('C', '127.0.0.1', 8890, '127.0.0.1', 9999)
	# routerC.configure_mapping_table({'A':('127.0.0.1', 8888), 'C':('127.0.0.1', 8890), 'D':('127.0.0.1', 8891)})
	routerC.init(router.RouterCtrl.LS, 20, 120)
	routerC.add_neighbor('A', 1)
	routerC.add_neighbor('D', 4)
	routerC.run()
	count = 0
	# while count < 6:
	# 	print('C ready to send message')
	# 	routerC.send(routerC.get_self_name(), 'B', 0, 'hello world')
	# 	count = count + 1
	# 	time.sleep(10)

	routerD = router.RouterCtrl('D', '127.0.0.1', 8891, '127.0.0.1', 9999)
	# routerD.configure_mapping_table({'D':('127.0.0.1', 8891), 'B':('127.0.0.1', 8889), 'C':('127.0.0.1', 8890)})
	routerD.init(router.RouterCtrl.LS, 20, 120)
	routerD.add_neighbor('B', 3)
	routerD.add_neighbor('C', 4)
	routerD.run()

if __name__ == '__main__':
	main()