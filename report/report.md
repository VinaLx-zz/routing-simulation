# 路由系统模拟

> 2015级计算机网络期末项目

## 简介

在应用层模拟一个可以在运行时动态添加、减少节点的路由系统。

### 小组成员

- 15331344 薛明淇
- 15331348 颜泽鑫
- 15331371 姚志立
- 15331373 叶佳全

### Github Repository

[https://github.com/VinaLx/routing-simulation](https://github.com/VinaLx/routing-simulation)

## 具体需求

分别使用

- 类[Distance Vector Routing Protocal](https://en.wikipedia.org/wiki/Distance-vector_routing_protocol)(DV)
- 类[Link State Routing Protocal](https://en.wikipedia.org/wiki/Link-state_routing_protocol)(LS)
- 有中控系统的类LS协议

实现路由系统，在此系统中

1. 系统可抽象为一个带权的无向图，其中"主机"为"节点"，"主机之间的消息传递代价"为"边权"
2. 在系统稳定时，任意两个可达节点之间的消息传递选择的路径需要是最优的
3. 在系统运行时，可以向系统中添加节点，并指定新节点和原节点的某个子集中所有节点的代价，新系统满足要求2
4. 在系统运行时，可以从系统中删除节点，任何的消息传递不再可以经过被删除的节点，新系统满足要求2

## 实现

### 整体结构

在此路由系统中，单个主机的整体模块结构大体上如图所示：

![uml](./uml.png)

`RoutingTable`是全局单例的路由表，逻辑上内容是目标主机到下一跳主机的映射。因此可以通过`RoutingTable.get`以及其它方法来查询路由表内部封装的信息。

`Transport`负责封装底层的数据传输，例如`Transport.send`将各模块的结构化数据包装为数据包并且序列化，查询`RoutingTable`确定下一跳主机，并进行传输。而目标（下一跳）节点的`Transport`收到消息并进行反序列化后，将接收到的`data`和`type`共同交给`DataDispatcher`进行处理。`Transport`之外的模块不需要关心在进行底层数据传输时使用的报文格式和数据，可以只关心自身要传输的数据。

`DataDispatcher`负责分派`Transport`接收到的数据给各个模块，各个模块在初始化阶段向`DataDispatcher.register`注册回调，指明自身的`type`，在`DataDispatcher`收到数据后，会根据`type`查找登记过的`receiver`，将`data`进行分发。这样在`Transport`之外，根据各个模块的需要可以定义非提前约定的报文结构。

不同的`Algorithm`负责实现不同的路由协议的算法部分，例如`DV`协议，`Algorithm`会定期通过`Transport`向其它主机发送自身的路由信息，并且在通过`DataDispatcher`接收到邻居的路由信息后，对`RoutingTable`进行更新。其它算法类似，通过算法自身内部的逻辑，对路由表进行更新。除了`Algorithm`之外的模块不需要关心`Algorithm`使用的具体算法和协议也可以进行正常工作。

`NeighborTable`保存邻居的状态，逻辑上为邻居主机到代价的映射，在邻居内容更新时，`NeighborTable`会通知自己的观察者（这里唯一的观察者是算法，所有的算法都需要在邻居状态变化时对应地更新路由表）。

`Neighbors`负责管理当前主机的邻居状态，以及实现了主动添加、更新、删除邻居的协议逻辑，大致是在`Neighbors.update`以及`Neighbor.delete`调用后，通过与邻居的握手来完成邻居状态的变化。对于宕机主机的发现，由`Algorithm`通过逻辑实现，后详。

### Hostname Server (HNS)

`HNS`没有在单个主机的结构中标出，因为`HNS`是独立的一个主机。

#### Motivation

由于在程序的绝大部分我们关心的只是系统中主机和主机的逻辑关系，主机只需要有自己的逻辑标识即可，所以我们希望把主机的标识（主机名）和主机的网络地址分离开，只在传输数据的过程中，需要获取到主机名对应的网络地址，其他时候均可以完全使用主机名来操作。

#### 程序流程

`HNS`相对于主机而言，在逻辑上是永久存在的。在主机启动时，需要指定当前主机使用的`HNS`的地址，`Transport`会在启动时向`HNS`登记自身的主机和网络地址，之后加入系统的主机就可以在`HNS`上获知当前主机的存在。在`Transport`传输数据时，接收的`destination`为主机名，因此它需要先向`HNS`查询该主机名对应的网络地址来进行数据的传输，如果无法查询到主机的地址，那么无法进行数据的发送。

除了`Transport`以外，程序的其它模块完全不需要知道`HNS`的存在。

#### 具体实现

by @姚志立

### Transport具体实现

by @姚志立

<!-- 封包，拆包，传输数据包格式设计，其它操作等等 -->

### Algorithm具体实现

by @叶佳全

<!-- DV, LS, 中心化LS, 超时检测 -->

### Neighbors具体实现

by @薛明淇

Neighbors实现了更新（添加和改变）和删除邻居状态的逻辑。由于系统是一个无向图，因此两个节点之间的代价应该是相等的，所以`Neighbors`需要在可以容忍的错误范围内尽量保证节点之间邻居状态的一致性。这里采取与邻居进行两次握手来确定邻居关系。

#### 协议流程

假设`HostA`希望更新`HostB`的邻居状态，具体流程如下：

```
HostA ===[Cost]==> HostB

HostA将HostB加入等待集合中，启动timeout倒计时

HostB在自身邻居表中更新HostA的代价为`Cost`

1. HostA在timeout之前收到了HostB的回复

    HostA <==[Cost]=== HostB

    HostA在自身邻居表中更新HostB的代价为`Cost`

    HostA在等待集合中删除HostB

2. HostA在timeout之前没有收到HostB的回复

    HostA在等待集合中删除HostB
```

#### 其它

1. 主动删除邻居使用的流程与更新邻居一样，只不过这里实现上将`Cost`置为-1，并在接收时进行特殊判断。

2. 主动发起邻居状态变化的报文和回复邻居状态变化的报文在结构上是一样的，也就是说如果`HostA`在timeout过后收到了`HostB`的回复，`HostA`会认为这是个主动发起邻居状态变化的请求，并执行回复请求的逻辑，最终两台主机的邻居状态仍然一致。

3. 这里没有过多考虑安全性和错误处理的问题，因此传输数据的格式是十分简化的，并且协议上也仅仅用了两次握手而不是三次。

### 顶层模块 `Router`

顶层模块`Router`没有有在整体结构中展现出来。

`Router`做的事十分简单，通过接受当前主机的配置，来初始化下层的模块，并且根据下层所有模块所提供的接口，来向`Controller`和`View`提供对应的数据访问接口。

其中配置包含的项目有：

1. 自身的主机名 `hostname`
2. 自身的监听地址 `self_addr`
3. 使用的`HNS`的地址 `hns_addr`
4. 提供给`Algorithm`的主机超时时间 `dead_timeout`
5. 提供给`Algorithm`的路由表更新/信息发送间隔 `update_interval`
6. 如果使用的是中心化算法，中控系统的主机名 `controller_hostname`

提供的接口有：

``` python
# 启动路由器的运行
def run():

# 终止路由器的运行
def stop():

# 向`destination`发送普通的数据信息`message`
def send(destination: str, message: str):

# 获取当前主机认为的当前系统中存在的所有主机名
def get_alive() -> List[str]:

# 更新/添加邻居的状态
def update_neighbor(name: str, cost: int):

# 删除邻居
def remove_neighbor(name: str, cost: int):

# 获取当前路由表
# type Info = {next: str, cost: int}
def get_routing_table() -> Dict[str, Info]:
```

### UI

by @颜泽鑫

<!-- 实现，提供的功能，简单截图 -->

## 程序运行测试

### 场景

### 运行测试

#### DV

#### LS

#### 中心化LS