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
    md5_instance = md5.new()
    md5_instance.update(path)

    return '/files/{}/blocks/'.format(md5_instance.hexdigest())

def list_blocks(path, driver):
    block_root = get_block_root(path)

    blocks = os.listdir(block_root)
    return len(blocks)

def get_size_of_file(path, driver):
    total_size = 0
    block_root = get_block_root(path)

    for block in driver.list_files(block_root):
        total_size += driver.getSize(block_root+block)

    return total_size