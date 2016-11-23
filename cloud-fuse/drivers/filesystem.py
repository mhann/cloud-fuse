import drivers.driver
import os

class FileSystem(drivers.driver.Driver):
    def deleteDirectory(self, directoryName):
        os.rmdir("data" + directoryName)
        return True

    def writeFile(self, fileName, fileContents):
        file = open("data" + fileName, 'r+')
        file.write(fileContents)
        return True

    def readFile(self, fileName):
        file = open("data" + fileName, 'r')
        return file.read()

    def makeDirectory(self, directoryName):
        print("Making directories")
        if not os.path.exists("data" + directoryName):
            os.makedirs("data" + directoryName)
        return True

    def listFiles(self, directoryName):
        return os.listdir("data" + directoryName)

    def getSize(self, fileName):
        return os.path.getsize("data" + fileName)
