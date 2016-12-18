#
# @file  cloud-fuse.py
#
# @brief Main entrypoint into the cloud-fuse software.
#

from __future__ import print_function, absolute_import, division

import logging
import math
import sqlite3
import os
import md5
import importlib

import helpers.blocks
import helpers.filesystem
import helpers.database

from errno      import ENOENT
from stat       import S_IFDIR, S_IFREG
from sys        import argv, exit
from time       import time

from sqlalchemy                 import Column, String, Integer, ForeignKey, create_engine, Boolean, Date
from sqlalchemy.orm             import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn, fuse_get_context

# Base from sqlalchemy orm so that we can derive classes from it.
Base = declarative_base()

class Node(Base):
    __tablename__ = 'node'
    id            = Column(Integer, primary_key=True)
    parent_id     = Column(Integer, ForeignKey('node.id'))
    children      = relationship("Node")
    name          = Column(String)
    size          = Column(Integer)
    permissions   = Column(Integer)
    directory     = Column(Boolean)
    create_time   = Column(Date)
    update_time   = Column(Date)
    read_time     = Column(Date)
    parent        = relationship("Node", remote_side=[id])

    @staticmethod
    def getTopLevelNodes():
        return session.query(Node).order_by(Node.id).filter(Node.parent == None)

    @staticmethod
    def getChildrenOfNode(parent):
        childNodes = []

        for row in session.query(Node).order_by(Node.id).filter(Node.parent == parent).all():
            print(row.name);
            childNodes.append(row)

        return childNodes

    @staticmethod
    def getNodeFromAbsPath(path):
        splitPath = path.split("/")

        lastParentNode = None

        for pathSection in splitPath:
            print("Working on path segment: {}".format(pathSection))
            if pathSection == "":
                continue

            try:
                print("Looking for node with parentid {} and name {}".format(lastParentNode, pathSection))
                lastParentNode = session.query(Node).order_by(Node.id).filter(Node.parent == lastParentNode, Node.name == pathSection).one()
                print("Found match for: {}, which was: {}".format(pathSection, Node.id))
            except:
                # No file existed in this path
                return False

        return lastParentNode

class Block(Base):
    __tablename__ = 'block'
    id            = Column(Integer, primary_key=True)
    hash          = Column(String)
    size          = Column(Integer)
    Node          = relationship("Node", remote_side=[id])

# Holds information about specific files. Soon to be replaced with a more inode-like system.
class File(Base):
    __tablename__ = 'file'
    id            = Column(Integer, primary_key=True)
    path          = Column(String)
    name          = Column(String)
    permissions   = Column(Integer)
    size          = Column(Integer)

    @staticmethod
    def get(path):
        return session.query(File).order_by(File.id).filter(File.path == helpers.filesystem.preparePath(path)).one()

    @staticmethod
    def listOfFileNames():
        knownFiles = []

        for file in session.query(File).order_by(File.id):
            knownFiles.append(file.name)

        return knownFiles

    @staticmethod
    def exists(path):
        print("Checking if {} exists".format(helpers.filesystem.preparePath(path)))
        fileCountQuery = session.query(File).filter_by(path=helpers.filesystem.preparePath(path))
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

# Main class passed to fuse - this is where we define the functions that are called by fuse.
class Context(LoggingMixIn, Operations):
    def removexattr(self, att1, att2):
        return 0

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()

        node = Node.getNodeFromAbsPath(path)
        if node:
            if(node.directory):
                attr = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2, st_size=0)
            else:
                attr = dict(st_mode=(S_IFREG | 0o755), st_nlink=2, st_size=helpers.blocks.get_size_of_file(path, filesystem))
        elif path == '/':
            attr = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
        else:
            raise FuseOSError(ENOENT)

        attr['st_ctime'] = attr['st_mtime'] = time()
        return attr

    def truncate(self, path, length, fh=None):
        blockPath = helpers.blocks.get_block_root(path)

        print("Deleting all files in: {}".format(blockPath))

        for f in fileSystem.list_files(blockPath):
            fileSystem.delete_file(blockPath + f)

    def read(self, path, size, offset, fh):

        if not Node.getNodeFromAbsPath(path):
            raise RuntimeError('unexpected path: %r' % path)

        offsetFromFirstBlock=offset%512
        firstBlock=int(math.ceil(offset/512))
        numberOfBlocks=int(math.ceil((offsetFromFirstBlock+size)/512))

        if numberOfBlocks > helpers.blocks.list_blocks(path, filesystem):
            numberOfBlocks = helpers.blocks.list_blocks(path, filesystem)

        print("Number of blocks: {}".format(numberOfBlocks))

        if offset == 0:
            firstBlock = 1

        fileContent = ""

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

            blockPath = helpers.blocks.get_block_root(path)

            print("Reading {} bytes from {} at offset {}".format(bytesToRead, helpers.blocks.get_block_root(path) + str(i), offsetForBlock))

            f = open(helpers.blocks.get_block_root(path) + str(i), 'r')
            f.seek(offsetForBlock)
            blockContentsFromOffset = f.read(bytesToRead)

            print("Would return: {}".format(blockContentsFromOffset))

            fileContent += blockContentsFromOffset

        return fileContent

    def readdir(self, path, fh):
        return ['.', '..'] + [node.name for node in Node.getChildrenOfNode(Node.getNodeFromAbsPath(path))]

    def mkdir(self, path, mode):
        if not Node.getNodeFromAbsPath(path):
            if len(path.split('/')[:-1]) == 1:
                print("Adding to root")
                parent=Node(name=path.split('/')[1], directory=True)
                session.add(parent)
                session.commit()
                return 0

            pathRoot = path.split('/')[:-1]
            pathRoot = '/'.join(pathRoot)

            parentNode = Node.getNodeFromAbsPath(pathRoot)

            if not parentNode.directory:
                print("Trying to add node to non-directory node!")
                # I doubt EEXIST is the correct thing to be returning here.
                return os.EEXIST

            newFile = Node(name=path.split('/')[1], directory=True)
            parentNode.children.append(newFile)
            session.commit()

            blockPath = helpers.blocks.get_block_root(path)

            filesystem.make_directory(blockPath)

            return newFile.id

        return os.EEXIST

    def create(self, path, mode):
        print("Create called")

        if not Node.getNodeFromAbsPath(path):
            if len(path.split('/')[:-1]) == 1:
                print("Adding to root")
                newFile=Node(name=path.split('/')[1])
                session.add(newFile)
                session.commit()
            else:
                pathRoot = path.split('/')[:-1]
                pathRoot = '/'.join(pathRoot)

                parentNode = Node.getNodeFromAbsPath(pathRoot)

                if not parentNode.directory:
                    print("Trying to add node to non-directory node!")
                    # I doubt EEXIST is the correct thing to be returning here.
                    return os.EEXIST

                newFile = Node(name=path.split('/')[-1], directory=False)
                parentNode.children.append(newFile)
                session.commit()


            blockPath = helpers.blocks.get_block_root(path)

            print("Block path is: {}".format(blockPath))

            filesystem.make_directory(blockPath)

            return newFile.id

        return os.EEXIST

    def open(self, path, flags):
        # NOT a real fd - but will do for simple testing
        return Node.getNodeFromAbsPath(path).id

    def write(self, path, data, offset, fh):

        blockPath = helpers.blocks.get_block_root(path)

        blockSize = 512
        firstBlock = int(math.ceil(offset/blockSize))
        firstBlockOffset = int(offset%blockSize)
        numberOfBlocks=int(math.ceil((firstBlockOffset+blockSize)/blockSize))

        if offset == 0:
            firstBlock = 1

        currentBlock = firstBlock

        test = helpers.blocks.string_to_chunks(data, blockSize)

        print(list(test))

        for i, dataBlock in enumerate(helpers.blocks.string_to_chunks(data, blockSize)):
            if(i == 0):
                # This is the first block that we are writing to
                bytesToRead=blockSize-firstBlockOffset
                offsetForBlock=firstBlockOffset
            elif(i == numberOfBlocks):
                # This is the last block that we are writing to
                bytesToRead=blockSize-(blockSize-firstBlockOffset)
                offsetForBlock=0
            else:
                bytesToRead=blockSize
                offsetForBlock=0

            currentBlock = firstBlock+i

            print("Writing data {} of size {} to block {} at offset {}".format(dataBlock, len(dataBlock), currentBlock, offsetForBlock))

            f = os.open(blockPath+str(currentBlock), os.O_CREAT | os.O_WRONLY)

            with os.fdopen(f, 'w') as file_obj:
                file_obj.seek(firstBlockOffset)
                file_obj.write(dataBlock)

        return len(data)

if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)

    engine = create_engine('sqlite:///')
    sessionMaker = sessionmaker()
    sessionMaker.configure(bind=engine)
    Base.metadata.create_all(engine)
    session = sessionMaker()

    parent1=Node(name='test', directory=True)
    parent1.children.append(Node(name='test2', directory=True))

    session.add(parent1)
    session.commit()

    print("Listing all nodes")
    for node in session.query(Node):
        print("Node: {}".format(node.name))

    Node.getNodeFromAbsPath('/test/test2').children.append(Node(name='test21'))

    session.commit()

    print(Node.getNodeFromAbsPath('/test/test2/test21').name)

    print("Testing drivers")
    driverImport = importlib.import_module("drivers.filesystem", __name__)

    global filesystem
    filesystem = driverImport.drivers.filesystem.FileSystem()

    fuse = FUSE(Context(), argv[1], ro=False, foreground=True, nothreads=True)