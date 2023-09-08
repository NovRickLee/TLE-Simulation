# TLE-Simulation
Pseudo real-time simulation of satellite position based on sgp4 dynamic model\
该项目希望实现自动抓取卫星TLE数据、模拟卫星在大地坐标系下的轨迹与坐标并绘制一个伪实时的可视化图片。
## 数据来源
项目所需的数据及其来源：\
    TLE数据：来自http://celestrak.org/；可以利用卫星编码查询最新的TLE数据；\
    AE8_MIN_0.1MeV.txt：欧空局AE8空间辐射模型，在太阳活动最弱情况下海拔500km的模拟数据；\
    coord.txt：AE8_MIN_0.1MeV.txt中对空间格点划分的数据。
## 伪实时
如简介所述，该项目对卫星位置的可视化是伪实时的。项目会在启动时计算好未来约5700s的卫星位置数据，在每个小时的最后一分钟里再好计算未来5700s的卫星位置。
## 问题
程序的主要开销在于卫星坐标由TEME坐标系向大地坐标系的转换。不知道是不是我的代码问题，astropy库的转换效率很低。
