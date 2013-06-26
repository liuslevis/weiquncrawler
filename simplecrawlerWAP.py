# # -*- coding: utf-8 -*-  
import sys


"""
这是一个新浪微群爬虫。目前只有命令行界面。
使用方法：下回分解。
"""
__author__ =  'David Lau'
__version__=  '0.1'
__nonsense__ = 'weiqun crawler'

#导入sina_reptile
from sina_reptile import *

#调试HTTP Web服务
import httplib
httplib.HTTPConnection.debuglevel = 0

#数据库 Beautiful Soup库
import sqlite3 as sqlite
from bs4 import BeautifulSoup

#url处理
import urlparse

#处理gzip
import StringIO
import StringIO
import gzip
import urllib2
import re
import os
import sys
import datetime
import time
import itertools
import termios
import fcntl
"""
Login to Sina Weibo with cookie
"""
PAGE_REQUEST_ERROR = '请求页不存在'
PAGE_REDIRECT = '如果没有自动跳转,请'
NOBODY_POST_THIS_PAGE = '你加入的群还没有人说话!'
NO_REPLY = '还没有人针对这条微博发表评论!'
WEIBO_SQUARE ='微博广场'
USERPROFILE_PREFIX = 'http://weibo.cn/%s/profile'#uid个人主页
#一般fans/follows第i页的url: http://weibo.cn/uid/fans?page=[i]
FANPAGE_PREFIX = 'http://weibo.cn/%s/fans'#uid的粉丝用户页面
FOPAGE_PREFIX = 'http://weibo.cn/%s/follow'#uid的关注用户页面
FANPAGE_SURFFIX = '?page=%s&st=c23d'
FOPAGE_SURFFIX = '?page=%s&st=c23d'
WEIBO_PER_PAGE = 10

MEET_TRAP = 99

#trap times 记录次数 到一定值则换cookie
TRAP_TIMES = 0


WEIQUN_BASE='http://q.weibo.cn/group/'   

    
def fromUTF8toSysCoding(html):
    '''
    decode and encode with sysencoding
    '''
    syscodetype = sys.getfilesystemencoding()
    return html.decode('utf-8').encode(syscodetype)

def degzip(compresseddata):
    '''
    decompress gzip (html) file,return ungzip html string
    '''
    if(compresseddata[0:3]=='\x1f\x8b\x08'):
        compressedstream = StringIO.StringIO(compresseddata)
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        html = gzipper.read() 
        return html
    else:
        return compresseddata
    
def storehtml(html,path,url=None,showdetail=True):
    '''
    将html存到磁盘path (html来源url)
    #没有文件夹则建立
    '''
    (basename,filename) = os.path.split(path)
    if not os.path.exists(basename):
        os.makedirs(basename)
    #建立文件
    try:
        fd = open(path,'w')#w+模式代表截断（或清空）文件，然后打开文件用于写
        fd.write(html)
        if showdetail:
            print "网页保存到本地"+path+',\turl='+url
    except Exception,E:
        if showdetail:
            print "网页保存到本地"+path+',\turl='+url
    finally:
        fd.close()
      
def urlprocessor(url,header,absUrl=True):
    '''
    带cookie(header)下载url页面html，检查html是否gzip压缩，有则解压；
    需要用Firebug查看浏览器访问时发送的GET headers（包括cookie），模拟，才可以正常访问；否则返回无法找到该页。
    返回: None 错误
         html 正常下载页面内容
    '''
    try:
        req = urllib2.Request(url, headers=header)
        f = urllib2.urlopen(req)
        html = f.read()
        '''
        #解压缩get得到的网页gzip包
        if(f.headers.get('Content-Encoding') == 'gzip'):
            html = degzip(html)

        #把相对地址替换成绝对地址
        if absUrl:
            html = getAbsUrl(url,html)   
        return html 
        '''
    except Exception,E:
        print "urlprocessor():下载页面错误："+url+'，错误代码:'+str(E)
        return None
    
    if html: 
        #解压缩get得到的网页gzip包
        if(f.headers.get('Content-Encoding') == 'gzip'):
            html = degzip(html)
    
        #把相对地址替换成绝对地址
        if absUrl:
            html = getAbsUrl(url,html)   
        
        return html
    else:
        return None
    
def getAbsUrl(base,html):
    '''
    用re把html内的相对地址替换成绝对地址,返回带绝对地址的html
    '''
    regex = '<a href="(.+?)"'
    reobj = re.compile(regex)
    #找出所有相对地址，存放在reladdrList中
    reladdrList = reobj.findall(html)
    for reladdr in reladdrList:
        if ':'  not in reladdr:
            #补全相对地址为绝对地址url,用re替换
            url = urlparse.urljoin(base,reladdr)
            #print "getAbsUrl()处理相对地址："+reladdr
            html = html.replace('<a href="'+reladdr,'<a href="'+url)
    return html
    
def testgetAbsUrl():
    '''
    测试testgetAbsUrl
    '''
    html = '''<div><a href="/profile/1808877652">Nulooper</a><span class="ctt">:NLP初学者报道，希望多多指教</span>&nbsp;<a href="/group/viewRt/225241/103r08nr6th">转发</a>&nbsp;<a href="/group/review/225241/103r08nr6th?&amp;#cmtfrm" class="cc">评论[0]</a>&nbsp;&nbsp;<span class="ct">01月26日 19:30</span></div>'''
    weiqunUrl = 'http://q.weibo.cn/group/225241/'
    html = getAbsUrl(weiqunUrl,html)
    print html

class Weiqun_crawler:
    '''
    微群爬虫类
    '''
    def __init__(self,weibodbname,userdbname,usersdir,savedir,weiqunID,startpage,endpage,headers_weiqun,headers_login,cookies_list,loginurl,begin_with_cookie_n=None):
        '''
        初始化类，设置保存地址，微群号，连接数据库
        '''
        print '----------- 初始化微群爬虫 id:%s -----------'%weiqunID
        #header cookie
        self.begin_with_cookie_n = begin_with_cookie_n
        self.cookies = []
        self.cookies.extend(cookies_list)
        self.cookie_iter = itertools.cycle(self.cookies)
        self.headers_weiqun = headers_weiqun
        self.headers_login = headers_login
        self.cur_cookie = ''
        self.change_cookie_times = 0 #改变cookie的次数
        self.loginurl= loginurl
        self.init_cookie_headers()
        
        #下载网页保存地址
        self.savedir = savedir
        self.weiqunID = str(weiqunID)
        self.usersdir = usersdir
        #扫微群页数
        self.startpage = startpage
        self.endpage = endpage
        #数据库名称
        self.weibodbname = weibodbname
        self.userdbname = userdbname
        #设置微博数据库
        print self.weibodbname
        self.con_weibo = sqlite.connect(self.weibodbname)
        self.cur_weibo = self.con_weibo.cursor()
        #设置用户数据库
        self.con_user = sqlite.connect(self.userdbname)
        self.cur_user = self.con_user.cursor()
        #初始化db表
        self.createweibostable()
        self.createuserstable()
        
        #析取微博信息
        self.allweiboinfos = [] #weiboinfo={raw,id,content...见db table weibos}
        self.replyinfos=[]#储存replyinfo{weiboid,...}(同数据库中weibos的item)
        self.rtinfos=[]#同上
        self.profiles=[]#储存profile={userid,username,weibos微博数,followers粉丝数,followings关注数}
        self.failed_reply_paths=[]#储存分析失败的reply.html路径，需要重新爬取
        self.failed_rt_paths=[]#同上
        #给crawler.cralw..函数返回用 或db网页下载状态用
        self.STATUS_FAILED = 2
        self.STATUS_DOWNLOADED = 1
        self.STATUS_UNDOWNLOAD = 0
        #上次爬虫下载的内容,用与self.is_trap
        self.last_crawl_html = ''
        
        #要下载的微群页表 类型ints
        self.weiqun_pages2download=[]

    def __del__(self):
        '''
        关闭数据库连接
        '''
        #print '----------- 销毁微群爬虫 id:%s -----------'%self.weiqunID
        self.con_weibo.close()
        self.con_user.close()
        
        
    def init_cookie_headers(self):
        #设置开始爬行使用的用户COOKIE
        if self.begin_with_cookie_n is not None: 
            if len(self.cookies) >= self.begin_with_cookie_n:
                if self.begin_with_cookie_n >= 0:
                    self.cur_cookie = self.cookies[self.begin_with_cookie_n]
                    self.headers_weiqun.update({'Cookie':self.cur_cookie})
                    self.headers_login.update({'Cookie':self.cur_cookie})
                    #print 'INIT COOKIE!!!!!!!!!!!!!!!!!!!!!'
                    #self.test_login('http://weibo.cn')
                    return
        #如果没有设置开始用户,则佢第0个COOKIE        
        self.cur_cookie = self.cookies[0]
        self.headers_weiqun.update({'Cookie':self.cur_cookie})
        self.headers_login.update({'Cookie':self.cur_cookie})
        #print 'INIT COOKIE!!!!!!!!!!!!!!!!!!!!!'
        #self.test_login('http://weibo.cn')
        
    def change_cookie_headers(self):
        self.cur_cookie = self.cookie_iter.next()
        self.headers_weiqun.update({'Cookie':self.cur_cookie})
        self.headers_login.update({'Cookie':self.cur_cookie})
        print 'CHANGE COOKIE!!!!!!!!!!!!!!!!!!!!!'
        self.test_login('http://weibo.cn')
        self.change_cookie_times+=1

    def get_user_relation_txt(self):
        '''
        从指定self.微群id 的db获取users,从user.db获取users的关系: follower_uid target_uid
        输出: user_relation_weiqunID.txt (Win CRLF Ansi?)
                第一个用户id标示源用户id，第二个用户id标示目标用户id，源用户关注目标用户
             user_list_all_weiqunID.txt (CRLF)
                每行是所有在关系里出现过的uid unique
        返回:True 成功
            False 失败 读取数据库时
            None 无查询结果
        '''
        print 'get_user_relation_txt: 正在生成用户关系对txt  weiqun=%s'% str(self.weiqunID)
        count = 0
        #选择某微群的所有用户
        sql_weiqundb = ''' SELECT DISTINCT userid FROM weibos ;'''
        #选择某用户的所有关系
        sql_usersdb = ''' SELECT followerid,userid FROM relation WHERE userid=='%s' or followerid=='%s' ;'''
        
        #-----------获取微群db的用户列表--------------------------------------------------------- 
        try:
            self.cur_weibo.execute(sql_weiqundb)
            self.dbcommit()
        except Exception,E:
            print 'get_user_relation_txt 数据库操作错误sql:%s'%sql_weiqundb
            print E
            return False
        userids = []
        res = self.cur_weibo.fetchall()
        if len(res)<1:#查询不到东西 返回None
            print 'get_user_relation_txt:微群%s的数据库%s中没有用户'%(self.weiqunID,self.weiqunID+'.db')
            return None            
        else:#有查询结果(有用户) ,添加到用户列表中userids
            for row in res:
                userid, = row
                #print userid
                #print type(userid)
                if userid not in userids:
                    userids.append(str(userid))
        
        #-----------获取users.db的用户关系--------------------------------------------------------- 
        print 'get_user_relation_txt:正在从users.db读取%d个用户的关系'%len(userids)
        relations = []
        for userid in userids:
            #print '\t获取用户关系uid:%s'%str(userid)
            try:
                self.cur_user.execute(sql_usersdb % (userid,userid))
                self.dbcommit()
            except Exception,E:
                print 'get_user_relation_txt 数据库操作错误sql:%s'%(sql_usersdb % (userid,userid))
                print E
                return False
            res2 = self.cur_user.fetchall()
            
            if len(res2)<1:#查询不到某个用户的关系 跳过
                print 'get_user_relation_txt:users.db中没有微群:%s,uid=%s的用户关系'%(self.weiqunID+'.db',userid)
                #return None
                continue            
            else:#有查询结果(有用户关系) ,添加到用户列表中userids
                for row in res2:
                    followerid,userid = row
                    relation = (followerid,userid)
                    #!!!!!!!!! 可能有重复的 !!!!!!!!!!!
                    relations.append(relation)
                    count+=1
                
        #写到文件中:user_relation_weiqunID.txt (CRLF)
        path = '../weiqun/user_relation_%s.txt' % str(self.weiqunID)
        txtlines = []
        relations.sort()
        for rela in relations:
            followerid,userid = rela
            txtline = str(followerid) + '\t' + str(userid) +'\r\n'
            txtlines.append(txtline)
        with open(path,'w') as f:
            f.writelines(txtlines)
            f.close()
            
        #写到文件中:user_list_all_weiqunID.txt (CRLF)
        usernum=0
        path = '../weiqun/user_list_all_%s.txt' % str(self.weiqunID)
        txtlines = []
        all_uid = set([])#use set as dinstinct list,fast!!
        for rela in relations:
            followerid,userid = rela
            if followerid not in all_uid:
                all_uid.add(followerid)
            if userid not in all_uid:
                all_uid.add(userid) 
        
        all_uid = [i for i in all_uid]
        all_uid.sort()
        for userid in all_uid:
            txtline = str(userid) +'\r\n'
            usernum+=1
            txtlines.append(txtline)
            
        with open(path,'w') as f:
            f.writelines(txtlines)
            f.close()
            
                
        print 'got_user_relation_txt: weiqun=%s'% (str(self.weiqunID))
        print '\t有关注关系',count
        print '\t所有用户(出现在关注关系中的)',usernum
        
    def load_weiqun_pages2download(self):
        '''
        任务:返回未下载\陷阱的微群页(微群id=self.weiqunID),
            更改:
            self.weiqun_pages2download[] of int(page)s
        返回:self.weiqun_pages2download[]
            False 失败
        '''
        print 'load_weiqun_pages2download:读取微群%s的下载列表'%self.weiqunID
        #path, url, status, type='weiqunpage',userid=微群id
        sql = '''SELECT path,url,status,type,userid,page FROM download WHERE userid == '%s' and type=='%s' '''%(str(self.weiqunID),'weiqunpage')
        try:
            self.cur_user.execute(sql)
            self.dbcommit()
        except Exception,E:
            print 'load_download_db_state数据库操作错误sql:%s'%sql
            print E
            return False

        res = self.cur_user.fetchall()
        
        if len(res)<1:#查询不到东西 返回[startpage ~ endpage]
            allpages = [i for i in range(self.startpage, self.endpage)]
            self.weiqun_pages2download = allpages
            return self.weiqun_pages2download
            
        else:#有查询结果(有下载过) 
            self.weiqun_pages2download = [i for i in range(self.startpage, self.endpage)]
            #将已下载过的pages从上表剔除
            for row in res:
                path,url,status,type,weiqunid,page = row
                #如果 没有下载过page 且 page不在weiqun_pages2download中,加入
                if status==self.STATUS_DOWNLOADED and \
                    page in self.weiqun_pages2download:
                    if page < self.endpage:#db记录未下载页数要小于传参的endpage页数
                        self.weiqun_pages2download.remove(page)

            
        
            print 'load_weiqun_pages2download:共%d个未下载'%len(self.weiqun_pages2download) 
            
            return self.weiqun_pages2download
 
    def update_download_db_state(self,url,path,type,status,page=None,userid=None,now=None):
        if now is None:
            now = datetime.datetime.now()
        try:
            self.cur_user.execute('''REPLACE INTO download(userid,type,page,status,url,path) VALUES ('%s','%s',%d,%d,'%s','%s');'''%(str(userid),str(type),int(page),int(status),str(url),str(path)))
            self.dbcommit()
        except Exception,E:
            print 'update_download_db_state:无法replace项'
            print E
            return False
        return True
    
    def load_download_db_state(self,url,path):
        '''
        任务:给定PK:url,path,查询self.userdbname的table:download
        返回:(userid,type,page,status,url,path,randurl,datetime) (最后一项)符合的项,
            None 若无查询结果
        '''
        
        sql = '''SELECT userid,type,page,status,url,path,randurl FROM download WHERE url == '%s' and path== '%s' '''%(str(url),str(path))
        try:
            self.cur_user.execute(sql)
            self.dbcommit()
        except Exception,E:
            print 'load_download_db_state数据库操作错误sql:%s'%sql
            print E
            return None

        res = self.cur_user.fetchall()
        if len(res)<1:#查询不到东西
            return None
        
        if len(res)>1:
            print 'load_download_db_state得到多个sql查询结果,返回最后一个结果'
        for row in res:
            #print type(row)#tuple
            userid,type,page,status,url,path,randurl = row
        
        return userid,type,page,status,url,path,randurl,None
        
    def update_download_list(self,endpage=None,weiqunid='',showdetail = False):
        '''
        任务:将给定微群id的 已/未下载的微群页记录到下载列表self.userdbname -> download table中
        返回:pages_undownload[] 未下载的微群页数列表
        '''
        pages_undownload = []
        #若参数没指定微群id则用crawler自己的微群id   endpage
        if weiqunid == '':    
            weiqunid = str(self.weiqunID)
        if endpage == None:
            endpage = self.endpage
    
        #开始扫描
        for i in range(1,endpage+1):
            weiqunUrl = WEIQUN_BASE + str(weiqunid)
            pageurl = weiqunUrl + '?page=' + str(i)
            path = self.savedir + '/' + str(weiqunid) +  '?page=' + str(i) + '.html'
            
            #判断是否下载过
            try:
                f = open(path,'r')
                localhtml=''
                lines = f.readlines()
                for line in lines:
                    localhtml+=line
                #如果下载过(且不是陷阱页)就不下载了 返回True
                #return True
                if not self.is_weiqun_page_trap(localhtml,showdetail=False):
                    if showdetail:
                        print '\t下载过且非陷阱,更新download table状态:已下载:%s,长度%d'%(path,len(localhtml))
                    # replace download table状态:已下载
                    # 格式path, url, status=1, type='weiqunpage',userid=微群id,page=i
                    succ = self.update_download_db_state(pageurl,path,type='weiqunpage',status=self.STATUS_DOWNLOADED,page=i,userid=weiqunid)
                    if not succ:
                        print 'update_download_list:更新数据库失败'
                else:
                    #if showdetail:
                    print '\t下了陷阱,更新download table状态:下载失败:%s,长度%d'%(path,len(localhtml))
                    # replace download table状态:陷阱
                    # 格式path, url, status=2, type='weiqunpage',userid=微群id,page=i
                    pages_undownload.append(i)
                    succ = self.update_download_db_state(pageurl,path,type='weiqunpage',status=self.STATUS_FAILED,page=i,userid=weiqunid)
                    if not succ:
                        print 'update_download_list:更新数据库失败'
            except Exception as e:
                #if showdetail:
                print '\t没下载过,更新download table状态:待下载:%s'%(path)
                #没有这个文件,改download table状态:待下载
                # 格式path, url, status=0, type='weiqunpage',userid=微群id,page=i
                pages_undownload.append(i)
                succ = self.update_download_db_state(pageurl,path,type='weiqunpage',status=self.STATUS_UNDOWNLOAD,page=i,userid=weiqunid)
                if not succ:
                        print 'update_download_list:更新数据库失败'
                        
        return pages_undownload
        
    def weiqun_crawl_page(self,i):
        '''
        爬虫方法，爬取微群=weiqunID的i页的页面，保存到路径self.savedir内。(如果下载过且非陷阱则跳过)
        保存格式：self.savedir/weiqunID?page=i，i是页码
            修改:下载列表状态:成功下载
        返回:True
            False
        '''
        weiqunUrl = WEIQUN_BASE + str(self.weiqunID)
        pageurl = weiqunUrl + '?page=' + str(i)
        #path = self.savedir/weiqunID?page=2.html,same as http://q.weiqun.cn/group/weiqunID?page=2
        path = self.savedir + '/' + str(self.weiqunID) +  '?page=' + str(i) + '.html'
        
        '''#用update_download_list 代替判断
        #判断是否下载过
        try:
            f = open(path,'r')
            localhtml=''
            lines = f.readlines()
            for line in lines:
                localhtml+=line
            #如果下载过(且不是陷阱页)就不下载了 返回True
            #return True
            if not self.is_weiqun_page_trap(localhtml):
                print '\t下载过且非陷阱,跳过:%s,长度%d'%(path,len(localhtml))
                return True
        except Exception as e:
            pass
        '''
        
        #下载url的html,把绝对地址转换成相对地址
        pagehtml = urlprocessor(pageurl,self.headers_weiqun,absUrl=True)
        #判断是否是trap
        if pagehtml:
            if self.is_weiqun_page_trap(pagehtml) :
                storehtml(pagehtml,path,pageurl)
                print "下载微群页面可能出错,错误样本:%s"%path
                return False
        else:
            #下载页面错误
            return False
        #转换成系统编码
        #pagehtml = fromUTF8toSysCoding(pagehtml)
        storehtml(pagehtml,path,pageurl)
        
        #修改db的下载列表状态:成功下载
        succ = self.update_download_db_state(pageurl,path,type='weiqunpage',status=self.STATUS_DOWNLOADED,page=i,userid=self.weiqunID)
        if not succ:
            print 'update_download_list:更新数据库失败'
        return True

    def is_weiqun_page_trap(self,html,showdetail=True):
        #是否 定向到 失败页
        if html:
            if PAGE_REQUEST_ERROR in html :
                if showdetail:
                    print 'is_weiqun_page_trap陷阱:%s'%PAGE_REQUEST_ERROR
                return True
            if NOBODY_POST_THIS_PAGE in html:
                if showdetail:
                    print 'is_weiqun_page_trap陷阱:%s'%NOBODY_POST_THIS_PAGE
                return True
            if PAGE_REDIRECT in html:
                if showdetail:
                    print 'is_weiqun_page_trap陷阱:%s'%PAGE_REDIRECT
                return True
        if html is None:
            if showdetail:
                print 'is_weiqun_page_trap陷阱: html is None'
            return True
        if len(html)< 4000:
            if showdetail:
                print 'is_weiqun_page_trap陷阱:网页长度过小'
            return True
        #是否与上次访问重复
        if self.last_crawl_html == str(html):
            if showdetail:
                print "is_spider_trap遇到重复网页:%s"%str(html)
            self.last_crawl_html = ''
            return True
        else:
            #缓存上次下载的页面,以备检查是否下载相同页面(反爬虫页)
            self.last_crawl_html = str(html)
        return False
    
    def rtreply_crawl(self,startpage,endpage,showdetail=False):
        '''
        待改善:速度慢,可并行加快下载,串行io提高效率
        前提:运行了 weiqun_crawl_page(),start_analyze_weibos(),end_analyze_weibos() 或数据库中表weibos有原创weibo(isoriginal=1)信息
        任务:从数据库中读取startpage~endpage页每条微博的评论`转发url,下载到:
        该weibo[i].html目录下的 ./weibo[i]/reply,./weibo[i]/rt 目录中
        每条转发\评论命名为rt[j].html,reply[j].html
        '''
        print "开始从数据库中读取每条微博的评论`转发url信息,下载到本地磁盘"
        header = self.headers_weiqun
        self.cur_weibo.execute("SELECT weiboid,path,replyurl,rturl,reply,rt FROM weibos WHERE isoriginal = 1")
        count = 0
        rtcount=0
        replycount=0
        for row in self.cur_weibo.fetchall():
            count+=1
            weiboid,path,replyurl,rturl,reply,rt = row
            #------------handle reply-------------------------------------
            #选取原创微博(isoriginal=1)的 本地存储地址path,评论replyurl
            if reply!=0:
                replyhtml = urlprocessor(replyurl,header)
                if ("请求页不存在 出错了" not in replyhtml):
                    replycount+=1
                    if showdetail: print "处理微博reply,第"+str(replycount)+'条reply:'+path+"的replyurl:"+replyurl
                    replypath = path.rstrip('.html')+'/'+'reply.html'
                    if showdetail: print "\t保存微博reply,第"+str(replycount)+'条reply到路径:'+replypath
                    storehtml(replyhtml,replypath,replyurl,showdetail)
                else:
                    print "下载reply页出错:请求页不存在 出错了,路径:"+path
                    pass
        
            #------------handle rt 基本同上-----------------------------------
            #选取原创微博(isoriginal=1)的 本地存储地址path,转发rturl
            if rt!=0:
                rthtml = urlprocessor(rturl,header)
                if ( PAGE_REQUEST_ERROR not in rthtml):
                    rtcount+=1
                    if showdetail: print "处理微博rt,第"+str(rtcount)+'条rt:'+path+"的rturl:"+rturl
                    rtpath = path.rstrip('.html')+'/'+'rt.html'
                    if showdetail: print "\t保存微博rt,第"+str(rtcount)+'条rt到路径:'+rtpath
                    storehtml(rthtml,rtpath,rturl,showdetail)
                else:
                    print "下载rt页出错:请求页不存在 出错了,路径:"+path
                    pass
                
        print "完成"+str(count)+("条微博的reply(%d) rt(%d)的下载,从:"%(replycount,rtcount))+ str(self.weibodbname)
        
    def start_rtreply_analyze(self):
        '''
        开始对硬盘的所有rt,reply网页进行分析,
        '''
        '''
        前提：当rtreply_crawl()下载好微群的每个reply(rt).html存至磁盘
        任务：1.从磁盘遍历savedir下所有路径为weiqunid?page=[i]/weibo[j]/reply(rt).html，交给self.rtreply_analyze(路径名)：
        返回:分析失败的rt/reply.html相对路径表failed_reply_paths[],failed_rt_paths[]，待重新爬取
        '''
        print "开始分析微博rt,reply：读取本地目录%s下的所有rt,reply"%(self.savedir)
        #self.replyinfos=[]#储存replyinfo{weiboid,...}(同数据库中weibos的item)
        #self.rtinfos=[]#同上
        #self.failed_reply_paths=[]#储存分析失败的reply.html路径，需要重新爬取
        #self.failed_rt_paths=[]#同上
        countrt=0#记录抽取微博rt数量
        countrtfail=0#rt抽取失败的数量
        countreplyfail=0#reply抽取失败的数量
        countreply=0#记录抽取微博reply数量
        #dir是文件名或目录，path是目录
        for pagedir in os.listdir(self.savedir):
            pagepath = self.savedir +'/' + pagedir
            if os.path.isdir(pagepath):
                for weibodir in os.listdir(pagepath):
                    #print pagepath #:./NLP/225241?page=9
                    #print weibodir #:weibo9.html weibo1 ...
                    weibopath = pagepath + '/' + weibodir
                    if os.path.isdir(weibopath):
                        rtpath = weibopath +'/rt.html'
                        replypath = weibopath+'/reply.html'
                        
                        #分析reply页的html
                        if os.path.isfile(rtpath):
                            print '分析rt：'+ replypath 
                            try:
                                f=open(rtpath,'r')
                                html=f.read()
                            except Exception,E:
                                print 'Weiqun_crawler.start_rtreply_analyze()打开本地缓存页面失败：'+str(rtpath)
                                f.close()
                                continue#不分析该页
                            finally:
                                f.close()
                            #分析rt.html
                            rtinfos = self.rt_analyze(html,rtpath)
                            #如果分析失败，记录到失败表中
                            if rtinfos is None:
                                countrtfail+=1
                                self.failed_rt_paths.append(replypath)
                            #成功加入表
                            else:
                                for rtinfo in rtinfos:
                                    countrt+=1
                                    self.rtinfos.append(rtinfo)
                        
                        #分析reply页的html
                        if os.path.isfile(replypath):
                            #print '分析reply：'+ replypath 
                            try:
                                f=open(replypath,'r')
                                html=f.read()
                            except Exception,E:
                                print 'Weiqun_crawler.start_rtreply_analyze()打开本地缓存页面失败：'+str(replypath)
                                f.close()
                                continue#不分析该页
                            finally:
                                f.close()
                            #分析reply.html
                            replyinfos = self.reply_analyze(html,replypath)
                            #如果改页分析失败，记录到失败表中
                            if replyinfos is None:
                                countreplyfail+=1
                                self.failed_reply_paths.append(replypath)
                            #成功加入表
                            else:
                                for replyinfo in replyinfos:
                                    countreply+=1
                                    self.replyinfos.append(replyinfo)
                        
        print "完成%d条reply，%d条rt的分析，失败reply:%d,rt:%d条，从本地目录：%s"%(countreply,countrt,countreplyfail,countrtfail,self.savedir)
        #返回:分析失败的rt/reply.html相对路径表failed_reply_paths[],failed_rt_paths[]，待重新爬取
        return self.failed_reply_paths,self.failed_rt_paths
    
    def end_rtreply_analyze_to_db(self):
        '''
        前提:start_rtreply_analyze()或rtreply_analyze()分析出评论转发内容存入replyinfos[] rtinfos[]
        任务:把replyinfos[] rtinfos[]的项存入数据库self.weibodbname
        '''
        countreply = 0
        countrt =0
        
        for rtinfo in self.rtinfos:
            countrt+=1
            pass
        
        for replyinfo in self.replyinfos:
            countreply+=1
            value=(replyinfo['weiboid'].replace(":",""),\
                #replyinfo['raw'].replace(":","").replace('"','').replace("'",""),\
                '',
                replyinfo['location'].replace(":",""),\
                replyinfo['content'].replace(":","").replace('"','').replace("'",""),\
                #replyinfo['contentraw'].replace(":","").replace('"','').replace("'",""),\
                '',
                replyinfo['username'].replace(":",""),\
                replyinfo['datetime'].replace(":",""),\
                replyinfo['isreplyto'].replace(":",""),\
                replyinfo['replyurl'].replace(":",""),\
                replyinfo['isrtto'].replace(":",""),\
                replyinfo['rturl'].replace(":",""),\
                replyinfo['atwho'].replace(":",""),\
                replyinfo['reply'],\
                replyinfo['rt'],\
                replyinfo['isoriginal'],\
            )
            try:
                #每条原创、评论、转发都看做一个weibo项，用weiboid区分
                #print value
                self.cur_weibo.execute("""INSERT INTO weibos(weiboid,raw,pagelocation,content,contentraw,username,datetime,isreplyto,replyurl,isrtto,rturl,atwho,reply,rt,isoriginal) VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%d,%d,%d);""" %value)                           
                
            except sqlite.Error,E:
                print 'DB:weibos表中插入weiboinfo项(reply)出现异常：INSERT VALUES=' + str(value)
                print E
            finally:
                self.dbcommit()
            
        print "把%d/%d条reply/rt存入数据库：%s"%(countreply,countrt,self.weibodbname)
    
    def reply_analyze(self,html,filename=None):
        '''
        任务：分析reply的html，将每条reply封装成replyinfo{},放入replyinfos[]
        返回：replyinfos[] :replyinfo{}的列表
        '''
        replyinfos=[]
        soup = BeautifulSoup(html)
        title = soup.title.string
        if NO_REPLY in html or  '评论列表' not in title:
            print '分析失败(无效reply页，可能需要重新爬取)：reply_analyze(html,%s)'%filename
            return None
        else:#有reply
            allc = soup.find_all("div", { "class" : "c" })
            #wap
            subject = allc[1]#被评论微博
            replies = allc[2:]#几个评论
            isreplyto = subject['id']#reply to的微博id,格式M_vr02n0ha52
            #print isreplyto
            if isreplyto:
                for reply in replies:
                    weiboid = None
                    userid = ''
                    content =''
                    contentraw=''
                    username = ''
                    userpage = ''
                    datetime = ''
                    replyurl =''
                    isrtto = ''
                    rturl = ''
                    rt=0
                    replynum=0
                    isoriginal = 3 #reply=3
                    atwho = ''
                    try:
                        weiboid = reply['id']
                        #print reply['id']#评论id格作为weiboid,格式C_1120421220327297
                    except KeyError,E:
                        weiboid = None
                        pass
                    if weiboid:
                        contentraw = str(reply)
                        content = str(reply.find('span',{'class':'ctt'}).get_text())
                        datetime = str(reply.find('span',{'class':'ct'}).get_text())
                        replyurl = str(reply.find('span',{'class':'cc'}).get('href'))
                        username = str(reply.a.get_text())
                        #提取"回复@谁:"的谁
                        r = re.compile(r'回复@(.*?):').search(content)
                        if r:
                            atwho = r.group(1)
                            #print atwho
                        replyinfo={}
                        if filename:
                            replyinfo.update({'location':filename})
                        else:
                            replyinfo.update({'location':''})
                            
                        
                        replyinfo.update({'weiboid':weiboid})
                        replyinfo.update({'raw':html})
                        replyinfo.update({'content':content})
                        replyinfo.update({'contentraw':contentraw})
                        replyinfo.update({'username':username})
                        replyinfo.update({'datetime':datetime})
                        replyinfo.update({'isreplyto':isreplyto})
                        replyinfo.update({'isrtto':isrtto})
                        replyinfo.update({'rt':rt})
                        replyinfo.update({'reply':replynum})
                        replyinfo.update({'replyurl':replyurl})
                        replyinfo.update({'rturl':rturl})
                        replyinfo.update({'isoriginal':isoriginal})
                        replyinfo.update({'atwho':atwho})
                        replyinfos.append(replyinfo)
                
                return replyinfos
        
        pass
    
    def rt_analyze(self,html):
        rtinfo={}
        soup = BeautifulSoup(html)
        
        return rtinfo
        pass

    def test_login(self,url):
        '''
        带header cookie访问weibo.cn，测试是否成功登陆首页
        '''
        header = self.headers_login
        #打开url处理html
        html = urlprocessor(url,header,absUrl=True)
        
        #转换成系统编码
        #html = fromUTF8toSysCoding(html)
    
        #获取用户信息打印
        print '测试登陆，请检查用户是否正确：'
        soup = BeautifulSoup(html)
        if soup.find("div", { "class" : "ut" }):
            print soup.find("div", { "class" : "ut" }).get_text()
        #re查找html的用户信息
        #pat_title = re.compile('<div class="ut">(.+?)</div>')
        #r = pat_title.search(html)
        #if r:
        #    print r.group(1)    
    
        #store html to disk
        #path = self.savedir + '/waplogin.html'
        #storehtml(html,path,url)
        #打开./waplogin.html看是否有用户名存在

    def dbcommit(self):
        '''
        提交db操作
        '''
        self.con_weibo.commit()
        self.con_user.commit()

    def dbtest(self):
        #value=('weiboid','1','12341a','4','5','6','7','8','9','10',11,'12','13',14,'15',16,'17')
        #self.cur_weibo.execute("INSERT INTO weibos(weiboid,raw,pagelocation,contentraw,content,userid,userpage,username,datetime,isreplyto,reply,replyurl,isrtto,rt,rturl,isoriginal,atwho) VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%d','%s','%s','%d','%s','%d','%s');" %value)    
        self.dbcommit()
        pass
    
    def createuserstable(self):
        '''
        初始化 用户信息、用户关系表
        '''
        #建表relation
        try:
            self.cur_user.execute('CREATE TABLE relation(userid TEXT,followerid TEXT,PRIMARY KEY(userid,followerid))')
            self.dbcommit()
        except sqlite.OperationalError,E:
            #print 'DB:%s建表relation出现异常：'%self.userdbname
            #print E
            pass
        #建表profile
        try:
            self.cur_user.execute('CREATE TABLE profile(userid TEXT PRIMARY KEY,username TEXT,followers INTERGER,followings INTERGER,weibos INTERGER)')
            self.dbcommit()
        except sqlite.OperationalError,E:
            #print 'DB:%s建表profile出现异常：'%self.userdbname
            #print E
            pass
        #建表download,保存网页下载进度信息
        try:
            self.cur_user.execute('CREATE TABLE download(url TEXT,path TEXT,type TEXT ,status INTERGER,page INTERGER ,userid TEXT ,randurl TEXT ,datetime TIMESTAMP,PRIMARY KEY(url,path))')
            self.dbcommit()
        except sqlite.OperationalError,E:
            #print 'DB:%s建表download出现异常：'%self.userdbname
            #print E
            pass
            
    def createweibostable(self):
        '''
        初始化微博信息db表
        '''
        try:
            #每条原创、评论、转发都看做一个weibo项，用weiboid区分
            '''
            self.cur_weibo.execute('CREATE TABLE weibos\
             (weiboid TEXT PRIMARY KEY,#主键，每个微博分配一个独立的id=genweiboid() 暂用生成先后顺序分配\
             raw TEXT,                      #此条微博的全部源代码\
             path TEXT,                    #此条微博储存到本地磁盘的位置
             pagelocation TEXT,                       #此条微博所在的网页地址（是爬下来存放在本地磁盘的路径）\
             contentraw TEXT,                     #此条微博内容的源代码\
             content,                             #正文\
             userid TEXT,                         #发微博用户id\
             userpage TEXT,                       #发微博用户主页\
             username TEXT,                       #发微博用户名\
             datetime TEXT,                       #发微博日期时间\
             isreplyto TEXT,                      #是否是某条微博的评论\
             reply INTEGER,                      #微博的评论数\
             replyurl TEXT,                       #微博的评论超链接url\
             isrtto TEXT,                         #是否是某条微博的转发\
             rt INTEGER,                         #微博的转发数\
             rturl TEXT,                          #微博的转发超链接url\
             isoriginal INTEGER,                 #是原创微博吗 1:是 0:否\
             atwho TEXT,                          #这条微博at了谁，如:id1,id2,id3\
             )')
             '''
            self.cur_weibo.execute('CREATE TABLE weibos(weiboid TEXT PRIMARY KEY,path TEXT,pagelocation TEXT,content TEXT,userid TEXT,userpage TEXT,username TEXT,datetime TEXT,isreplyto TEXT,reply INTEGER,replyurl TEXT,isrtto TEXT,rt INTEGER,rturl TEXT,isoriginal INTEGER,atwho TEXT,raw TEXT,contentraw TEXT)')
            self.dbcommit()
        except sqlite.OperationalError,E:
            print 'DB建表weibos出现异常：'
            #print E
            pass    #已经存在table    
        
    def start_crawl_profiles_from_uid_in_weibodb(self,showdetail=False):
        '''
        前提：db:self.weibodbname有uid
        任务：读取db:self.weibodbname的uid，下载uid的type:profile，fans，follow页到本地磁盘/uid/[type]/[i].html
        db:写self.userdbname的download表
        返回:True 完成退出(可能有几个没爬)
        '''
        header = self.headers_login
        print "start_crawl_profiles_from_uid_in_weibodb:开始从数据库读取uid,从网络下载uid主页到本地磁盘self.usersdir/uid/profile.html"
        try:
            self.cur_weibo.execute("SELECT DISTINCT userid FROM weibos")
            self.dbcommit()
        except Exception,E:
            print 'start_crawl_profiles_from_uid_in_weibodb：从db读取uid错误'
            print E
            return None
            
        count_done = 0
        count_invalid_uid = 0
        count_trap = 0
        count_skip = 0
        list = self.cur_weibo.fetchall()
        print '\t共有用户：%d个'%len(list)
        for row in list:
            #print type(row)#tuple
            uid, = row
            #print type(uid)#unicode
            
            if uid==None or uid==0 or uid=='':
                count_invalid_uid+=1
                if showdetail:
                    print "start_crawl_profiles_from_uid_in_weibodb:无效uid:%s"%uid
                continue
            else:
                type = 'profile'
                page = 0
                #下载uid的profile页,存到磁盘
                html = self.crawl_user_page(uid, page, type, header,showdetail)
                
            #处理下载好的html
            if html is None:
            #下载profile失败，则加入失败列表
                count_trap+=1
                if showdetail:
                    print 'start_crawl_profiles_from_uid_in_weibodb:下载用户profile失败,记录在download表上uid：%s' % uid
            elif html == '':
                count_skip+=1
            else:
                count_done+=1
                   
        print '\tstart_crawl_profiles_from_uid_in_db:成功下载/跳过/无效uid/爬虫陷阱的profile页：%d/%d/%d/%d个'%(count_done,count_skip,count_invalid_uid,count_trap)    
        return True

    def start_crawl_fans_follow_from_profiles_in_db(self,delayfunc,stop_when_trap=True,showdetail=False):
        '''
        前提：db:self.userdbname有uid,followers,followings（fans,fos数量）
        任务：读取db:self.userdbname的uid，fans，fos，下载粉丝、关注用户页:[i].html到本地self.usersdir/uid/fans /follow
        输出：文件如上述
        db:写self.userdbname的download表
        返回:True 完全爬完
            MEET_TRAP 遇见陷阱,暂停退出
        '''
        header = self.headers_login
        print "start_crawl_fans_follow_from_profiles_in_db():开始从数据库%s读取uid,关注数,粉丝数，下载每个uid的fans follow页:[i].html到本地磁盘self.usersdir/uid/fans /follow"%self.userdbname
        try:
            self.cur_user.execute("SELECT  userid,weibos,followers,followings FROM profile")
            self.dbcommit()
        except Exception,E:
            print 'start_crawl_fans_follow_from_profiles_in_db：读取uid错误'
            print E
        countuser = 0
        countpage = 0
        countdownload = 0
        list = self.cur_user.fetchall()
        print '\t共有用户：%d个'%len(list)
        for row in list:

            countuser+=1
            #print type(row)#tuple
            uid,weibonum,fansnum,fosnum = row
            
            #延迟,以防被ban
            delayfunc(countpage)
            
            #-----------下载用户fans页---------------------------
            end = int(fansnum / WEIBO_PER_PAGE + 2) 
            type = 'fans'
            for i in range(1,end):
                countpage+=1
                #返回的html是:None则有陷阱,''则是跳过,'...'则是网页内容
                html = self.crawl_user_page(uid, i, 'fans', header, weibonum, fansnum, fosnum, showdetail)
                if html is None:
                    print 'start_crawl_fans_follow_from_profiles_in_db:爬取遇到陷阱，无法爬取uid:%s的%s第%d页'%(uid,type,i)
                    #若参数设定 遇到陷阱停止爬取
                    if stop_when_trap:
                        return MEET_TRAP
                elif html is '':
                    print 'start_crawl_fans_follow_from_profiles_in_db:本地已有,跳过爬取uid:%s的%s第%d页'%(uid,type,i)
                else:#处理 网页HTML代码
                    countdownload+=1
                    pass
                    

            #-----------下载用户follow页---------------------------
            end = int(fosnum / WEIBO_PER_PAGE + 2)
            type = 'follow'
            for i in range(1,end):
                countpage+=1
                html = self.crawl_user_page(uid, i, 'follow', header, weibonum, fansnum, fosnum, showdetail)
                if html is None:
                    print 'start_crawl_fans_follow_from_profiles_in_db:爬取遇到陷阱，无法爬取uid:%s的%s第%d页'%(uid,type,i)
                    print '已经连续爬取%d个网页'%countdownload
                    #若参数设定 遇到陷阱停止爬取
                    if stop_when_trap:
                        
                        return MEET_TRAP
                elif html is '':
                    #if showdetail:
                    print 'start_crawl_fans_follow_from_profiles_in_db:本地已有,跳过爬取uid:%s的%s第%d页'%(uid,type,i)
                else:#处理 网页HTML代码
                    countdownload+=1
                    pass
            
        print 'start_crawl_fans_follow_from_profiles_in_db:共处理用户%d个,处理网页%d个，下载网页%d个'%(countuser,countpage,countdownload)
        return True
        
    def is_spider_trap(self,uid,weibonum,fansnum,fonum,pagetype,html):
        '''
        if uid  not in html:
            #重定向到login的用户主页，但是页面隐含请求url，隐含这个uid，失效！
            print '干 为什么不出来'
            return True
        '''
        if self.last_crawl_html == str(html):
            print "is_spider_trap遇到重复网页:%s"%str(html)
        else:
            self.last_crawl_html = str(html)
        
        
        if LOGIN_USER_NAME in html:
            print "is_spider_trap重定向到登陆用户%s主页" % LOGIN_USER_NAME
            return True
        if (PAGE_REQUEST_ERROR in html):
            return True

        '''
        待改善：添加更多爬虫陷阱例外
        '''
        #不是陷阱
        return False
    
    def gen_user_page_url(self,uid,page,type,showdetail=False):
        '''
        任务:生成给定uid的profile/fans/follow的第page页的url
        输出:url或None(生成失败时)
        '''
        if type == 'follow':
            url_base = FOPAGE_PREFIX % uid + FOPAGE_SURFFIX
        elif type == 'fans':
            url_base = FANPAGE_PREFIX % uid + FANPAGE_SURFFIX
        elif type == 'profile':
            url  = USERPROFILE_PREFIX % uid
        else:#如果type不是上述，参数错误，返回None
            print 'gen_user_page_url：参数错误tpye=%s'%type
            return None
        if type!= 'profile':
            url = url_base % str(page)
        
        return url
    
    def gen_user_page_path(self,uid,page,type,showdetail=False):
        '''
        任务:生成给定uid的profile/fans/follow的第page页的保存文件路径
        输出:path或None(生成失败时)
        '''
        if type == 'follow':
            path_base = self.usersdir+'/%s/follow/' % uid
        elif type == 'fans':
            path_base = self.usersdir+'/%s/fans/' % uid
        elif type == 'profile':
            path = self.usersdir+'/%s/profile.html' % uid
        else:#如果type不是上述，参数错误，返回None
            print 'gen_user_page_path：参数错误tpye=%s'%type
            return None
        if type!= 'profile':
            path = path_base + str(page) + '.html'
        return path
    
    def crawl_user_page(self,uid,page,type,header,weibonum=None,fansnum=None,fosnum=None,showdetail=False):
        '''
        任务：爬取给定uid的关注页（第page页,type是'fans'或者'follow'或者'profile'）(查询self.userdbname,如果爬取过就跳过)
        输出：把关注页存到本地：是self.gen_user_page_path(uid, page, type) = self.usersdir/[uid]/[type]/[i].html(fans或follow) | self.usersdir/[uid]/profile.html
        返回：返回None:遇到爬虫陷阱，储存文件
             返回'':已下载好,跳过爬取,
             返回html:成功爬取，储存文件并
        '''
        url = self.gen_user_page_url(uid, page, type)
        path = self.gen_user_page_path(uid, page, type)
        if url is None or path is None:
            return None
        
        #从self.userdbname检查是否下载过
        godownload = False
        query = self.load_download_db_state(url,path)
        if query is None:
            godownload =True
        else:
            auid,atype,apage,astatus,aurl,apath,arandurl,atimestamp = query
            if astatus != 1:
                godownload = True
        
        if godownload: 
            #下载网页
            html = urlprocessor(url,header,absUrl=True)
            
            #如果是陷阱,依然保存到磁盘，留作分析
            if self.is_spider_trap(uid, weibonum, fansnum, fosnum,type,html): 
                print "crawl_user_page:可能是爬虫陷阱 下载到路径：%s ,url:%s,type:%s下载到第%d页"%(path,url,type,page)
                storehtml(html,path,url)
                #更新下载状态(失败)到数据库table download 
                self.update_download_db_state(url,path,type,self.STATUS_FAILED,page,uid)
                return None
            #成功下载，保存到磁盘
            else:
                #转换成系统编码
                #pagehtml = fromUTF8toSysCoding(pagehtml)
                storehtml(html,path,url)
                #更新下载状态(成功)到数据库table download 
                self.update_download_db_state(url,path,type,self.STATUS_DOWNLOADED,page,uid)
                if showdetail:
                    print 'crawl_user_page成功下载网页到：%s,url：%s'%(path,url)
                return html
        else:#dont download
            if showdetail:
                print 'crawl_user_page不重复下载url:%s,已有有效网页:%s'
            return ''
        
    def analyze_user_profiles(self,showdetail=False):
        '''
        前提：有self.usersdir/[uid]/profile.html
        任务：读取上述所有文件，交由analyze_username_weibos_fans_fos_num()分析（会改动self.profiles[])
        修改：self.profiles[],self.userdbname的table download
        返回：self.profiles[]
            NOne:无文件self.usersdir
        '''
        try:
            os.listdir(self.usersdir)
        except OSError,e:
            print 'analyze_user_profiles错误:无文件self.usersdir'
            print e
            return None
            
        print 'analyze_user_profiles():从硬盘self.usersdir读取%d个用户profile进行关系分析'%len(os.listdir(self.usersdir))
        count = 0
        for uid in os.listdir(self.usersdir):
            path =  self.usersdir +'/' +uid+'/profile.html'
            if os.path.isfile(path):
                with open(path) as f:
                    html = f.read()
                    #分析下载页的 微博[38] 关注[73] 粉丝[27] 数
                    nums = crawler.analyze_username_weibos_fans_fos_num(html,showdetail)
                    if nums is None:#无效profile
                        print 'analyze_user_profiles:无效profile:%s'%path
                        pass
                    else:#有效profile,获取上述项的num
                        if showdetail: print nums
                        username,weibosnum,fansnum,fosnum = nums
                        #将用户的profile {username,uid,weibonum,fansnum,fosnum},加到self.profiles[]中
                        #之后调用end_crawl_user_info_to_db()将self.profiles存入./users.db的user
                        profile = {}
                        profile.update({'username':username,'userid':uid,'weibos':int(weibosnum),'followers':int(fansnum),'followings':fosnum})
                        self.profiles.append(profile)
                        count+=1
        print 'analyze_user_profiles():分析了%d个用户profile，%d个失败'%(count, len(os.listdir(self.usersdir))-count)
        return self.profiles

    def end_store_user_profiles_to_db(self):
        count=0
        for profile in self.profiles:
            userid = profile['userid']
            username = profile['username']
            weibos = profile['weibos']
            followers = profile['followers']
            followings = profile['followings'] 
            try:
                self.cur_user.execute('''INSERT INTO profile(userid,username,weibos,followers,followings) VALUES ('%s','%s',%d,%d,%d); ''' % (userid,username,weibos,followers,followings))
                self.dbcommit()
                count+=1
            except Exception,E:
                print 'end_store_user_profiles_to_db():./user.db往profile表中插入项出现错误：'
                print E
        print 'end_store_user_profiles_to_db():完成%d条profile表项的更新，在db：./user.db'%count
               
    def analyze_username_weibos_fans_fos_num(self,html,showdetail=False):
        '''
        输入:wap html源代码of微博用户profile页:“usrename的微博[0] 关注[21] 粉丝[5] 分组[1] @她的”
        输出：(username,weibonum,fansnum,fosnum) 或 None
        '''
        soup = BeautifulSoup(html)
        title = str(soup.title.string)
        #wap用户名在标题
        username = title.rstrip(u'的微博')
        #wap如果标题有 “微博广场”字样而非username，下载出错，需要重新下载
        if  WEIBO_SQUARE in title:
            return None
        else:
            #wap分析 网页蓝微博[0] 关注[21] 粉丝[5] 分组[1] @她的
            allres = soup.find_all("div", { "class" : "tip2"})
            for res in allres:
                #res类型<class 'bs4.element.Tag'>
                text =  res.get_text()
                
                if (u'微博['in text) and (u'关注[' in text) and (u'粉丝[' in text):
                    if showdetail:  print text#微博[754] 关注[193] 粉丝[261] 分组[1] @她的
                    weibosnum = 0
                    fansnum=0
                    fosnum=0
                    #获取微博数
                    res = re.compile(u'微博\[(.+?)\]').search(text)
                    if res is not None:
                        weibosnum = int(res.group(1))
                    #获取关注数
                    res = re.compile(u'关注\[(.+?)\]').search(text)
                    if res is not None:
                        fosnum = int(res.group(1))
                    #获取粉丝数
                    res = re.compile(u'粉丝\[(.+?)\]').search(text)
                    if res is not None:
                        fansnum = int(res.group(1))
                    #分析成功，返回数目
                    if showdetail:  print username,weibosnum,fansnum,fosnum
                    return username,weibosnum,fansnum,fosnum
                else:#分析错误，返回
                    return None
                
    def test_analyze_weibos_fans_fos_num(self):
        '''
        前提：self.usersdir/uid/profile.html 有文件(执行过self.start_crawl_profiles_from_uid_in_weibodb())
        任务：测试crawler.analyze_username_weibos_fans_fos_num()
        输出：很多行：    微博[1590] 关注[124] 粉丝[153] 分组[1] @她的
                       我们都关注文章同學
        '''
        print '测试test_analyze_weibos_fans_fos_num()，将看到类似\n“微博[233] 关注[257] 粉丝[322] 分组[1] @他的\n智能侠-AI 233 322 257”'
        for uid in os.listdir(self.usersdir):
            path =  self.usersdir+'/'+uid+'/profile.html'
            if os.path.isfile(path):
                with open(path) as f:
                    html = f.read()
                    nums = crawler.analyze_username_weibos_fans_fos_num(html,showdetail=True)
                    if nums is None:
                        print "非有效profile:%s"%path
                    else:
                        print nums
        
    def end_analyze_weibos_to_db(self):
        '''
        输入：self.allweiboinfos[]
        前提：start_analyze_weibos_from_disk()执行完毕，将析取的微博信息self.allweiboinfos[]储存好
        任务：把all weiboinfo{}中内容存至数据库
        '''
        print "将分析好的微博信息self.allweiboinfos[]存入数据库文件:"+self.weibodbname + '...'
        for weiboinfo in self.allweiboinfos:
            #微博在本地磁盘的路径
            path = str(weiboinfo['path']).replace("'",'').replace('"','')
            #微博所在网页page的路径
            pagelocation = str(weiboinfo['pagelocation']).replace("'",'').replace('"','')#去除字符串中的'与"(sqlite 类型TEXT不允许)
            #微博(WAP版)的id
            weiboid = str(weiboinfo['weiboid']).replace("'",'').replace('"','')
            #用户信息
            username = str(weiboinfo['username']).replace("'",'').replace('"','')
            userid = str(weiboinfo['userid']).replace("'",'').replace('"','')
            userpage = str(weiboinfo['userpage']).replace("'",'').replace('"','')
            content = str(weiboinfo['content']).replace("'",'').replace('"','')
            contentraw = str(weiboinfo['contentraw']).replace("'",'').replace('"','')
            replyurl = str(weiboinfo['replyurl']).replace("'",'').replace('"','')
            rturl = str(weiboinfo['rturl']).replace("'",'').replace('"','')
            datetime = str(weiboinfo['datetime']).replace("'",'').replace('"','')
            atwho = str(weiboinfo['atwho']).replace("'",'').replace('"','')
            isreplyto = str(weiboinfo['isreplyto']).replace("'",'').replace('"','')
            raw = str(weiboinfo['raw']).replace("'",'').replace('"','')
            isrtto = str(weiboinfo['isrtto']).replace("'",'').replace('"','')
            reply = int(weiboinfo['reply'])
            rt = int(weiboinfo['rt'])
            isoriginal = int(weiboinfo['isoriginal'])
            
            value =  (weiboid,path,pagelocation,content,userid,userpage,username,datetime,isreplyto,replyurl,isrtto,rturl,atwho,raw,contentraw,reply,rt,isoriginal)
            #往weibos表中插入weiboinfo项
            try:
                #每条原创、评论、转发都看做一个weibo项，用weiboid区分
                self.cur_weibo.execute("""INSERT INTO weibos(weiboid,path,pagelocation,content,userid,userpage,username,datetime,isreplyto,replyurl,isrtto,rturl,atwho,raw,contentraw,reply,rt,isoriginal) VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%d,%d,%d);""" %value)                           
            except sqlite.Error,E:
                print 'DB:weibos表中插入weiboinfo项出现异常：INSERT VALUES=' + str(value)
                print E
            finally:
                self.dbcommit()
        print "完成"
                
    def start_analyze_weibos_from_disk(self,showdetail=True):
        '''
        前提：当weiqun_crawl_page()下载好微群的每个page.html存至磁盘
        任务：1.从磁盘遍历savedir下所有page.html，交给analyze_weiqun_weibo()：
                a.抽出页内每条weibo[j]的html存到self.savedir/weiqunID?pagename_html=[i]/weibo[j].html
                b.分析每条微博，析取信息到weiboinfo={}，dic key同db的weibos表，将每条微博的weiboinfo加到总表allweiboinfos
        返回：allweiboinfos 微博抽取信息的总表。
        '''
        print "开始分析微博：读取本地目录%s下的所有网页"%(self.savedir)
        header = self.headers_weiqun
        self.allweiboinfos = []#微博信息总表，元素是weiboinfo={}
        count=0#记录抽取微博数量
        j=0 #分析第j页上的微博
        for pagename_html in os.listdir(self.savedir):
                #分割文件名与后缀ext，如:pagename_html = '225241?page=1',ext='.html'
                pagename,ext =  os.path.splitext(pagename_html)
                if ext == '.html' and 'page' in pagename:
                    #打开page.html
                    try:
                        f=open(self.savedir+'/'+pagename_html,'r')
                        html=f.read()
                    except Exception,E:
                        print 'Weiqun_crawler.start_analyze_weibos_from_disk()打开本地缓存页面失败：'+str(pagename_html)
                        continue#不分析该页
                    finally:
                        f.close()
                    j+=1
                    
                    #分析第j页的所有微博,存到pageweiboinfos=[weiboinfo1,weiboinfo2,...]，其中weiboinfo={}，内容同db table weibos' item
                    pageweiboinfos = []
                    pageweiboinfos = self.analyze_weiqun_page(html,pagename_html,showdetail)
                    for weiboinfo in pageweiboinfos:
                        #每个微博都加入总表
                        self.allweiboinfos.append(weiboinfo)
                    
                    #把第j页的所有微博源代码单独存到pagename目录下
                    i=0
                    for weiboinfo in pageweiboinfos:
                        count+=1
                        i+=1
                        #建立pagename文件，存放分析微博的源代码weibo[i].html
                        path = self.savedir+'/'+pagename+'/'+'weibo'+str(i)+'.html'
                        weiboinfo.update({'path':path})
                        storehtml(weiboinfo['raw'],weiboinfo['path'],pagename,showdetail=False)
                        if showdetail:  print ("\t分析第%d页第%d条微博并储存在:"%(j,i))+path
                    
                    print '\t分析weiqun页上的微博完毕:%s'%pagename_html
        print "完成%d条微博抽取，从本地目录：%s"%(count,self.savedir)
        return self.allweiboinfos
        
    def analyze_weiqun_page(self,html,pagename,showdetail):
        '''
        分析微群页面html，返回weibos=[],由getweibos()调用
        weibo是抽取出来的html：按一般page中微博格式：（WAP）
        <div class="c" id="M_103r08nr6th">...</div> ,其中id疑似unique?（WAP和Web不一样）
        ???假设id是uid，存为weiboid???
        '''
        
        #完成下面的bs分析:取出该页每条微博的tag，存为weibohtml
        #调用analyze_weibo_from_page提取出多条微博信息weiboinfo{}，存在weiboinfos[]并返回
        weiboinfos=[]
        soup = BeautifulSoup(html)
        allres = soup.find_all("div", { "class" : "c"})
        for res in allres:
            #res类型<class 'bs4.element.Tag'>
            if res.has_key('id'):
                weibohtml=str(res)
                weiboinfo = self.analyze_weibo_from_page(weibohtml,pagename,showdetail)
                if weiboinfo:#如果是一条weibo
                    weiboinfos.append(weiboinfo)
        return weiboinfos

    def analyze_weibo_from_page(self,html,pagelocation,showdetail):
        '''
        分析每条微博的html，抽取出如下元素
        '''
        weiboinfo = {}
        #------------------------------------------------------------------------------ 
        #是否对某条微博的评论、转发，是否原创
        weiboinfo.update({'isreplyto': ''})
        weiboinfo.update({'isrtto' : ''})
        weiboinfo.update({'isoriginal' : 1})
        #------------------------------------------------------------------------------ 
        #at了谁
        atwho = self.analyze_weibo_atwho(html)
        weiboinfo.update({'atwho':atwho})
        #------------------------------------------------------------------------------ 
        #微博所在page(page存在本地磁盘路径)
        pagelocation = self.savedir + '/' + pagelocation
        weiboinfo.update({'pagelocation':pagelocation})
        #------------------------------------------------------------------------------ 
        #纯html文档
        weiboraw = html
        weiboinfo.update({'raw':weiboraw})
        #------------------------------------------------------------------------------ 
        #找出weiboid
        weiboid = self.analyze_weibo_weiboid(html)
        if weiboid: weiboinfo.update({'weiboid':weiboid})
        else:
            print '这不是微博loc:%s'%pagelocation
            return None
        #------------------------------------------------------------------------------ 
        #发帖的userid,username,userpage
        userid,username,userpage = self.analyze_uid_uname_upage_from_weibo(html)
        weiboinfo.update({'userid':userid})
        weiboinfo.update({'username':username})
        weiboinfo.update({'userpage':userpage})
        #------------------------------------------------------------------------------ 
        #微博内容 content 与 contentraw（原始html）
        content,contentraw = self.analyze_weibo_content(html)
        weiboinfo.update({'content':content})
        weiboinfo.update({'contentraw':contentraw})
        #------------------------------------------------------------------------------ 
        #分析转发rt，评论reply，转发超链rturl,评论超链replyurl
        rt,rturl,reply,replyurl = self.analyze_weibo_rtreply(html)
        weiboinfo.update({"rt":rt})
        weiboinfo.update({"rturl":rturl})
        weiboinfo.update({"reply":reply})
        weiboinfo.update({"replyurl":replyurl})
        #------------------------------------------------------------------------------
        #获取datetime 
        datetime = self.analyze_weibo_datetime(html)
        weiboinfo.update({"datetime":datetime})
        #------------------------------------------------------------------------------
        #打印这条weibo析取信息
        if showdetail:
            self.printweiboinfo(weiboinfo)
        
        #返回weiboinfo={}
        return weiboinfo 
            
    def analyze_weibo_atwho(self,html):
        '''
        这条weibo at了谁
        待完善
        '''
        soup = BeautifulSoup(html)
        #待完善
        return ''

    def analyze_weibo_weiboid(self,html):
        '''
        从html找出weiboid，返回str weiboid
        '''
        soup = BeautifulSoup(html)
        idtag = soup.find('div',{'class':'c'})
        try:
            weiboid = idtag['id']
        except KeyError,E:
            #print "这不是微博(无weiboid)"
            return None
        return str(weiboid)
    
    def analyze_uid_uname_upage_from_weibo(self,html):
        '''
        从html找出发weibo的(userid,username,userpage)
        '''
        soup = BeautifulSoup(html)
        usertag = soup.div.div.a
        username = usertag.get_text()
        userpage = usertag.get('href')
        
        if('profile' in userpage):
            userid = userpage.split('/')[-1]
        else:
            userid = userpage
            print 'analyze_uid_uname_upage_from_weibo():获取userid错误'
        return (str(userid),str(username),str(userpage))
    
    def analyze_weibo_content(self,html):
        '''
        从html找出content，以及源代码contentraw
        获取第一个span即可
        返回(content,contentraw)
        '''
        soup = BeautifulSoup(html)
        contenttag = soup.find('span')
        if contenttag:
            content = contenttag.get_text()
        else:
            content = ''
            print '获取content失败'
        #获取contentraw
        if contenttag:
            contentraw = str(contenttag)
        else:
            contentraw = ''
            
        return (str(content),contentraw)
    
    def analyze_weibo_rtreply(self,html):
        '''
        从html分析:转发rt，评论reply，转发超链rturl,评论超链replyurl
        返回(rt,rturl,reply,replyurl)
        '''
        #获取转发，评论字符 rtchars='转发[2]' replychars='评论'
        #rt reply一般在两个span中间，用re找
        replytag = ''
        rttag = ''
        replychars=''
        rtchars=''
        rt=0
        reply=0
        rturl=''
        replyurl=''
        
        regex = '''/span>(.+?)<span class="ct"'''
        res = re.compile(regex).search(html)
        if res:# rtreply='<a href= replyurl ...>评论[1]</a> <a href= rturl>转发[2]</a>'
            rtreply = str(res.group(1))
            tag = BeautifulSoup(rtreply)
            allprobablytags = tag.find_all('a')
            #下面设置rttag 与 replytag，使：
            #replytag = bs('<a href= replyurl ...>评论[1]</a>')
            #rttag = bs('<a href= rturl>转发[2]</a>')
            for tag in allprobablytags:
                if("转发" in tag.get_text()):
                    rttag = tag
                elif("评论" in tag.get_text()):
                    replytag = tag
                else:
                    pass
            
            if rttag is None:
                print "解析微博 转发 错误！"
                print rtreply
            elif replytag is None:
                print "解析微博 评论 错误！"
                print rtreply
            else:#获取 评论[i] 转发[j] 字符串
                replychars = str(replytag.contents[0]) #'转发[2]'
                rtchars = str(rttag.contents[0]) # '评论' or'评论[0]'
            
            #分析转发数rt
            if('[' and ']' in rtchars):
                res = re.compile('\[(.+?)\]').search(rtchars)
                if res is not None:
                    rt = int(res.group(1))
            else:rt=0
            #评论数reply
            if('[' and ']' in replychars):
                res = re.compile('\[(.+?)\]').search(replychars)
                if res is not None:
                    reply = int(res.group(1))
            else:reply=0
            
            #分析转发超链rturl,评论超链replyurl
            rturl=''
            replyurl=''
            if replytag.get('href'):
                replyurl = replytag.get('href')
            if rttag.get('href'):
                rturl = rttag.get('href')
                        
        return (rt,rturl,reply,replyurl)
               
    def analyze_weibo_datetime(self,html):
        '''
        分析weibo html的时间，以字符串返回
        '''
        soup = BeautifulSoup(html)
        datetime = soup.find('span',{'class':'ct'}).get_text()
        if datetime:
            dt = str(datetime)
        else:
            dt = ''
            print '获取datetime失败'
        #待改善：2012-12-13 16:02:59 或者 5分钟前 或者 01月16日 11:11 或者 刚才   
        return dt
    
    def test_rtreply_analyze(self):
        #测试rtreply_analyze()分析本地的rt reply网页
        print '测试：rt_analyze(),reply_analyze()，观察需要先删除db文件，执行后打开db文件观察是否将网页内容析取到db，是否报错'
        self.createweibostable()
        nonereply =  '/Users/mac/Dropbox/weiquncrawler/replytest/none-reply.html'
        multireply = '/Users/mac/Dropbox/weiquncrawler/replytest/reply-multi-page.html'
        with open(nonereply,'r') as f:
            html = f.read()
            self.reply_analyze(html,nonereply)
        with open(multireply,'r') as f:
            html = f.read()
            self.reply_analyze(html,multireply)
        self.end_rtreply_analyze_to_db()
        
    def printweiboinfo(self,weiboinfo):
        '''
        任务：打印weiboinfo{}中内容
        '''
        pagelocation = str(weiboinfo['pagelocation'])
        weiboid = str(weiboinfo['weiboid'])
        username = str(weiboinfo['username'])
        userid = str(weiboinfo['userid'])
        userpage = str(weiboinfo['userpage'])
        content = str(weiboinfo['content'])
        rt = int(weiboinfo['rt'])
        reply = int(weiboinfo['reply'])
        replyurl = str(weiboinfo['replyurl'])
        rturl = str(weiboinfo['rturl'])
        datetime = str(weiboinfo['datetime'])
        print "___________微博___________"
        print "微博所在页："+pagelocation        
        print "微博id："+weiboid
        print "用户名："+username+',用户id：'+userid+",用户主页："+userpage
        print "微博内容："+content
        print "评论数:%d,转发数:%d"%(reply,rt)
        print "评论url:%s\n转发url：%s"%(replyurl,rturl)  
        print '发微博时间:|'+datetime+'|' 
        pass
'''
def change_cookies():
    global COOKIE
    global COOKIE1
    global COOKIE2
    global COOKIE3
    global COOKIE4
    global COOKIE5
    
    if COOKIE == COOKIE1:
        COOKIE = COOKIE2
    elif COOKIE == COOKIE2:
        COOKIE = COOKIE3
    elif COOKIE == COOKIE3:
        COOKIE = COOKIE4
    elif COOKIE == COOKIE4:
        COOKIE = COOKIE5
    elif COOKIE == COOKIE5:
        COOKIE = COOKIE1
    else:
        COOKIE = COOKIE1
    
    print '更换COOKIE!',COOKIE
    print HEADERS_WEIQUN
'''    
def delayfunc(times):

    '''
    global TRAP_TIMES       
    print "TRAP_TIMES:",TRAP_TIMES
    
    TRAP_TIMES+=1
    if TRAP_TIMES > 5:
        #change_cookies()
        TRAP_TIMES = 0
        return int(5)
    '''    
    
    if times == 1:
        sleeptime = int(3)
    elif times == 2:
        sleeptime = int(4)
    elif times == 3:
        sleeptime = int(7)
    elif times == 4:
        sleeptime = int(120)
    elif times == 5:
        sleeptime = int(240)
    elif times == 6:
        sleeptime = int(480)
    elif times == 6:
        sleeptime = int(3600)
    else:
        sleeptime = int(3600)
        
    return sleeptime
    pass
    
def run_my_crawler(crawler,pagelist):
    try:
        for i in pagelist:
            trap_in_same_page = 0
            success = crawler.weiqun_crawl_page(i)
            while not success:
                print '第%d页遇见陷阱' % i
                trap_in_same_page+=1
                sleeptime = delayfunc(trap_in_same_page)
                
                #换COOKIES
                if sleeptime > 50:
                    crawler.change_cookie_headers()
                    trap_in_same_page = 0
                else:
                    print '\t第%d次被陷,睡眠%d秒'%(trap_in_same_page,sleeptime)
                    time.sleep(sleeptime)
                #如果成功下载,则跳出while
                if crawler.weiqun_crawl_page(i):
                    break
                #如果下载同一页 更换cookie超过一定次数,停止
                if crawler.change_cookie_times > 10:
                    print 'CHANGE COOKIE MORE THAN %d times, return False'%crawler.change_cookie_times 
                    return False
    except Exception as e:
        print e
        print "Error occured in run_my_crawler,pid:{1}\nError:{2}",os.getpid(),e
        
def get_pages_to_download(crawler,startpage,endpage):
    '''
    任务:找出crawler.userdbname的数据库表download 没有下载过的微群page号
    返回:pages[]
    '''
    pages = []
    weiqunid = str(crawler.weiqunID)
     
    return pages


    

def multi_thread_crawl_weiqun(crawler,startpage,endpage,threadnum,showdetail = True):
    print '%d线程准备下载微群%s的%d页微博'%(threadnum,str(crawler.weiqunID),crawler.endpage)
    #多线程爬取
    if threadnum>=1:
        #读取db未下载微群页到crawler.weiqun_pages2download[]
        crawler.load_weiqun_pages2download()
        #print 'thread=%d'%threadnum
        pagelist = [i for i in crawler.weiqun_pages2download]
        #如果有page需要下载
        if pagelist:
            #若无法拆分则1线程下载
            if len(pagelist)<threadnum:
                succ = multi_thread_crawl_weiqun(crawler,startpage,endpage,1,showdetail)
                return succ
            else:#可以拆分则拆分
                pagelist_list = chunks_avg(pagelist,threadnum)
                for pagelist in pagelist_list:    
                    p = Process(target=run_my_crawler, args=(crawler,pagelist) )
                    p.start()
                    time.sleep(0)
                return True
        else:
            return False
            
    #以下无用
    #开始顺序爬微群第startpage~endpage页
    elif threadnum==0:
        #读取db未下载微群页到crawler.weiqun_pages2download[]
        crawler.load_weiqun_pages2download()
        #print 'thread==1'
        for i in crawler.weiqun_pages2download:            
            trap_in_same_page = 0
            success = crawler.weiqun_crawl_page(i)
            while not success:
                print '第%d页遇见陷阱' % i
                trap_in_same_page+=1
                sleeptime = delayfunc(trap_in_same_page)
                
                #换COOKIES
                if sleeptime > 50:
                    crawler.change_cookie_headers()
                else:
                    print '\t第%d次被陷,睡眠%d秒'%(trap_in_same_page,sleeptime)
                    time.sleep(sleeptime)
                #如果成功下载,则跳出while
                if crawler.weiqun_crawl_page(i):
                    break
                #如果更换cookie超过一定次数,停止
                if crawler.change_cookie_times > 10:
                    print 'CHANGE COOKIE MORE THAN %d times, return False'%crawler.change_cookie_times 
                    return False
                
            
        return True
    else:
        return False
        
#测试按键有否按下
def kbhit():
    fd = sys.stdin.fileno()
    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    try:
        while True:
            try:
                c = sys.stdin.read(1)
                return True
            except IOError:
                return False
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
        
                
if __name__ == '__main__':
    LOGIN_URL = 'http://weibo.cn' #测试用户登陆用
    
    #!编码重要:设置python(2.7.3)的内部处理encoding使用utf-8(默认ascii),以确保能在mac命令行下python执行本文件
    #详见http://docs.python.org/2/howto/unicode.html
    reload(sys)
    sys.setdefaultencoding('utf-8')
    print '系统编码：'
    print sys.getdefaultencoding()
    
    #weiquns=[('./张国荣','./张国荣.db',3231589944,6248,6593,LOGIN_URL)]
    
    
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


    LOGIN_USER_NAME = 'daviddivad3231589944'
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
    #准备db的下载列表
    create_user_db_table(userdbname)
        
    
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
        
        #update下载列表db(初次下载完成使用),返回未下载页数pages
        #crawler.update_download_list( endpage,showdetail=True)
        
        #建立下载列表
        crawler.load_weiqun_pages2download()

        #注意，登陆weibo.cn 和访问微群Headers不一样！
        #Headers使用Firefox登陆用插件Firebug获取
    for crawler in crawlers:
            #对单个微群 n线程爬取微群crawler
            threadnum = 10 #单群10线程一般会导致封禁
            multi_thread_crawl_weiqun(crawler, crawler.startpage, crawler.endpage,\
                threadnum, showdetail=True)
            
            begin_pages = len(crawler.weiqun_pages2download)    
            print '======= 启动爬虫%d线程 微群id:%s 任务:%d页 ======'%(threadnum,\
                str(crawler.weiqunID),begin_pages )
            
            
            #--------------------------分析weibo部分----------------------------- 
            #从磁盘上的网页pages内抽取微博信息weiboinfos[],并把分离的每条微博存到磁盘
            weiboinfos = crawler.start_analyze_weibos_from_disk(showdetail=False)
            #把微博信息存储到数据库中
            crawler.end_analyze_weibos_to_db()
            
            
            #--------------------------处理RT Reply部分----------------------------- 
            #从数据库中读取每条微博的评论`转发url，下载到本地
            crawler.rtreply_crawl(startpage,endpage,showdetail=True)
    
            #分析本地的rt reply网页（返回失败页路径）
            crawler.start_rtreply_analyze()
            #储存rt reply分析结果到db
            crawler.end_rtreply_analyze_to_db()
            
                        

