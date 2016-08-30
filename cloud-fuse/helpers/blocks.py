def stringToChunks(self, string, chunkSize):
    while string:
        yield string[:chunkSize]
        string = string[chunkSize:]
