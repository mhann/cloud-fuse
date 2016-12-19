import drivers.driver
import os

class FileSystem(drivers.driver.Driver):
    def delete_directory(self, directoryName):
        os.rmdir("data12" + directoryName)
        return True

    def write_file(self, fileName, fileContents):
        file = open("data12" + fileName, 'w+')
        file.write(fileContents)
        return True

    def readFile(self, fileName):
        try:
            file = open("data12" + fileName, 'r')
            return file.read()
        except:
            return False

    def make_directory(self, directoryName):
        print("Making directories")
        if not os.path.exists("data12" + directoryName):
            os.makedirs("data12" + directoryName)
        return True

    def list_files(self, directoryName):
        return os.listdir("data12" + directoryName)

    def getSize(self, fileName):
        return os.path.getsize("data12" + fileName)
