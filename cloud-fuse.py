#
# @file  cloud-fues.py
#
# @brief Main entrypoint into the cloud-fuse software.
#

from __future__ import print_function, absolute_import, division

import logging
import math
import sqlite3
import os

from errno      import ENOENT
from stat       import S_IFDIR, S_IFREG
from sys        import argv, exit
from time       import time

from sqlalchemy                 import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.orm             import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn, fuse_get_context

# Base from sqlalchemy orm so that we can derive classes from it.
Base = declarative_base()

# Holds information about specific files. Soon to be replaced with a more inode-like system.
class File(Base):
    __tablename__ = 'files'
    id            = Column(Integer, primary_key=True)
    path          = Column(String)
    name          = Column(String)
    permissions   = Column(Integer)
    size          = Column(Integer)

# Main class passed to fuse - this is where we define the functions that are called by fuse.
class Context(LoggingMixIn, Operations):

    # Remove the first character ('/') from path.
    #
    # @FIXME: Should check that the first character is actually / so that if it is called twice on the same string it does not take two characters off the front.
    def preparePath(self, path):
        return path[1:]

    def listOfFileNames(self):
        knownFiles = []

        for file in session.query(File).order_by(File.id):
            knownFiles.append(file.name)

        return knownFiles

    def addFile(self, path):
        newFile = File(path=path, name=path, permissions=777, size=0)
        session.add(newFile)
        session.commit()
        return newFile.id

    def fileExists(self, path):
        print("Checking if {} exists".format(self.preparePath(path)))
        fileCountQuery = session.query(File).filter_by(path=self.preparePath(path))
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
        return session.query(File).order_by(File.id).filter(File.path == self.preparePath(path)).one()

    def removexattr(self, att1, att2):
        return 0

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()

        if self.preparePath(path) in self.listOfFileNames():
            attr = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
        elif path == '/':
            attr = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
        else:
            raise FuseOSError(ENOENT)

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
        return ['.', '..'] + self.listOfFileNames()

    def mkdir(self, path, mode):
        print("do nothing")

    def create(self, path, mode):

        print("Create called")

        if not self.fileExists(path):
            self.addFile(path[1:])
            return self.getFile(path[1:]).id

        return os.EEXIST

    def open(self, path, flags):
        print("open called with flags: {}".format(flags))
        print("CREATE FLAG: {}".format(os.O_CREAT))
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
    sessionMaker = sessionmaker()
    sessionMaker.configure(bind=engine)
    Base.metadata.create_all(engine)
    session = sessionMaker()

    fuse = FUSE(Context(), argv[1], ro=False, foreground=True, nothreads=True)
