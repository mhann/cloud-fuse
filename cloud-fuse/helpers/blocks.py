import md5
import os


#
# Take a string, and split into chunks the size of chunkSize.
# The final string will be string%chunkSize .
def string_to_chunks(string, chunkSize):
    while string:
        yield string[:chunkSize]
        string = string[chunkSize:]

def get_block_root(path):
    md5Instance = md5.new()
    md5Instance.update(path)

    return '/files/{}/blocks/'.format(md5Instance.hexdigest())

def list_blocks(path, driver):
    blockRoot = get_block_root(path)

    blocks = os.listdir(blockRoot)
    return len(blocks)

def get_size_of_file(path, driver):
    totalSize = 0
    blockRoot = get_block_root(path)

    for block in driver.list_files(blockRoot):
        totalSize += driver.getSize(blockRoot+block)

    return totalSize