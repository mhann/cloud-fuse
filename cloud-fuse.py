from __future__ import print_function, absolute_import, division

import logging

from errno import ENOENT
from stat import S_IFDIR, S_IFREG
from sys import argv, exit
from time import time
import math
import sqlite3
import os
from sqlalchemy import Column, String, Integer, ForeignKey, create_engine

from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn, fuse_get_context

Base = declarative_base()

class File(Base):
    __tablename__ = 'files'
    id            = Column(Integer, primary_key=True)
    path          = Column(String)
    name          = Column(String)
    permissions   = Column(Integer)
    size          = Column(Integer)

#    def __init__(self, name, permissions, size, folder=None):
#        self.name = name
#        self.permissions = permissions
#        self.size = size
#        self.folder = folder

#        self.save()

#    def save(self):
#        dbHandle=Database()

        #dbHandle.safeWriteOperation("INSERT INTO files (name, folder, permissions, size) VALUES (?, ?, ?, ?)", [self.name, self.folder, self.permissions, self.size]);

#    @staticmethod
#    def list():
#        dbHandle=Database()
#
#        c = dbHandle.conn.cursor()
#
#        fileList = []
#
#        for row in c.execute("SELECT name, permissions, size, folder FROM files"):
#            tmpFile = File(row[0], row[1], row[2], row[3])
#            print("listing file with name %s", row[0], tmpFile.name)
#            fileList += [tmpFile]
#
#        dbHandle.conn.commit()
#
#        return fileList


class Singleton(object):

    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = object.__new__(cls, *args, **kwargs)

        return cls._instances[cls]

class Database(Singleton):
    conn = ""

    def __init__(self):
        if False == os.path.isdir('./example.db'):
            self.conn = sqlite3.connect('example.db')
            self.setupDatabase()
        else:
            self.conn = sqlite3.connect('example.db')

    def safeWriteOperation(self, sql, parameters=[]):
        c = self.conn.cursor()

        try:
            c.execute(sql, parameters)
        except:
            print("There was an error running the database query")

        self.conn.commit()

    def setupDatabase(self):
        self.safeWriteOperation("CREATE TABLE files  (id INTEGER PRIMARY KEY AUTOINCREMENT, name text, permissions int, size int, folder int)")
        self.safeWriteOperation("CREATE TABLE folder (id INTEGER PRIMARY KEY AUTOINCREMENT, name text, permissions int, size int, folder int)")
        self.safeWriteOperation("CREATE TABLE blocks (id INTEGER PRIMARY KEY AUTOINCREMENT, cloudName text, offset int, file int, size int)")

class Context(LoggingMixIn, Operations):

    def preparePath(self, path):
        return path[1:]

    def listOfFileNames(self):
        knownFiles = []

        for file in s.query(File).order_by(File.id):
            knownFiles.append(file.name)

        return knownFiles

    def addFile(self, path):
        newFile = File(path=path, name=path, permissions=777, size=0)
        s.add(newFile)
        s.commit()
        return newFile.id

    def fileExists(self, path):
        print("Checking if {} exists".format(self.preparePath(path)))
        fileCountQuery = s.query(File).filter_by(path=self.preparePath(path))
        fileCount = fileCountQuery.count()

        print("Database query returned {}".format(fileCount))

        if fileCount == 0:
            print("File Does Not Exist")
            return False
        elif fileCount == 1:
            print("File Exists")
            return True
        else:
            print("Something unexpected happened - we should not have more than one file")

            # Return true to stop another duplicate file being added
            return True

    def getFile(self, path):
        return s.query(File).order_by(File.id).filter(File.path == self.preparePath(path)).one()

    def listKnownFiles(self):
        with open('listing.txt') as f:
            content = f.readlines()

        return content

    def removexattr(self, att1, att2):
        return 0

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()

        if path == '/':
            attr = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
        elif path in self.listOfFileNames():
            size = len('%s\n' % uid)
            attr = dict(st_mode=(S_IFREG | 0o444), st_size=size)
        elif path == '/gid':
            size = len('%s\n' % gid)
            attr = dict(st_mode=(S_IFREG | 0o444), st_size=size)
        elif path == '/pid':
            size = len('%s\n' % pid)
            attr = dict(st_mode=(S_IFREG | 0o444), st_size=size)
        else:
            size = len('%s\n' % pid)
            attr = dict(st_mode=(S_IFREG | 0o755), st_size=size)

        attr['st_ctime'] = attr['st_mtime'] = time()
        return attr

    def read(self, path, size, offset, fh):

        offsetFromFirstBlock=offset%512
        firstBlock=int(math.ceil(offset/512))
        numberOfBlocks=int(math.ceil((offsetFromFirstBlock+size)/512))

        for i in range(firstBlock, firstBlock+numberOfBlocks):
            if(i == firstBlock):
                bytesToRead=512-offsetFromFirstBlock
                offsetForBlock=offsetFromFirstBlock
            elif(i == firstBlock+numberOfBlocks):
                bytesToRead=512-(512-offsetFromFirstBlock)
                offsetForBlock=0
            else:
                bytesToRead=512
                offsetForBlock=0

            print("Would read {} bytes from block #{} at offset {}".format(bytesToRead, i, offsetForBlock))

        uid, gid, pid = fuse_get_context()
        encoded = lambda x: ('%s\n' % x).encode('utf-8')

        if path == path:
            return encoded(uid)
        elif path == '/gid':
            return encoded(gid)
        elif path == '/pid':
            return encoded(pid)

        raise RuntimeError('unexpected path: %r' % path)

    def readdir(self, path, fh):
#        realFileList = []
#
#        for fileObject in File.list():
#            print("reading file with name:", fileObject.name)
#            realFileList.append(fileObject.name)
#
        print("realFileList:", self.listOfFileNames())

        return ['.', '..'] + self.listOfFileNames()

    def mkdir(self, path, mode):
        #conn = sqlite3.connect('example.db')
        #c = conn.cursor()
        #c.execute('INSERT INTO file (name) VALUES (?)', path[0])
        #conn.commit()
        #c.close()
        print("do nothing")

    def create(self, path, mode):
        if not self.fileExists(path):
            self.addFile(path[1:])
            return self.getFile(path[1:]).id

        return os.EEXIST

    def open(self, path, flags):
        return self.getFile(path).id

    def write(self, path, data, offset, fh):

        blockPath = 'data/files/{}/blocks/'.format(md5.new().update(path).hexdigest())

        if not os.path.exists(blockPath):
            os.mkdirs(blockPath)

        return 1

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)

    engine = create_engine('sqlite:///', echo=True)
    session = sessionmaker()
    session.configure(bind=engine)
    Base.metadata.create_all(engine)

    john = File(name='john')
    s = session()
    s.add(john)
    s.commit()
    it = s.query(File).filter(File.name == 'john').one()
    print("File Name: ", it.name)

    fuse = FUSE(Context(), argv[1], ro=False, foreground=True, nothreads=True)
