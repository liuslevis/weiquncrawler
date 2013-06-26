weiquncrawler
=============

  This is a crawler aiming at Sina Weiqun website's(WAP) information, including given Weiqun's posts, replies, users and their follow relation.
  Written in Python 2.7.1, store data in SQLite3.
  Relation-crawling part customized on Github Project sina_reptile.
  
  It crawls Weiqun info by the way of downloading the WAP website, and crawls user relation using API( OAuth 1.0 ).
  
  Most comments on source code is written in Chinese.
  
  
  Abstract
=============
  Weiqun is a novel social network service, serving current Weibo users, which can gather people with common interest or tags, providing a platform of communication for circles. Weiqun is also a information subscription mechanism, in which way after user joined a Weiqun, could mutually hear all people in this Weiqun posting information, namely Weiqun message, without having a Follow relationship with given user that they want to hear, vice versa, which is necessary in Weibo or Twitter. Comparing with strong connected relationship like Followship in Weibo or Twitter, relationship in Weiqun is weak connected as described before. Thus, comparing with user information behavior in Sina Weibo, it might be different in Weiqun.
  
  Given the Weiqun's API is not accessible currently, it's difficult to access Weiqun's data in large scale and efficient. This paper introduces a Weiqun crawler designed and implemented by author, which can crawl Weiqun information and user relation with high efficiency in large scale.
  

  Usage
=============

If you need one in English, just let me know.

环境要求:

操作系统:Windows XP 或以上,Mac OS 10.8 或以上,Linux

运行环境:安装 Python 2.7.3,JAVA 虚拟机 1.6 或以上,Apache Maven 工具。

环境配置:

1 安装 Python 2.7.3 IDE,Win 下安装包下载地址: http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi

2 安装 JAVA SDK(JDK) 1.6 或以上,确保在命令行输入 java -version 能查看版
本,下载地址: http://www.oracle.com/technetwork/java/javase/downloads/index.html

3 安装 Maven:Win 下,解压附带光盘 tool 文件夹的 maven 压缩文件到 c:\mvn3,
并把 c:\mvn3\bin 添加到计算机的 PATH,确保在命令行输入 mvn 或 mvn.bat 能启动 maven。

4 安装 SQLite3 数据库文件查看器:sqliteadmin,Win 下安装包见附带光盘 tool 文件夹。

使用说明:

1 网页爬虫:
注册微群用户,用 2.3.1 节的方法获取每个用户的 COOKIE,填在 simplecrawlerWAP.py 的『#填写用户 COOKIE』(默认已经填好)处。用浏览器登录刚注 册用户,加入欲爬取的微群。
在源代码根目录的文件 weiqun2download.txt 中填好欲爬取的微群 ID 和页数(已 经填好,按需改写),以空格隔开,可填写多行微群 ID、页数。

在终端进入源代码根目录执行命令:

python simplecrawlerWAP.py 

开始下载微群页, 下载好指定微群页后会下载微群消息的评论、转发等数据。若爬虫中断可重复执行该命令直到任务完成。爬虫同时爬取 weiqun2download.txt 的微群,每个微群都用默认 10 线程爬取,用户可在 simplecrawler.py 内的 threadnum 行修改线程数。

查看结果:

下载好的微群网页按页存储在名为『../微群 ID/微群 ID?page=页码』的文件夹中; 析取出的微博 DOM 文件储存路径『../微群 ID/微群 ID?page=页码/weibo 序号.html』; 下载到的评论、转发网页储存在路径『../微群 ID/微群 ID?page=页码/weibo 序号 /reply.html』、『../微群 ID/微群 ID?page=页码/weibo 序号/rt.html』;分析􏰀取出的 数据存在名为『../微群 ID/微群 ID.db』的 sqlite3 数据库文件中。
sqlite3 数据库文件可以用 sqliteadmin 软件查看。

2 用户关系爬虫:

在源代码根目录的文件 crawlertest.txt 中填好 API 密钥,填的行数即为爬虫线程。 密钥从 crawler.txt 中复制即可,每行为一个密钥。
在终端进入源代码根目录,执行 python sina_reptile.py。 查看结果:结果储存在『../users.db』sqlite3 数据库文件中。

3 生成用户关系对文本文件:

在源代码根目录执行:python getRelation.py
此时,脚本会读取 weiqun2download.txt 的微群号,从 微群 ID.db 读取用户,从
users.db 导出用户关系到文本文件『../weiqun/user_relation_微群 ID.txt』,文件格 式: 『源用户\t 目标用户\n\r』 (源用户 关注 目标用户)
