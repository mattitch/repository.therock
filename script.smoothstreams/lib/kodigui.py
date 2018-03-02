# -*- coding: utf-8 -*-
import xbmc, xbmcgui

class ManagedListItem(object):
    def __init__(self,label='', label2='', iconImage='', thumbnailImage='', path='',data_source=None):
        self._listItem = xbmcgui.ListItem(label,label2,iconImage,thumbnailImage,path)
        self.dataSource = data_source
        self.properties = {}
        self.label = label
        self.label2 = label2
        self.iconImage = iconImage
        self.thumbnailImage = thumbnailImage
        self.path = path
        self._ID = None
        self._manager = None

    @property
    def listItem(self):
        if not self._listItem:
            if not self._manager: return None
            self._listItem = self._manager.getListItemFromManagedItem(self)
        return self._listItem

    def _takeListItem(self,manager,lid):
        self._manager = manager
        self._ID = lid
        self._listItem.setProperty('__ID__',lid)
        li = self._listItem
        self._listItem = None
        return li

    def _updateListItem(self):
        self.listItem.setProperty('__ID__',self._ID)
        self.listItem.setLabel(self.label)
        self.listItem.setLabel2(self.label2)
        self.listItem.setIconImage(self.iconImage)
        self.listItem.setThumbnailImage(self.thumbnailImage)
        self.listItem.setPath(self.path)
        for k,v in self.properties.items():
            self.listItem.setProperty(k,v)

    def pos(self):
        if not self._manager: return None
        return self._manager.getManagedItemPosition(self)

    def addContextMenuItems(self,items,replaceItems=False):
        self.listItem.addContextMenuItems(items,replaceItems)

    def addStreamInfo(self, stype, values):
        self.listItem.addStreamInfo(stype,values)

    def getLabel(self):
        return self.label

    def getLabel2(self):
        return self.label2

    def getProperty(self,key):
        return self.properties.get(key,'')

    def getdescription(self):
        return self.listItem.getdescription()

    def getduration(self):
        return self.listItem.getduration()

    def getfilename(self):
        return self.listItem.getfilename()

    def isSelected(self):
        return self.listItem.isSelected()

    def select(self,selected):
        return self.listItem.select(selected)

    def setArt(self,values):
        return self.listItem.setArt(values)

    def setIconImage(self,icon):
        self.iconImage = icon
        return self.listItem.setIconImage(icon)

    def setInfo(self,itype,infoLabels):
        return self.listItem.setInfo(itype, infoLabels)

    def setLabel(self,label):
        self.label = label
        return self.listItem.setLabel(label)

    def setLabel2(self,label):
        self.label2 = label
        return self.listItem.setLabel2(label)

    def setMimeType(self,mimetype):
        return self.listItem.setMimeType(mimetype)

    def setPath(self,path):
        self.path = path
        return self.listItem.setPath(path)

    def setProperty(self,key,value):
        self.properties[key] = value
        return self.listItem.setProperty(key, value)

    def setSubtitles(self,subtitles):
        return self.listItem.setSubtitles(subtitles) #List of strings - HELIX

    def setThumbnailImage(self,thumb):
        self.thumbnailImage = thumb
        return self.listItem.setThumbnailImage(thumb)


class ManagedControlList(object):
    def __init__(self,window,control_id,max_view_index):
        self.controlID = control_id
        self.window = window
        self.control = window.getControl(control_id)
        self.items = []
        self.sort = None
        self._idCounter = 0
        self._maxViewIndex = max_view_index

    def __getattr__(self,name):
        return getattr(self.control,name)

    def __getitem__(self,idx):
        return self.getListItem(idx)

    def _updateItems(self,bottom,top):
        for idx in range(bottom,top):
            li = self.control.getListItem(idx)
            mli = self.items[idx]
            mli._listItem = li
            mli._updateListItem()

    def _nextID(self):
        self._idCounter+=1
        return str(self._idCounter)

    def setSort(self,sort):
        self._sortKey = sort

    def addItem(self,managed_item):
        self.items.append(managed_item)
        self.control.addItem(managed_item._takeListItem(self,self._nextID()))


    def addItems(self,managed_items):
        self.items += managed_items
        self.control.addItems([i._takeListItem(self,self._nextID()) for i in managed_items])

    def replaceItems(self,managed_items):
        oldSize = self.size()
        self.items = managed_items
        size = self.size()
        if size > oldSize:
            for i in range(0,size - oldSize):
                self.control.addItem(xbmcgui.ListItem())
        elif size < oldSize:
            removeIDX = size - 1
            lowest = removeIDX - (oldSize - size)

            while removeIDX >= lowest:
                self.control.removeItem(removeIDX)
                removeIDX-=1

        self._updateItems(0,self.size())

    def getListItem(self,pos):
        li = self.control.getListItem(pos)
        mli = self.items[pos]
        mli._listItem = li
        return mli

    def getSelectedItem(self):
        pos = self.control.getSelectedPosition()
        return self.getListItem(pos)

    def removeItem(self,index):
        self.items.pop(index)
        self.control.removeItem(index)

    def insertItem(self,index,managed_item):
        self.items.insert(index,managed_item)
        self.control.addItem(managed_item._takeListItem(self,self._nextID()))
        self._updateItems(index,self.size())

    def moveItem(self,mli,dest_idx):
        source_idx = mli.pos()
        if source_idx < dest_idx:
            rstart = source_idx
            rend = dest_idx+1
            dest_idx-=1
        else:
            rstart = dest_idx
            rend = source_idx+1
        mli = self.items.pop(source_idx)
        self.items.insert(dest_idx,mli)

        self._updateItems(rstart,rend)

    def shiftView(self,shift,hold_selected=False):
        if not self._maxViewIndex: return
        selected = self.getSelectedItem()
        selectedPos = selected.pos()
        viewPos = self.getViewPosition()

        if shift > 0:
            pushPos = selectedPos + (self._maxViewIndex - viewPos) + shift
            if pushPos >= self.size(): pushPos = self.size() - 1
            self.selectItem(pushPos)
            newViewPos = self._maxViewIndex
        elif shift < 0:
            pushPos = (selectedPos - viewPos) + shift
            if pushPos < 0: pushPos = 0
            self.selectItem(pushPos)
            newViewPos = 0

        if hold_selected:
            self.selectItem(selected.pos())
        else:
            diff = newViewPos - viewPos
            fix = pushPos - diff
            #print '{0} {1} {2}'.format(newViewPos, viewPos, fix)
            if self.positionIsValid(fix):
                self.selectItem(fix)


    def reset(self):
        self.items = []
        self.control.reset()

    def size(self):
        return len(self.items)

    def getViewPosition(self):
        try:
            return int(xbmc.getInfoLabel('Container({0}).Position'.format(self.controlID)))
        except:
            return 0

    def getViewRange(self):
        viewPosition = self.getViewPosition()
        selected = self.getSelectedPosition()
        return range(max(selected - viewPosition,0),min(selected + (self._maxViewIndex - viewPosition) + 1,self.size() - 1))

    def positionIsValid(self,pos):
        return pos > 0 and pos < self.size()

    def sort(self,sort=None):
        sort = sort or self._sortKey

        self.items.sort(key=self._sortKey)

        self._updateItems(0,self.size)

    def getManagedItemPosition(self,mli):
        return self.items.index(mli)

    def getListItemFromManagedItem(self,mli):
        pos = self.items.index(mli)
        return self.control.getListItem(pos)
