import drivers.driver
import os

class FileSystem(drivers.driver.Driver):
    def delete_directory(self, directoryName):
        os.rmdir("data" + directoryName)
        return True

    def write_file(self, fileName, fileContents):
        file = open("data" + fileName, 'r+')
        file.write(fileContents)
        return True

    def readFile(self, fileName):
        file = open("data" + fileName, 'r')
        return file.read()

    def make_directory(self, directoryName):
        print("Making directories")
        if not os.path.exists("data" + directoryName):
            os.makedirs("data" + directoryName)
        return True

    def list_files(self, directoryName):
        return os.listdir("data" + directoryName)

    def getSize(self, fileName):
        return os.path.getsize("data" + fileName)
