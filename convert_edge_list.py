# -*- coding: utf-8 -*- 

import os
import sys

from itertools import count, izip
from collections import OrderedDict, Set

class IndexOrderedSet(Set):
    """An OrderedFrozenSet-like object
       Allows constant time 'index'ing
       But doesn't allow you to remove elements"""
    def __init__(self, iterable = ()):
        self.num = count()
        self.dict = OrderedDict(izip(iterable, self.num))
    def add(self, elem):
        if elem not in self:
            self.dict[elem] = next(self.num)
    def index(self, elem):
        return self.dict[elem]
    def __contains__(self, elem):
        return elem in self.dict
    def __len__(self):
        return len(self.dict)
    def __iter__(self):
        return iter(self.dict)
    def __repr__(self):
        return 'IndexOrderedSet({})'.format(self.dict.keys())
        
        
def getuidindex(uid,uid_list):
    '''
    获得uid(string)在表list[strings]中的位置
    返回 -1 如果不再表内
    '''
    i=-1
    if uid in uid_list:
        i = uid_list.index(uid)
        
    return i
    
def help():
    print "\t usage: python convert_userid_result.py relation_file.txt"
    print "\t note file must has .txt!"
    print "\t will translate ID to uid in .edgelist file,according to mapping in .map file."

    
    
if __name__ == '__main__':
    try:
        oldfile = sys.argv[1]
        oldfilebase = os.path.splitext(sys.argv[1])[0]
    except:
        help()
        exit()
    print 'converting relation(uid uid) to relation(index index) to edge list,weight free:',
    print oldfile
    newlines=[]
    #get src dst
    uid_list = []
    uid_set = IndexOrderedSet()
    pairs = []
    with open(oldfile) as f:
        count = 0
        for i in f.readlines():
            if i:
                count += 1
                if count % 10000 == 0:
                    print "已读取Edge:",count,"个"
                i = i.rstrip('\n')
                i = i.rstrip('\r')
                res = i.split('\t')
                src = int(res[0])
                dst = int(res[1])
                if src not in uid_set:
                    #uid_list.append(src)
                    uid_set.add(src)
                if dst not in uid_set:
                    #uid_list.append(dst)
                    uid_set.add(dst)
                pairs.append((src,dst))
        f.close()
    print "读取Edges完成"
    #sort mapping list
    #uid_set = set(uid_list)
    ##uid_list = []
    #for i in uid_set:
    #    i=int(i)
    #    uid_list.append(i)
    
    # trans pairs: 123141224 \t 1251231412 to 55 \t 43
    # save to .edgelist
    count = 0
    for pair in pairs:
        count+=1
        if count % 10000 == 0:
            print "已处理Edge:",count,"个"
        src,dst = pair
        isrc = uid_set.index(src) #getuidindex(src,uid_list)
        idst = uid_set.index(dst) #,uid_list)
        newline = str(isrc) + '\t' + str(idst) + '\n'
        newlines.extend(newline)
        #print isrc,' ,',idst
        
    
    newfile = oldfilebase + '.edgelist.txt'
    with open(newfile,'w') as f:
        f.writelines(newlines)
        f.close()
        
    # record mapping uid to index
    # save to .map
    mapfile = oldfilebase +'.map.txt'
    newlines = []
    for uid in uid_set:
        newline = str(uid) + '\t' + str(uid_set.index(uid)) + '\n'
        newlines.append(newline)
    with open(mapfile,'w') as f:
        f.writelines(newlines)
        f.close()
    
    print 'converting finished,gen 2 new file:'
    print newfile
    print mapfile
    