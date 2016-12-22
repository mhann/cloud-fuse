from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import drivers.driver


class GoogleDriveDriver(drivers.driver.Driver):
    scopes = 'https://www.googleapis.com/auth/drive.metadata.readonly'
    client_secret_file = 'client_secrets.json'
    application_name = 'Drive API Python Quickstart'
    gauth = False

    def init(self):
        global gauth
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()

    def write_file(self, fileName, content):
        drive = GoogleDrive(gauth)

        file1 = drive.CreateFile({'title': fileName})  # Create GoogleDriveFile instance with title 'Hello.txt'.
        file1.SetContentString(content)  # Set content of the file from given string.
        file1.Upload()

    def delete_file(self, file_name):
        drive = GoogleDrive(gauth)

