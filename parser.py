#!/usr/bin/python

import struct
import binascii
import datetime
import os
import sys

def locate_cache_dir(rootpath=None):
    if not rootpath:
        tpath = os.path.expanduser("~")+"/.cache"
    else:
        tpath = rootpath+"/.cache"
    for root, dirs, files in os.walk(tpath):
        for d in dirs:
            if d.endswith(".default"):
                directory = root+"/"+d+"/Cache"
                break
    try:
        return directory
    except NameError:
        print >>sys.stderr, "no cache dir"
        exit(1)

def _hexdump(data,highlight=-1,endlight=-1):
    def _Split_String(s):
        __i=0
        while __i < len(s):
            __i += 2
            yield s[__i-2:__i]

    i = 0
    while i < len(data):
        dhex = binascii.b2a_hex(data[i:i+16])
        ascstring = ""
        print "%04X" % i,
        for r in _Split_String(dhex):
            if highlight <= i <= endlight:
                print r,
                #print '\033[1m'+__r+'\033[0m',
            else:
                print r,
            if int(r,16) >= 32 and int (r,16) <= 127:
                ascstring += chr(int(r,16))
            else:
                ascstring += '.'

        print ((32-len(dhex))/2)*"   ",
        #print 'X'*((32-len(dhex))*2),
        print " |  ",ascstring


        i += 16
    print "--"

class Metadata(object):
    
    def print_data(self):
        pass

class InternalMetadata(Metadata):
    def __init__(self,buf):

        self.fetchcount = struct.unpack(">I",buf[8:12])[0]
        self.firstfetch = datetime.datetime.fromtimestamp(struct.unpack(">I",buf[12:16])[0])
        self.lastfetch = datetime.datetime.fromtimestamp(struct.unpack(">I",buf[16:20])[0])
        self.requestsize = struct.unpack(">I",buf[28:32])[0]
        self.responsesize = struct.unpack(">I",buf[32:36])[0]
        self.request = buf[36:36+self.requestsize-1]
        self.response = buf[36+self.requestsize:]

    def disp(self):
        print self.request,self.fetchcount,self.firstfetch,self.lastfetch

    def get_url(self):
        return self.request

class Data(object):
    def print_data(self):
        print len(self.data)
    
class InternalData(Data):
    def __init__(self,buf):
        self.filename = ""
        self.data = buf


class ExternalData(Data):
    def __init__(self,filename):
        try:
            fp = open(DIR+"/"+filename)
            self.data = fp.read()
            fp.close()
            #print "+"+filename
        except IOError:
            pass
            #print "-"+filename

class Bucket(object):
    def __init__(self,b,c):
        self.hashnumber = b[0]
        self.eviction = b[1]
        self.datalocation = b[2]
        self.metalocation = b[3]
        self.c = c

        self.loc = (self.datalocation & 0x30000000) >> 28
        self.mloc = (self.metalocation & 0x30000000) >> 28
        if self.hashnumber == 0:
            self.dataclass = None
            self.metadataclass = None
            return

        if self.loc != 0:
            self.eblocks = ((self.datalocation & 0x03000000) >> 24) +1
            self.startblock = self.datalocation & 0x00ffffff
            self.filename = ""
            self.datablock = c[self.loc].read_data(self.startblock,self.eblocks)
            q = InternalData(self.datablock)
        else:
            self.eblocks = -1
            self.startblock = -1
            ftmp = "%08X%s%02x" % (self.hashnumber,"d",(self.datalocation & 0x000000ff))
            if (self.datalocation & 0x000000ff) != 1:
                self.filename = ""
                q = None
            else:
                self.filename = "%s/%s/%s" % (ftmp[0],ftmp[1:3],ftmp[3:])
                q = ExternalData(self.filename)

        self.dataclass = q


        if self.mloc != 0:
            self.emblocks = ((self.metalocation & 0x03000000) >> 24) +1
            self.mstartblock = self.metalocation & 0x00ffffff
            self.mfilename = ""
            self.metadatablock = c[self.mloc].read_data(self.mstartblock,self.emblocks)
            #print self.mloc, self.mstartblock, self.emblocks
            q = InternalMetadata(self.metadatablock)
        else:
            self.emblocks = -1
            self.mstartblock = -1
            ftmp = "%08X%s%02x" % (self.hashnumber,"m",(self.metalocation & 0x000000ff))
            if (self.metalocation & 0x000000ff) == 0:
                self.mfilename = ""
            else:
                self.mfilename = "%s/%s/%s" % (ftmp[0],ftmp[1:3],ftmp[3:])
            q = None
        self.metadataclass = q
    def disp(self):
        print "---"
        print "Loc/Mloc",self.loc,self.mloc
        if self.dataclass != None:
            print "Data:",self.startblock,self.eblocks,self.dataclass.print_data()
        if self.metadataclass != None:
            self.metadataclass.disp()
    def display_url(self):
        if self.metadataclass != None:
            print self.metadataclass.get_url()

    def search(self,url):
        if self.metadataclass.request == url:
            return True
        else:
            return False


class CacheMap(object):
    def __init__(self,fname,c):
        fp = open(fname,"r")
        self.c = c
        self.version = fp.read(4)
        self.datasize,self.entrycount,self.dirty,self.recordcount = struct.unpack(">IIII",fp.read(16))
        self.e_array = struct.unpack(">IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",fp.read(128))
        self.u_array = struct.unpack(">IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",fp.read(128))
        print self.datasize,self.entrycount,self.dirty,self.recordcount
        self.bucketraw=[]
        self.bucket=[]
        while True:
            try:
                buf = fp.read(16)
                print "x"
                if len(buf) < 16:
                    break
                self.bucketraw.append(struct.unpack(">IIII",buf))
            except IOError:
                break

        for b in self.bucketraw:
            tbuck = Bucket(b,self.c)
            if tbuck.metadataclass != None:
                self.bucket.append(tbuck)

        i=0;
        for b in self.bucket:
            if b.metadataclass == None:
                continue
            i += 1
        print i,len(self.bucket)

        fp.close()

    def search(self, url):
        for b in self.bucket:
            if b.search(url) == True:
                return b
        return None

    def display_urls(self):
        for f in self.bucket:
            f.display_url()
            

class CacheFile(object):
    def __init__(self,fname,blocks):
        self.blocks = blocks
        self.cbsize = 4194304 / self.blocks
        fp = open(fname,"r")
        self.header = fp.read(blocks)
        self.data = fp.read()
        fp.close()
    def __repr__(self):
        return "<CacheFile %d, %d>" % (self.blocks,self.cbsize)

    def read_data(self,s,n):
        try:
            return self.data[self.cbsize*s:self.cbsize*(s+n)+1]
        except:
            return None


DIR=locate_cache_dir("/var/lib/lxc/forge-lxc/rootfs/home/forge")
#DIR=locate_cache_dir()

c = (None,CacheFile(DIR+"/_CACHE_001_",16384),CacheFile(DIR+"/_CACHE_002_",4096),
     CacheFile(DIR+"/_CACHE_003_",1024))
cm = CacheMap(DIR+"/_CACHE_MAP_",c)
cm.display_urls()
"""
if y:
    y.disp()
    foo = open("xyzzy", "w")
    foo.write(y.dataclass.data)
    foo.close()
"""

        
