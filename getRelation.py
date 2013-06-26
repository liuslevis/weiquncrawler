# # -*- coding: utf-8 -*-  
import sys


"""
这是一个新浪微群爬虫。目前只有命令行界面。
使用方法：下回分解。
"""
__author__ =  'David Lau'
__version__=  '0.1'
__nonsense__ = 'weiqun crawler,relation txt generator'

#导入sina_reptile
from sina_reptile import *
from simplecrawlerWAP import *


        
                
if __name__ == '__main__':
    LOGIN_URL = 'http://weibo.cn' #测试用户登陆用
    
    #!编码重要:设置python(2.7.3)的内部处理encoding使用utf-8(默认ascii),以确保能在mac命令行下python执行本文件
    #详见http://docs.python.org/2/howto/unicode.html
    reload(sys)
    sys.setdefaultencoding('utf-8')
    print '系统编码：'
    print sys.getdefaultencoding()
    
        #Trap time stamp    
    LAST_TRAP_TIME = datetime.datetime.now()
    #cookie
    #填写用户COOKIE
    COOKIE1 = 'gsid_CTandWM=4KxsCpOz1GZCmdnhIRfo3dyGpfe;_WEIBO_UID=3231589944'#david
    COOKIE2 = '_WEIBO_UID=3231589944; gsid_CTandWM=4KigCpOz1kJGN62tgSyo96K5D9h'#jion
    COOKIE3 = '_WEIBO_UID=3231589944; gsid_CTandWM=4KfJCpOz1RtwETBsrTJiC7bgieU'#mie
    COOKIE4 = 'gsid_CTandWM=4KHACpOz15FImpwmD6Dq2dJ48aI; _WEIBO_UID=3271500664'#miemiemie
    COOKIE5 = '_WEIBO_UID=3271500664; gsid_CTandWM=4KNhCpOz1mRs5r4AA9S1adTAz7N'#my reg
    COOKIE = COOKIE5
    COOKIES = [COOKIE1,COOKIE2,COOKIE3,COOKIE4,COOKIE5]
    HEADERS_LOGIN = { "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",\
                "Accept-Charset":"GBK,utf-8;q=0.7,*;q=0.3",\
                'Accept-Encoding':'gzip,deflate,sdch',#这里告知服务器，可以用gzip压缩包传递html\ 
                'Accept-Language':'zh-CN,zh;q=0.8',\
                "Connection":"keep-alive",\
                "Host":"weibo.cn",\
                "Cookie": COOKIE,\
                "Referer":'''http://newlogin.sina.cn/crossDomain/?g=4KigCpOz1kJGN62tgSyo96K5D9h&t=1364395377&m=cdba&r=&u=http%3A%2F%2Fweibo.cn%2F%3Fgsid%3D4KigCpOz1kJGN62tgSyo96K5D9h%26vt%3D4&cross=1&vt=4''',\
                "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22",\
                }
          
    HEADERS_WEIQUN = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",\
                    'Accept-Encoding':'gzip,deflate',#这里告知服务器，可以用gzip压缩包传递html\ 
                    'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',\
                    'Connection':'keep-alive',\
                    'Cookie':COOKIE,\
                    'Host':'q.weibo.cn',\
                    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:17.0) Gecko/20100101 Firefox/17.0',\
                }    
                
    userdbname = '../users.db'
    weiquns = [] 
    startpage=1

    
                   
    #读取 weiqun2download.txt 的微群号,下载总页数
    weiqunparas = []
    weiqunids = []     
    print '从weiqun2download.txt读取准备下载的weiqunids:'
    weiqunlist = 'weiqun2download.txt'
    with open(weiqunlist) as f:
        for i in f.readlines():
            res = re.sub('#',' ',i).split(' ')
            weiqunid = res[0].strip()
            endpage = int(res[1].strip())
            startpage = 1
            print  'weiqunid:',weiqunid
            print  'page:',startpage,'~',endpage
            weiqunparas.append( (weiqunid,startpage,endpage) )

        
    
    #wrap 微群crawler参数        
    for para in weiqunparas:
        weiqunid,startpage,endpage = para
        weiqun = ('../weiqun/%d'%int(weiqunid),'../weiqun/%d.db'%int(weiqunid),userdbname,'../users',weiqunid,startpage,endpage,LOGIN_URL)
        weiquns.append(weiqun)
        weiqunids.append(weiqunid)
            
    #初始化多个crawler
    crawlers = []
    for weiqun in weiquns[0:]:
        savedir,weibodbname,userdbname,usersdir,weiqunid,startpage,endpage,login_url = weiqun
    
        #初始化爬虫类
        crawler = Weiqun_crawler(weibodbname,userdbname,usersdir,savedir,weiqunid,startpage,endpage,HEADERS_WEIQUN,HEADERS_LOGIN,COOKIES,login_url ,4)
        crawlers.append(crawler)
        
    for crawler in crawlers:
            #--------------------------从微群db中读取用户，从users.db中读取用户关系，生成用户关系txt文件，格式：FolloerID\tUserID\n----------------------------- 
            crawler.get_user_relation_txt()
            
