import md5
import os

def stringToChunks(string, chunkSize):
    while string:
        yield string[:chunkSize]
        string = string[chunkSize:]

def getBlockRoot(path):
    md5Instance = md5.new()
    md5Instance.update(path)

    return 'data/files/{}/blocks/'.format(md5Instance.hexdigest())

def listBlocks(path):
    blockRoot = getBlockRoot(path)

    blocks = os.listdir(blockRoot)
    return len(blocks)

def getSizeOfFile(path):
    totalSize = 0
    blockRoot = getBlockRoot(path)

    for block in os.listdir(blockRoot):
        totalSize += os.path.getsize(blockRoot+block)

    return totalSize
