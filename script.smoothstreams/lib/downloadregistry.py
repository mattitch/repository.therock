# -*- coding: utf-8 -*-
import os, json
import util
import URLDownloader

class DownloadRegistry(object):
    _registryFile = os.path.join(util.PROFILE,'dlregistry.json')
    _version = 1

    def __init__(self):
        self.registry = []
        self.readRegistry()

    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        try:
            self.saveRegistry()
        except:
            util.ERROR()

    def __len__(self):
        return self.size()

    def __getitem__(self,idx):
        return self.registry[idx]

    def __setitem__(self,idx,value):
        self.registry[idx] = value

    def cleanScheduled(self):
        clean = []
        for i,item in self.enumerate():
            if item._udType == 'SCHEDULE_ITEM':
                if item.exists():
                    del item['start']
                    self[i] = URLDownloader.Download(item)
                    continue
                if item.isOld(): clean.append(item)

        for item in clean:
            self.remove(item)

    def checkData(self,data): #Fix for initial testing format
        if not isinstance(data,list): return data
        ct=0
        items = []
        for d in data:
            i = URLDownloader.Download(d)
            i['ID'] = ct
            items.append(i.serialize())
            ct+=1

        data = {'version':self._version,'items':items}

        with open(self._registryFile,'w') as f:
            json.dump(data,f)
        return data

    def readRegistry(self):
        if not os.path.exists(self._registryFile):
            self.registry = []
            return

        try:
            with open(self._registryFile,'r') as f:
                data = json.load(f)
        except:
            util.ERROR()
            self.registry = []
            return

        data = self.checkData(data)

        self.registry = []

        for i in data['items']:
            self.registry.append(URLDownloader.Download.deSerialize(i))

    def saveRegistry(self):
        items = []
        for i in self.registry:
            items.append(i.serialize())

        with open(self._registryFile,'w') as f:
            json.dump({'version':self._version,'items':items},f)

    def removeMissing(self):
        old = self.registry
        self.registry = []
        for i in old:
            if i.exists(): self.registry.append(i)

    def deleteAll(self):
        for i in self.registry:
            i.clean()
        self.registry = []

    def add(self,download):
        self.registry.append(download)
        self.registry.sort(key=lambda x: x.ID,reverse=True)

    def updateItem(self,download):
        for i,item in self.enumerate():
            if item.ID == download.ID:
                self[i] = download
                return

    def remove(self,item):
        for i, it in self.enumerate():
            if it.ID == item.ID:
                self.registry.pop(i)
                return

    def delete(self,item):
        for i in self.range():
            if self[i].ID == item.ID:
                item = self.registry.pop(i)
                item.clean()
                return

    def size(self):
        return len(self.registry)

    def enumerate(self):
        return enumerate(self.registry)

    def range(self):
        return range(self.size())

    def empty(self):
        return self.size() == 0
