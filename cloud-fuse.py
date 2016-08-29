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
import md5

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

    def getBlockRoot(self, path):
        md5Instance = md5.new()
        md5Instance.update(path)

        return 'data/files/{}/blocks/'.format(md5Instance.hexdigest())

    def listBlocks(self, path):
        blockRoot = self.getBlockRoot(path)

        blocks = os.listdir(blockRoot)
        return len(blocks)

    def getSizeOfFile(self, path):
        totalSize = 0
        blockRoot = self.getBlockRoot(path)

        for block in os.listdir(blockRoot):
            totalSize += os.path.getsize(blockRoot+block)

        return totalSize

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
            attr = dict(st_mode=(S_IFREG | 0o755), st_nlink=2, st_size=self.getSizeOfFile(path))
        elif path == '/':
            attr = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
        else:
            raise FuseOSError(ENOENT)

        attr['st_ctime'] = attr['st_mtime'] = time()
        return attr

    def truncate(self, path, length, fh=None):
        blockPath = self.getBlockRoot(path)

        print("Deleting all files in: {}".format(blockPath))

        for f in os.listdir(blockPath):
            os.remove(blockPath+f)

    def read(self, path, size, offset, fh):

        if not self.preparePath(path) in self.listOfFileNames():
            raise RuntimeError('unexpected path: %r' % path)

        offsetFromFirstBlock=offset%512
        firstBlock=int(math.ceil(offset/512))
        numberOfBlocks=int(math.ceil((offsetFromFirstBlock+size)/512))

        if numberOfBlocks > self.listBlocks(path) :
            numberOfBlocks = self.listBlocks(path)

        if offset == 0:
            firstBlock = 1

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

            blockPath = self.getBlockRoot(path)

            print("Reading {} bytes from {} at offset {}".format(bytesToRead, self.getBlockRoot(path)+str(i), offsetForBlock))

            f = open(self.getBlockRoot(path)+str(i), 'r')
            f.seek(offsetForBlock)
            blockContentsFromOffset = f.read(bytesToRead)

            print("Would return: {}".format(blockContentsFromOffset))

            return blockContentsFromOffset

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
        # NOT a real fd - but will do for simple testing
        return self.getFile(path).id

    def write(self, path, data, offset, fh):

        blockPath = self.getBlockRoot(path)

        if not os.path.exists(blockPath):
            os.makedirs(blockPath)

        blockSize = 512
        firstBlock = int(math.ceil(offset/512))
        firstBlockOffset = int(offset%512)

        if offset == 0:
            firstBlock = 1

        print("Writing data {} of size {} to block {} at offset {}".format(data, len(data), firstBlock, firstBlockOffset))

        f = os.open(blockPath+str(firstBlock), os.O_CREAT | os.O_WRONLY)

        with os.fdopen(f, 'w') as file_obj:
            file_obj.seek(firstBlockOffset)
            file_obj.write(data)

        return len(data)

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
