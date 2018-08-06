#  GUI libraries
from tkinter import messagebox
from tkinter import *
from tkinter.ttk import *

#  url sifting
import urllib.request
from bs4 import BeautifulSoup as BS

#  threading
import queue
import threading

#  backing up library
import os

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

from filecreation import makeJSON
import json
import base64

class App(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.linkarr, self.namearr = self.GetLinks()
        self.CreateUI()
        
        self.grid(sticky = (N,S,W,E))
        parent.grid_rowconfigure(0, weight = 1)
        parent.grid_columnconfigure(0, weight = 1)

    def GetLinks(self):
        linkarr = []
        namearr = []
        
        # find all links
        serverdata = json.load(open('serverdata.json','r'))
        
        for magazine in serverdata['productDetails']:
            namearr.append(magazine['created'])
            linkarr.append(str(base64.b64decode(magazine['pdfFile']))[2:-1])

        return linkarr, namearr
        
    def CreateUI(self):
        self.tv = Treeview(self)

        self.tv.pack()

        for i in range(0, len(self.namearr)-1):
            self.tv.insert('', 'end', text=self.namearr[i])

        self.tv.bind("<Double-1>", self.OnDoubleClick)
        
        self.tv.grid(sticky = (N,S,W,E))
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

    def OnDoubleClick(self, event):
        item = self.tv.selection()[0]
        self.queue = queue.Queue()
        filename = self.tv.item(item,"text")
        link = self.linkarr[self.namearr.index(filename)]
        print(link)
        Downloader(self.queue, link, filename).start()

class Downloader(threading.Thread):
    def __init__(self, queue, link, filename):
        threading.Thread.__init__(self)
        self.queue = queue
        self.link = link
        self.filename = filename
        
    def backup(self):
        #  connects to google drive
        SCOPES = 'https://www.googleapis.com/auth/drive'
        store = file.Storage('storage.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
            creds = tools.run_flow(flow, store)
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

        FILES = (
            (self.filename, 'application/pdf'),
        )

        for filename, mimeType in FILES:
            metadata = {'name': filename}
            if mimeType:
                metadata['mimeType'] = mimeType
            res = DRIVE.files().create(body=metadata, media_body=filename).execute()
            if res:
                self.queue.put("Task finished")

        messagebox.showwarning('Finished', 'Finished downloading ' + self.link)
        
    def run(self):
        messagebox.showwarning("Confirm", self.link + " will start downloading")
        
        # adding a header
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Linux; Android 6.0.1; SM-G532G Build/MMB29T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.83 Mobile Safari/537.36')]
        urllib.request.install_opener(opener)
        
        urllib.request.urlretrieve(self.link, self.filename)

        messagebox.showwarning("Finished", self.link + " has been downloaded\nPress okay to upload")

        self.backup()
        
def main():
    makeJSON()
    # GUI
    root = Tk()
    App(root)
    root.mainloop()

if __name__ == '__main__':
    main()
