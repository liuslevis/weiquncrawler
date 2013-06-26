# -*- coding: utf-8 -*- 

import os
import sys

#处理前TOPN名用户
TOPN = 20

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
    print "\t usage: python convert_userid_result.py relation_file.rank"
    print "\t will translate ID to uid in .rank file,according to .map file."
    print "\t .rank could be any other string, e.g. salsa,pagerank, etc."
    
if __name__ == '__main__':

    try:
        srcfile = sys.argv[1]
        resfile = srcfile+'.uid.txt'
    except:
        help()
        exit()
        
    tmp = os.path.splitext(sys.argv[1])[0]
    mapfile = os.path.splitext(tmp)[0] + '.map.txt'

    print 'convert rank result file to:'
    print resfile
    print 'using mapfile:'
    print mapfile

    #get mapping
    uid_list = []
    with open(mapfile) as f:
        for line in f.readlines():
            if line:
                uid = line.split()[0]        
                uid_list.append(int(uid))
        f.close()
    
    
    
    
    #get rank res from srcfile:
    #Print top 20 vertices:(blank with \t)
    #1. 27	0.772947
    #2. 19	0.739721
    #3. 25	0.710808
    oldlines = []
    with open(srcfile) as f:
        for i in f.readlines():
            oldlines.append(i)
        f.close()
        
    #处理前20名
    newlines = [ oldlines[0]]
    for line in oldlines:
        if oldlines.index(line) < TOPN+1 and oldlines.index(line)>0:
            res = line.split()
            mapID = res[1]
            uid = str(uid_list[int(mapID)])
            print mapID,'->',uid
            res[1] = uid
            newline = ''
            for i in res:
                newline+= i+' '
            newline+='\n'
            newlines.append(newline)
            
    newlines.extend( oldlines[TOPN+1:])
    #写入结果 resfile
    with open(resfile,'w') as f:
        f.writelines(newlines)
        f.close()
                
    print 'converted rankfile,gen 1 new file:'
    print resfile
    