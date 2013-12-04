###监控BTCChina的市场深度以及用户信息，提供交易，止损等功能。

####1.监控市场行情:

可以运行`python monitor.py`来获取实时市场信息，信息每隔15s抓取一次。

####2.交易脚本: 

运行`python deal.py`来快速执行相关交易。建议采用多开`Terminal tab/window`或者使用`tmux`等终端仿真软件来同时运行`monitor`与`deal`。一边监控，一边及时进行交易。

####3.止损及止盈:

因为btcchina的挂单不提供止损卖出，所以来个后台程序来监控价格并提供止损服务是十分必要的。项目文件中的`daemon.py`为止损脚本。此脚本运行在`Daemon`模式下，打印出的Log文件在`tmp/daemon.log`里。此脚本每隔30s抓取一次当前交易价格，并读取`btc.conf`配置文件里的`risk section`提供的配置选项，根据配置文件设置及当前价格决定是继续持有还是卖出。

####4.Web访问

您可以自己配置好`Flask`运行环境以及web容器(`uwsgi`等)，`Flask`项目的入口文件为`hello.py`. 可以通过这个Web界面来监控价格及进行简单的交易。

####5.配置文件

配置文件名`btc.conf`，样例文件见`btc.conf.sample`.其中:

+ info,deal: 配置用于查询及交易的api key. 建议为info与deal设置两组不同的key分别用于查询及交易.
+ risk: 配置止损及止盈脚本的卖出条件:
  + `low_sell_ratio`: 当当前价格/最后一次买入价格<=low_sell_ratio时，止损卖出
  + `high_sell_ratio`: 当当前价格/最后一次买入价格>=high_sell_ratiio时，止盈卖出
  + `low_sell_price`: 当当前价格<=low_sell_price时，止损卖出
  + `high_sell_price`: 当当前价格>=high_sell_price时，止盈卖出
  + `fall_down_sell`: 当最近两次查询的价格落差(30s内)>fall_down_sell时，卖出所有。
  + 当以上选项不存在或者设置为0时，表示不使用这个卖出条件。
+ user: 当使用Flask Web访问时，设置相关的登录用户名及密码。

####6.其他问题？

发送邮件到[shieffan@gmail.com](mailto:shieffan@gmail.com)联系我即可。
