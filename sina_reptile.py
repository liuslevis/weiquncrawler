#!/usr/bin/python
#-*-coding:utf8-*-
from pprint import pprint
from weibopy.auth import OAuthHandler
from weibopy.api import API
from weibopy.binder import bind_api
from weibopy.error import WeibopError
import time,os,pickle,sys
import logging.config 
from multiprocessing import Process

import sqlite3 as sqlite
import math
import re
MAX_INSERT_ERROR = 5000
#from pymongo import Connection
CALL_BACK = 'http://www.littlebuster.com'
CALL_BACK=None
CALL_BACK='oob'
mongo_addr = 'localhost'
mongo_port = 27017
db_name = 'weibo'


a_consumer_key = '211160679'
a_consumer_secret = '63b64d531b98c2dbff2443816f274dd3'
a_key = '44bd489d6a128abefdd297ae8d4a494d'
a_secret = 'fb4d6d537ccc6b23d21dc888007a08d6'
someoneid = '1404376560'
davidid='3231589944'
a_ids = [davidid]

class Sina_reptile():
    """
    爬取sina微博数据
    """

    def __init__(self,consumer_key,consumer_secret,userdbname):
        self.consumer_key,self.consumer_secret = consumer_key,consumer_secret
        self.con_user = None
        self.cur_user = None
        try:
            self.con_user = sqlite.connect(userdbname,timeout = 20)
            self.cur_user = self.con_user.cursor()
        except Exception,e:
            print 'Sina_reptile init无法连接数据库!'
            print e
            return None
        #self.connection = Connection(mongo_addr,mongo_port)
        #self.db = self.connection[db_name]
        #self.collection_userprofile = self.db['userprofile']
        #self.collection_statuses = self.db['statuses']

    def getAtt(self, key):
        try:
            return self.obj.__getattribute__(key)
        except Exception, e:
            print e
            return ''

    def getAttValue(self, obj, key):
        try:
            return obj.__getattribute__(key)
        except Exception, e:
            print e
            return ''

    def auth(self):
        """
        用于获取sina微博  access_token 和access_secret
        """
        if len(self.consumer_key) == 0:
            print "Please set consumer_key"
            return
        
        if len(self.consumer_secret) == 0:
            print "Please set consumer_secret"
            return
        
        self.auth = OAuthHandler(self.consumer_key, self.consumer_secret,CALL_BACK)
        auth_url = self.auth.get_authorization_url()
        print 'Please authorize: ' + auth_url
        verifier = raw_input('PIN: ').strip()
        #403error
        self.auth.get_access_token(verifier)
        self.api = API(self.auth)
        print 'authorize success'

    def setToken(self, token, tokenSecret):
        """
        通过oauth协议以便能获取sina微博数据
        """
        self.auth = OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.setToken(token, tokenSecret)
        self.api = API(self.auth)

    def get_userprofile(self,id):
        """
        获取用户基本信息
        """
        try:
            userprofile = {}
            userprofile['id'] = id
            user = self.api.get_user(id)
            self.obj = user
            
            userprofile['screen_name'] = self.getAtt("screen_name")
            userprofile['name'] = self.getAtt("name")
            userprofile['province'] = self.getAtt("province")
            userprofile['city'] = self.getAtt("city")
            userprofile['location'] = self.getAtt("location")
            userprofile['description'] = self.getAtt("description")
            userprofile['url'] = self.getAtt("url")
            userprofile['profile_image_url'] = self.getAtt("profile_image_url")
            userprofile['domain'] = self.getAtt("domain")
            userprofile['gender'] = self.getAtt("gender")
            userprofile['followers_count'] = self.getAtt("followers_count")
            userprofile['friends_count'] = self.getAtt("friends_count")
            userprofile['statuses_count'] = self.getAtt("statuses_count")
            userprofile['favourites_count'] = self.getAtt("favourites_count")
            userprofile['created_at'] = self.getAtt("created_at")
            userprofile['following'] = self.getAtt("following")
            userprofile['allow_all_act_msg'] = self.getAtt("allow_all_act_msg")
            userprofile['geo_enabled'] = self.getAtt("geo_enabled")
            userprofile['verified'] = self.getAtt("verified")

#            for i in userprofile:
#                print type(i),type(userprofile[i])
#                print i,userprofile[i]
#            

        except WeibopError, e:      #捕获到的WeibopError错误的详细原因会被放置在对象e中
            print "error occured when access userprofile use user_id:",id
            print "Error:",e
            #log.error("Error occured when access userprofile use user_id:{0}\nError:{1}".format(id, e),exc_info=sys.exc_info())
            return None
            
        return userprofile

    def get_specific_weibo(self,id):
        """
        获取用户最近发表的50条微博
        """
        statusprofile = {}
        statusprofile['id'] = id
        try:
            #重新绑定get_status函数
            get_status = bind_api( path = '/statuses/show/{id}.json', 
                                 payload_type = 'status',
                                 allowed_param = ['id'])
        except:
            return "**绑定错误**"
        status = get_status(self.api,id)
        self.obj = status
        statusprofile['created_at'] = self.getAtt("created_at")
        statusprofile['text'] = self.getAtt("text")
        statusprofile['source'] = self.getAtt("source")
        statusprofile['favorited'] = self.getAtt("favorited")
        statusprofile['truncated'] = self.getAtt("ntruncatedame")
        statusprofile['in_reply_to_status_id'] = self.getAtt("in_reply_to_status_id")
        statusprofile['in_reply_to_user_id'] = self.getAtt("in_reply_to_user_id")
        statusprofile['in_reply_to_screen_name'] = self.getAtt("in_reply_to_screen_name")
        statusprofile['thumbnail_pic'] = self.getAtt("thumbnail_pic")
        statusprofile['bmiddle_pic'] = self.getAtt("bmiddle_pic")
        statusprofile['original_pic'] = self.getAtt("original_pic")
        statusprofile['geo'] = self.getAtt("geo")
        statusprofile['mid'] = self.getAtt("mid")
        statusprofile['retweeted_status'] = self.getAtt("retweeted_status")
        return statusprofile

    def get_latest_weibo(self,user_id,count):
        """
        获取用户最新发表的count条数据
        """
        statuses,statusprofile = [],{}
        try:            #error occur in the SDK
            timeline = self.api.user_timeline(count=count, user_id=user_id)
        except Exception as e:
            print "error occured when access status use user_id:",user_id
            print "Error:",e
            #log.error("Error occured when access status use user_id:{0}\nError:{1}".format(user_id, e),exc_info=sys.exc_info())
            return None
        for line in timeline:
            self.obj = line
            statusprofile['usr_id'] = user_id
            statusprofile['id'] = self.getAtt("id")
            statusprofile['created_at'] = self.getAtt("created_at")
            statusprofile['text'] = self.getAtt("text")
            statusprofile['source'] = self.getAtt("source")
            statusprofile['favorited'] = self.getAtt("favorited")
            statusprofile['truncated'] = self.getAtt("ntruncatedame")
            statusprofile['in_reply_to_status_id'] = self.getAtt("in_reply_to_status_id")
            statusprofile['in_reply_to_user_id'] = self.getAtt("in_reply_to_user_id")
            statusprofile['in_reply_to_screen_name'] = self.getAtt("in_reply_to_screen_name")
            statusprofile['thumbnail_pic'] = self.getAtt("thumbnail_pic")
            statusprofile['bmiddle_pic'] = self.getAtt("bmiddle_pic")
            statusprofile['original_pic'] = self.getAtt("original_pic")
            statusprofile['geo'] = repr(pickle.dumps(self.getAtt("geo"),pickle.HIGHEST_PROTOCOL))
            statusprofile['mid'] = self.getAtt("mid")
            statusprofile['retweeted_status'] = repr(pickle.dumps(self.getAtt("retweeted_status"),pickle.HIGHEST_PROTOCOL))
            statuses.append(statusprofile)

#            print '*************',type(statusprofile['retweeted_status']),statusprofile['retweeted_status'],'********'
#        for j in statuses:
#            for i in j:
#                print type(i),type(j[i])
#                print i,j[i]

        return statuses

    def friends_ids(self,id):
        """
        获取用户关注列表id
        """
        next_cursor,cursor = 1,0
        ids = []
        while(0!=next_cursor):
            fids = self.api.friends_ids(user_id=id,cursor=cursor)
            self.obj = fids
            ids.extend(self.getAtt("ids"))
            cursor = next_cursor = self.getAtt("next_cursor")
            previous_cursor = self.getAtt("previous_cursor")
        return ids
    
    def followers_ids(self,id):
        """
        获取用户粉丝列表id
        """
        next_cursor,cursor = 1,0
        ids = []
        while(0!=next_cursor):
            fids = self.api.followers_ids(user_id=id,cursor=cursor)
            self.obj = fids
            ids.extend(self.getAtt("ids"))
            cursor = next_cursor = self.getAtt("next_cursor")
            previous_cursor = self.getAtt("previous_cursor")
        return ids
    
    def manage_access(self):
        """
        管理应用访问API速度,适时进行沉睡
        """
        info = self.api.rate_limit_status()
        self.obj = info
        sleep_time = round( (float)(self.getAtt("reset_time_in_seconds"))/self.getAtt("remaining_hits"),2 ) if self.getAtt("remaining_hits") else self.getAtt("reset_time_in_seconds")
        print self.getAtt("remaining_hits"),self.getAtt("reset_time_in_seconds"),self.getAtt("hourly_limit"),self.getAtt("reset_time")
        print "sleep time:",sleep_time,'pid:',os.getpid()
        time.sleep(sleep_time + 1.5)

    def save_data(self,userprofile,statuses):
        #self.collection_statuses.insert(statuses)
        #self.collection_userprofile.insert(userprofile)
        pass
        
def reptile(sina_reptile,userid):
    ids_num,ids,new_ids,return_ids = 1,[userid],[userid],[]
    while(ids_num <= 10000000):
        next_ids = []
        for id in new_ids:
            try:
                sina_reptile.manage_access()
                return_ids = sina_reptile.friends_ids(id)
                ids.extend(return_ids)
                userprofile = sina_reptile.get_userprofile(id)
                statuses = sina_reptile.get_latest_weibo(count=50, user_id=id)
                if statuses is None or userprofile is None:
                    continue
                sina_reptile.save_data(userprofile,statuses)
            except Exception as e:
                print "log Error occured in reptile"
                #log.error("Error occured in reptile,id:{0}\nError:{1}".format(id, e),exc_info=sys.exc_info())
                time.sleep(60)
                continue
            ids_num+=1
            print ids_num
            if(ids_num >= 10000000):break
            next_ids.extend(return_ids)
        next_ids,new_ids = new_ids,next_ids

def run_crawler(consumer_key,consumer_secret,key,secret,userid,userdbname):
    try:
        
        sina_reptile = Sina_reptile(consumer_key,consumer_secret,userdbname)
        sina_reptile.setToken(key, secret)
        reptile(sina_reptile,userid)
        #sina_reptile.connection.close()
    except Exception as e:
        print e
        print 'log Error  occured in run_crawler'
        #log.error("Error occured in run_crawler,pid:{1}\nError:{2}".format(os.getpid(), e),exc_info=sys.exc_info())

def run_my_crawler(consumer_key,consumer_secret,key,secret,userdbname,ids):
    if ids:
        if len(ids)>0:
            try:
                sina_reptile = Sina_reptile(consumer_key,consumer_secret,userdbname)
                sina_reptile.setToken(key, secret)
                reptile_friends_of_uids_to_db(sina_reptile,ids,userdbname)
            except Exception as e:
                print 'Error occured in run_my_crawler,pid:%s'%str(os.getpid())
                print e
                #log.error("Error occured in run_my_crawler,pid:{1}\nError:{2}".format(os.getpid(), e),exc_info=sys.exc_info())
        else:
            print 'run_my_crawler ids[]<=0',ids
    else:
        print 'run_my_crawler ids[] is None',ids

def get_uids_in_weibodb(weibodbname):
    '''
    任务:从数据库weibodbname中获取uids='xxx'
    返回:uids[]
        None 如果无法连接数据库
    '''
    #init db
    try:
        con_weibo = sqlite.connect(weibodbname)
        cur_weibo = con_weibo.cursor()
    except Exception,e:
        print 'reptile_friends_of_uids_to_db无法连接数据库!'
        print e
        return None
    
    try:
        cur_weibo.execute("SELECT DISTINCT userid FROM weibos")
        con_weibo.commit()
    except Exception,E:
        print 'get_uids_in_weibodb：从db读取uid错误'
        print E
        return None


    list = cur_weibo.fetchall()
    uids=[]
    print 'get_uids_in_weibodb共读取用户：%d个 从weibodb:%s'%(len(list),weibodbname)
    for row in list:
        uid, = row
        if uid:
            uids.append(str(uid))
    print 'get_uids_in_weibodb返回取用户：%d个'%len(uids)
    con_weibo.close()
    return uids
        
def get_undonwload_ids(ids):
    '''
    任务:从userdbname数据库中的relation表中
    返回:[]待下载的ids
        None 连接数据库错误
    '''
    print 'get_undonwload_ids:得到%d个用户,从%s找出待下载关系的用户'%(len(ids),userdbname)
    #init db
    try:
        con_user = sqlite.connect(userdbname)
        cur_user = con_user.cursor()
    except Exception,e:
        print 'get_undonwload_ids 无法连接数据库!'
        print e
        return None
    
    #从gotrelation表找出没下载过的ids 
    ids_to_download = []
    for userid in ids:
        userid = str(userid)
        if not has_gotrelation_db(cur_user,con_user,userid):
            if userid not in ids_to_download:
                ids_to_download.append(userid)
                
    print 'get_undonwload_ids:还需要下载%d个用户'%(len(ids_to_download))
    return ids_to_download


def create_user_db_table(userdbname):
    #init db
    print 'create_user_db_table in db:%s'%userdbname
    try:
        con_user = sqlite.connect(userdbname)
        cur_user = con_user.cursor()
    except Exception,e:
        print 'create_user_db_table: error'
        print e
        return None
    #create tb   
    try:
        cur_user.execute('CREATE TABLE relation(userid TEXT ,followerid TEXT,PRIMARY KEY(userid,followerid));')
        con_user.commit()
    except Exception,e:
        print e
        pass
    try:
        cur_user.execute('CREATE TABLE gotrelation(userid TEXT PRIMARY KEY,gotfans INTERGER,gotfos INTERGER);')
        con_user.commit()
    except Exception,e:
        print e
        pass

def reptile_friends_of_uids_to_db(sina_reptile,ids_to_download,userdbname):
    '''
    任务:把ids的粉丝/关注用api爬取,放到userdbname数据库中的relation表中
    返回:None 无法连接数据库
        True 完成
    '''
    print 'reptile_friends_of_uids_to_db:得到%d个用户,待爬取关系至%s'%(len(ids_to_download),userdbname)
       
    for userid in ids_to_download:
        #id 的关注
        frids = reptile_friends_of_uid(sina_reptile,userid)
        #id的粉丝
        foids = reptile_fos_of_uid(sina_reptile,userid)
        print 'reptile_friends_of_uids_to_db:为用户%s找到%d个关注,%d个粉丝'%(userid,len(frids),len(foids))
        count=0
        gotfans = len(foids)
        gotfos  = len(frids)
        ins_fans = 0
        ins_fos = 0
        has_relation = 0
        sql_fri = ''
        sql_fo = ''
        if frids:#用户的关注
            fri_ins_error = 0#记录插入fan错误次数
            for frid in frids:
                frid = str(frid)
                count+=1
                ins_fos+=1
                sql_fri = 'INSERT INTO relation(userid ,followerid) VALUES("%s","%s");'%(frid,userid)
                try:
                    sina_reptile.cur_user.execute(sql_fri)
                except Exception,e:
                    #print 'got fri relation %s fo %s'%(str(userid),str(frid))
                    has_relation+=1
                    fri_ins_error+=1
                    #print sql_fri
                    #print e
                    if fri_ins_error>MAX_INSERT_ERROR:#如果插入三次都错误,很有可能是已有记录,跳出for
                        print '\t插入%d次错误,跳出%s关注关系插入'%(fri_ins_error,userid)
                        break
                    continue
                    pass
            try:
                sina_reptile.con_user.commit()
            except Exception,e:
                print 'reptile_friends_of_uids_to_db commit插入%s的关注(%d个)有问题:'%(userid,len(frids))
                print e
                pass
            
        if foids:#用户的粉丝
            fo_ins_error = 0#记录插入fo错误次数
            for foid in foids:
                followerid = str(foid)
                count+=1
                ins_fans+=1
                sql_fo = 'INSERT INTO relation(userid ,followerid) VALUES("%s","%s");'%(userid,followerid)
                try:
                    sina_reptile.cur_user.execute(sql_fo)
                except Exception,e:
                    #print 'got fri relation %s fo %s'%(str(foid),str(userid))
                    has_relation+=1
                    fo_ins_error+=1
                    #print sql_fo
                    print e
                    if fo_ins_error>MAX_INSERT_ERROR:#如果插入三次都错误,很有可能是已有记录,跳出for
                        print '\t插入%d次错误,跳出%s粉丝关系插入'%(fo_ins_error,userid)
                        break
                    continue
                    pass
            try:
                sina_reptile.con_user.commit()
            except Exception,e:
                print 'reptile_friends_of_uids_to_db commit插入%s的粉丝(%d个)有问题:'%(userid,len(foids))
                print e
                pass
        
        if has_relation!=0:
            print '\tuid:%s已经有关系记录'%str(userid),has_relation,'个'

        
        if count!=(len(frids)+len(foids)):
            print '\t 用户%s少添加关系%d个'%(userid, (len(frids) + len(foids) - count) )
        
        #更新下载表gotrelation
        print '\t更新gotrelation表 uid:%s,fans/fos:'%userid,gotfans,gotfos
        update_gotrelation_db(sina_reptile.cur_user, sina_reptile.con_user,userid,gotfans,gotfos)
    
    sina_reptile.con_user.close()
    print 'reptile_friends_of_uids_to_db:完成%d个用户的关系爬取至%s'%(len(ids_to_download),userdbname)
    return True

def has_gotrelation_db(cur_user,con_user,uid,check_serious=True):
    '''
    任务:检查是否下载过关系
    #如果check_serious 则从db table relation与gotrelation找出fans fos数校对(1秒1个 慢)   
    #否则 查若有gotrelation项  则return True
    '''
    #如果严格检查,则从relation表中找出某个uid的 fans fos数量(1秒1个 慢)   
    if check_serious:
        fans=0
        fos=0
        #get fans relation num
        try:
            cur_user.execute("""SELECT COUNT(*) FROM relation WHERE userid=='%s' ;"""%uid)
            con_user.commit()
            res = cur_user.fetchone()
            fans,=res
        except Exception,e:
            print 'has_gotrelation_db 读取relation表有问题,uid= %s'%(uid)
            print e
            return False 
    
        #get fri relation num
        try:
            cur_user.execute("""SELECT COUNT(*) FROM relation WHERE followerid=='%s' ;"""%uid)
            con_user.commit()
            res = cur_user.fetchone()
            fos,=res
        except Exception,e:
            print 'has_gotrelation_db 读取relation表有问题,uid= %s'%(uid)
            print e
            return False 
    
    
    #从gotrelation表中获取 fans fos数(快)
    try:
        cur_user.execute("""SELECT userid,gotfans,gotfos FROM gotrelation WHERE userid=='%s' ;"""%uid)
        con_user.commit()
    except Exception,e:
        print 'has_gotrelation_db 读取gotrelation表有问题,uid= %s'%(uid)
        print e
        return False
        
    list = cur_user.fetchone()
    if list:
        userid,gotfans,gotfos = list
        if str(userid)==str(uid):
            #看参数决定是否严格检查
            if check_serious:
                if gotfans<=fans and gotfos<=fos:
                    #print 'has_got(serious)....',list,fans,fos
                    return True
            else:#不严格检查  有项则跳过
                #print 'not_got',list,fans,fos
                return True
    
    #print 'final_not_got',uid,fans,fos
    return False

#无用
def test_load_gotrelation_db(userids):
    userids=['1937245577','1402787970','1234567890']
    con_user = sqlite.connect('../users.db')
    cur_user = con_user.cursor()
    sql = '''SELECT    userid FROM    gotrelation WHERE userid=='%s' '''
    for userid in userids:
        try:
            cur_user.execute( sql%str(userid) )
            tup= cur_user.fetchone()
            
            if tup is not None:#有用户
                print sql,userid
                print tup
                
        except Exception,e:
            print 'test_load_gotrelation_db 读取gotrelation表有问题,uid= %s'%(userid)
            print e
    con_user.close()
                
#无用               
def load_gotrelation_db(cur,con,userids):
    '''
    给定userids,到users.db->gotrelation中看看是否有下载好的userid,若没有,加入wait_userids[]
    返回:需要下载的wait_userids
    '''
    #userids.sort()
    sql = '''SELECT    userid FROM    gotrelation WHERE userid=='%s' '''
    #sql = '''SELECT    count(*) FROM    gotrelation  '''
    wait_userids = []
    con_user = sqlite.connect('../users.db')
    cur_user = con_user.cursor()
    for userid in userids:
        #???没有返回??? 单步试试
        try:
            cur_user.execute( sql% str(userid) )
            tup= cur_user.fetchone()
            
            if tup is not None:#有用户
                print '\t已有用户:%s'%str(userid)
                print sql,userid
                print tup
            else:
                #print '\t没有用户:%s'%str(userid)
                wait_userids.append(userid)
                
        except Exception,e:
            print 'test_load_gotrelation_db 读取gotrelation表有问题,uid= %s'%(userid)
            print e
        
    print 'load_gotrelation_db 复查:需要下载%d个用户'%len(wait_userids)
    con_user.close()
    return wait_userids

def update_gotrelation_db(cur_user,con_user,userid,gotfans,gotfos):
    #更新下载表gotrelation
    try:
        cur_user.execute("""REPLACE INTO gotrelation(userid,gotfans,gotfos) VALUES('%s',%d,%d)"""%(userid,gotfans,gotfos))
        con_user.commit()
    except Exception,e:
        print 'update_gotrelation_db 更新gotrelation表有问题,uid= %s'%(userid)
        print e
        
    

def reptile_fos_of_uid(sina_reptile,id):
    '''
    返回:ids[] id的粉丝
    '''
    try:
        sina_reptile.manage_access()
        #ids = [int,int,...]
        return_ids = []
        return_ids.extend(sina_reptile.followers_ids(id))
        #print '获取id:%s的fos:'%id
        #print return_ids
    except Exception as e:
        #log.error("Error occured in reptile,id:{0}\nError:{1}".format(id, e),exc_info=sys.exc_info())
        print 'logerror("Error occured in reptile_fans_fos_of_uid,id:{0}\nError:{1}".format(id, e),exc_info=sys.exc_info()'
        time.sleep(60)
    return return_ids

def reptile_friends_of_uid(sina_reptile,id):
    '''
    返回:ids[] id关注的用户
    '''
    try:
        return_ids = []
        sina_reptile.manage_access()
        #ids = [int,int,...]
        return_ids.extend( sina_reptile.friends_ids(id))
        #print '获取id:%s的fos:'%id
        #print return_ids
    except Exception as e:
        #log.error("Error occured in reptile,id:{0}\nError:{1}".format(id, e),exc_info=sys.exc_info())
        print 'logerror("Error occured in reptile_friends_of_uid,id:{0}\nError:{1}".format(id, e),exc_info=sys.exc_info()'
        time.sleep(60)
    return return_ids


#split the arr into N chunks 
#如[1,2,3,4,5] m=2 -> [[1,2,3] [4,5]]
def chunks(arr, m):
    n = int(math.ceil(len(arr) / float(m)))
    return [arr[i:i + n] for i in range(0, len(arr), n)]

#或者让一共有m块，自动分（尽可能平均）
#如[1,2,3,4,5] m=2 -> [[1,3,5] [2,4]]
def chunks_avg(arr, m):
    n = int(math.ceil(len(arr) / float(m)))
    res = [arr[i:i + n] for i in range(0, len(arr), n)]
    
    if m < len(arr):
        maxsplit = m
    else:
        maxsplit = len(arr)
    newres = [ [] for i in range(0,maxsplit)]
    
    for i in range(0,len(arr)):
        newres[i%m].append(arr[i])
        pass
    return newres
    
def test_chunks():
    arr = []    
    m = 100
    for i in range(1,50):
        arr.append(i)

    res = chunks_avg(arr,m)
    print 'chunks_avg:'
    for i in res:
        print i

    res = chunks(arr,m)
    print 'chunks:'
    for i in res:
        print i
if __name__ == "__main__":
    '''
    读取weiqun2download.txt的weiqunid,从weiqunid.db获取用户id,用api下载用户关系
    '''
    
    #读weiqunid
    print '从weiqun2download.txt读取准备下载的weiqunIDs:'
    weiqunlist = 'weiqun2download.txt'
    weiqunIDs=[]
    weiqunparas=[]
    with open(weiqunlist) as f:
        for i in f.readlines():
            res = re.sub('#',' ',i).split(' ')
            weiqunid = res[0].strip()
            endpage = int(res[1].strip())
            startpage = 1
            print  'weiqunid:',weiqunid
            print  'page:',startpage,'~',endpage
            weiqunparas.append( (weiqunid,startpage,endpage) )
            weiqunIDs.append(weiqunid)

    logging.config.fileConfig("logging.conf")
    log = logging.getLogger('logger_sina_reptile')
    
    
    
    #consumer_key= '应用的key'
    #consumer_secret ='应用的App Secret'
    #token = '用户的Access token key'
    #tokenSecret = '用户的Access token secret'
    

    
    userdbname = '../users.db'
    weiqunids = weiqunIDs
    weibodbnames=[]
    ids_to_download = []
    
    
    
    # my test
    #sina_reptile = Sina_reptile(a_consumer_key,a_consumer_secret,userdbname)
    #sina_reptile.setToken(a_key, a_secret)
    
    #建立users.db(负责储存下载列表,储存用户关系)
    create_user_db_table(userdbname)
    
    #获取所有weiqundb的ids
    for weiqunid in weiqunids:
        weibodbnames.append('../weiqun/%s.db'%weiqunid)

    for weibodbname in weibodbnames:
        ids = get_uids_in_weibodb(weibodbname)
        if ids:
            ids_to_download.extend( get_undonwload_ids(ids) )
    
    #单个爬虫运行
    #reptile_friends_of_uids_to_db(sina_reptile,ids_to_download,userdbname)
    
    #多个爬虫运行
    
    #获取爬虫数目
    crawler_count = 0
    crawlerids = 'clawer.txt'#20线程
    crawlerids = 'crawlertest.txt'#2线程
    with open(crawlerids) as f:
        for i in f.readlines():
            crawler_count+=1
    print '有%d个sina API sectret key'%crawler_count
    
    #切分ids[]
    if len(ids_to_download):
        ids_list = chunks(ids_to_download,crawler_count)
        print '切分成任务块:',crawler_count
    else:#没有任务则推出
        print '没有任务,退出'
        sys.exit(0)
    i=0
    for ids in ids_list:
        i+=len(ids)
    print '\t把%d个ID分成%d个任务.\n开始爬行!!!!!!!!'%(i,len(ids_list))
    
    #开始爬行
    print 'API secret:'
    with open(crawlerids) as f:
        index=0
        for i in f.readlines():
            print i
            j = i.strip().split(' ')
            p = Process(target=run_my_crawler, args=(j[0],j[1],j[2],j[3],userdbname,ids_list[index]))
            index+=1
            print '爬虫%d启动!!'%index
            p.start()
            #time.sleep(10000)

    
    
    #friendids = reptile_friends_of_uid(sina_reptile,ids)
    #print friendids
    
    #userprofile = sina_reptile.get_userprofile(davidid)
    #weibo = sina_reptile.get_specific_weibo("3408234545293850")
    #print userprofile
    #sina_reptile.manage_access()
    #print weibo
    
    #'''


    
    
    # origins:
    #sina_reptile = Sina_reptile('2173594644','fc76ecb30a3734ec6e493e472c5797f8')
    #sina_reptile.auth()
    #sina_reptile.setToken("e42c9ac01abbb0ccf498689f70ecce56", "dee15395b02e87eedc56e380807528a8")
    #sina_reptile.get_userprofile("1735950160")
#    sina_reptile.get_specific_weibo("3408234545293850")
##    sina_reptile.get_latest_weibo(count=50, user_id="1735950160")
##    sina_reptile.friends_ids("1404376560")
#    reptile(sina_reptile)
#    sina_reptile.manage_access()
