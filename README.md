###监控BTCChina的市场深度以及用户信息，并提供交易接口。

####监控市场行情:

可以运行`python monitor.py`来获取实时市场信息，信息每隔15s抓取一次。

####交易脚本: 

运行`python deal.py`来快速执行相关交易。建议采用多开Terminal tab/window或者使用Tmux等终端仿真软件来同时运行monitor与deal。一边监控，一边及时进行交易。

####Web访问

您可以自己配置好Flask运行环境以及web容器(uwsgi等)，Flask项目的入口文件为hello.py. 可以通过这个Web界面来监控价格及进行简单的交易。

####配置文件

配置文件名btc.conf，样例文件见btc.conf.sample. 建议设置两组不同的key分别用于查询及交易.

####其他问题？

发送邮件到[shieffan@gmail.com](mailto:shieffan@gmail.com)联系我即可。
