import dropbox
import dropbox.files

import drivers.driver


class DropboxDriver(drivers.driver.Driver):
    def init(self):
        global dbx
        dbx = dropbox.Dropbox("wB4qXMwTafAAAAAAAAAAyxiCpOxsYLuvCyYMRZTT_RZDGXHdiqiqq1CJZ2XegDsA")
        dbx.users_get_current_account()

    def delete_directory(self, directory_name):
        dbx.files_delete(directory_name)

    def write_file(self, fileName, fileContents):
        try:
            dbx.files_upload(fileContents, fileName, dropbox.files.WriteMode.overwrite, mute=True)
        except:
            return False

    def readFile(self, fileName):
        try:
            metadata, result = dbx.files_download(fileName)
            return result.content
        except:
            return False

    def make_directory(self, directoryName):
        try:
            dbx.files_create_folder(directoryName)
            return True
        except:
            return False

    def list_files(self, directory_name):
        try:
            return dbx.files_list_folder(directory_name)
        except:
            return False