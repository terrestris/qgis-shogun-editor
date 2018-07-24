# -*- coding: utf-8 -*-
'''
(c) 2018 terrestris GmbH & Co. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'July 2018'

import sys

if sys.version_info[0] >= 3:
    from qgis.PyQt.QtCore import QRect, Qt
    # we are faking the old way of QtGui, not the best style, but makes it easier
    # for switching betweeng version 2 and 3
    from qgis.PyQt import QtWidgets as QtGui
    from qgis.PyQt.QtGui import QFont
else:
    from PyQt4.QtCore import QRect, Qt
    from PyQt4 import QtGui
    from PyQt4.QtGui import QFont

from qgis.gui import QgsExtentGroupBox

class LayerListItem(QtGui.QListWidgetItem):
    def __init__(self, text, layerId):
        super(LayerListItem, self).__init__(text)
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsDragEnabled |
        Qt.ItemIsSelectable)
        self.layerId = layerId

class LayerListWidget(QtGui.QListWidget):
    def __init__(self, parent):
        super(LayerListWidget, self).__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)

    def populateList(self, layers):
        for layer in layers:
            item = LayerListItem(text = layer[1], layerId = layer[0])
            self.addItem(item)

    def dragEnterEvent(self, e):
        item = self.itemAt(e.pos())
        if item is not None:
            # we need to pass the name of the layer and it's id to the mimeData
            # for drag and drop. For reasons of simplicity we just add the
            # layerId and name to one string which we pass and decode it later
            # we use '&;*&' so this code must not appear in layer names
            mimeText = item.text() + '&;*&' + str(item.layerId)
            e.mimeData().setText(mimeText)


class LayerTreeItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent):
        super(LayerTreeItem, self).__init__(parent)
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable |
        Qt.ItemIsDragEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable |
        Qt.ItemIsDropEnabled)
        self.savedAttributes = {}
        self.newAttributes = {}
        self.layerId = None
        self.id = None


    def setSavedAttributes(self, savedAttributes):
        self.savedAttributes = savedAttributes
        self.setText(0, self.savedAttributes['text'])
        self.role = self.savedAttributes['@class']
        self.id = self.savedAttributes['id']
        if self.savedAttributes['root']:
            return
        if self.savedAttributes['checked'] == True :
            self.setCheckState(0,Qt.Checked)
        else:
            self.setCheckState(0,Qt.Unchecked)


    def updateNewAttributes(self):
        self.newAttributes['text'] = self.text(0)
        self.newAttributes['root'] = False
        self.newAttributes['@class'] = self.role

        if self.checkState(0) == Qt.Checked:
            self.newAttributes['checked'] = True
        else:
            self.newAttributes['checked'] = False

        if self.parent() is None:
            self.newAttributes['parentId'] = self.treeWidget().rootId
            self.newAttributes['index'] = self.treeWidget().indexOfTopLevelItem(self)
        else:
            self.newAttributes['parentId'] = self.parent().id
            self.newAttributes['index'] = self.parent().indexOfChild(self)

        if self.role == 'de.terrestris.appshogun.model.tree.LayerTreeLeaf':
            self.newAttributes['expandable'] = False
            self.newAttributes['expanded'] = False
            self.newAttributes['leaf'] = True
        else:
            self.newAttributes['expandable'] = True
            self.newAttributes['expanded'] = True
            self.newAttributes['leaf'] = False

        if self.layerId is not None:
            self.newAttributes['layer'] = self.layerId
        #self.newAttributes['expanded'] = self.isExpanded()


    def getItemChange(self):
        if len(self.savedAttributes) == 0:
            return self.newAttributes
        else:
            change = {}
            for (key, value) in self.savedAttributes.items():
                if key in self.newAttributes:
                    if value != self.newAttributes[key]:
                        change[key] = self.newAttributes[key]
            if len(change) == 0:
                return None
            else:
                change['id'] = self.id
                return change


class LayerTreeWidget(QtGui.QTreeWidget):
    SHOGUN_TREE_LEAF = 'de.terrestris.appshogun.model.tree.LayerTreeLeaf'
    SHOGUN_TREE_FOLDER = 'de.terrestris.appshogun.model.tree.LayerTreeFolder'

    def __init__(self, parentWindow):
        super(LayerTreeWidget, self).__init__(parentWindow)
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.deletedItemIds = []

    def setupNewTree(self):
        folder = self.addNewFolder(None)
        folder.setText(0, 'Background layer')


    def populateTree(self, layerTree):
        # delete all items, then populate the tree with items representing
        # the layer tree structure
        self.clear()
        self.rootId = layerTree['id']
        self.constructTreeChildrenRecursive(self.invisibleRootItem(), layerTree['children'])

        iter = QtGui.QTreeWidgetItemIterator(self)
        val = iter.value()
        while val:
            val.setExpanded(True)
            iter += 1
            val = iter.value()

    def constructTreeChildrenRecursive(self, parent, children):
        for child in children:
            item = LayerTreeItem(parent)
            attrs = {key : value for (key, value) in child.items() if key != 'children'}
            item.setSavedAttributes(attrs)
            if 'children' in child.keys():
                if not child['children']:
                    return
                # 'children' is a list, to make sure the items are put into the
                # tree in the right order according to there index, we sort them
                sortedChildren = sorted(child['children'], key = lambda x : x['index'])
                self.constructTreeChildrenRecursive(item, sortedChildren)


    def getLayerTreeChanges(self):
        allChanges = {
            'newItems' : [],
            'changeItems' : [],
            'deleteItems' : []
            }
        # iterate through all items in the layertree and find new or
        # changed items
        iter = QtGui.QTreeWidgetItemIterator(self)
        treeitem = iter.value()
        while treeitem:
            treeitem.updateNewAttributes()
            change = treeitem.getItemChange()
            if change is not None:
                if not 'id' in change:
                    allChanges['newItems'].append(change)
                else:
                    allChanges['changeItems'].append(change)

            iter += 1
            treeitem = iter.value()

        if len(self.deletedItemIds) > 0:
            allChanges['deleteItems'] = [x for x in self.deletedItemIds]
            self.deletedItemIds = []

        for x in allChanges:
            if len(allChanges[x]) > 0:
                return allChanges
        return None


    def dropEvent(self, e):
        dropItem = self.itemAt(e.pos())
        mime = e.mimeData()
        if dropItem is None:
            if mime.hasText():
                newItem = LayerTreeItem(parent = self)
                layerName, layerId = mime.text().split('&;*&')
                newItem.setText(0, layerName)
                newItem.role = self.SHOGUN_TREE_LEAF
                newItem.layerId = int(layerId)
            else:
                self.changePositionInTree(self.invisibleRootItem())
        else:
            # if dropItem is a TreeLeaf it represents a layer so it cannot get a
            # child, so insert the dragged item in the parent folder
            if dropItem.role == self.SHOGUN_TREE_LEAF:
                if dropItem.parent() is not None:
                    dropItem = dropItem.parent()
                else:
                    dropItem = self.invisibleRootItem()

            # if mime has Text its coming from the layerlistwidget
            if mime.hasText():
                newItem = LayerTreeItem(parent = dropItem)
                layerName, layerId = mime.text().split('&;*&')
                newItem.setText(0, layerName)
                newItem.role = self.SHOGUN_TREE_LEAF
                newItem.layerId = int(layerId)
            else:
                self.changePositionInTree(dropItem)
        iter = QtGui.QTreeWidgetItemIterator(self)
        val = iter.value()
        while val:
            val.setSelected(False)
            iter += 1
            val = iter.value()


    def changePositionInTree(self, newParentItem):
        selectedItem = self.selectedItems()[0]
        oldParentItem = selectedItem.parent()
        # cannot insert a folder to itself
        cursor = newParentItem
        while cursor is not None:
            if selectedItem == cursor:
                return
            cursor = cursor.parent()

        if oldParentItem is None:
            self.invisibleRootItem().removeChild(selectedItem)
        else:
            oldParentItem.removeChild(selectedItem)
        newParentItem.addChild(selectedItem)
        newParentItem.setExpanded(True)
        selectedItem.setExpanded(True)


    def on_context_menu(self, point):
        item = self.itemAt(point)
        acts = []
        if item is None:
            a1 = QtGui.QAction('Add Folder (top level)', None)
            a1.triggered.connect(lambda: self.addNewFolder(None))
            acts.append(a1)
            a2 = QtGui.QAction('Delete Tree Contents completely', None)
            a2.triggered.connect(self.deleteAll)
            acts.append(a2)
        else:
            a1 = QtGui.QAction('Rename', None)
            a1.triggered.connect(lambda: self.renameItem(item))
            acts.append(a1)
            if item.role == self.SHOGUN_TREE_LEAF:
                a2 = QtGui.QAction('Delete Leaf', None)
                a2.triggered.connect(lambda: self.deleteLeaf(item))
                acts.append(a2)
            else:
                a2 = QtGui.QAction('New Folder (inside selected)', None)
                a2.triggered.connect(lambda: self.addNewFolder(item))
                acts.append(a2)
                a3 = QtGui.QAction('Delete Folder', None)
                a3.triggered.connect(lambda: self.deleteLeaf(item))
                acts.append(a3)
        menu = QtGui.QMenu()
        menu.addActions(acts)
        point = self.mapToGlobal(point)
        menu.exec_(point)


    def addNewFolder(self, item):
        if item is None:
            parent = self
        else:
            parent = item
        new = LayerTreeItem(parent)
        new.setText(0, 'New folder')
        new.role = self.SHOGUN_TREE_FOLDER
        new.setCheckState(0, Qt.Checked)
        return new

    def deleteAll(self):
        topitem = self.invisibleRootItem()
        for index in range(topitem.childCount()):
            child = topitem.child(index)
            topitem.removeChild(child)

    def renameItem(self, item):
        text, ok = QtGui.QInputDialog.getText(self,
            'Text Input Dialog', 'Enter the new name:')
        if ok:
            item.setText(0, text)

    def getSubtreeIds(self, item):
        # as there is no option in QT to iterate only a subtree, we had to write
        # a recursive iteration by ourselves to get all id's that are about to
        # be deleted
        idList = []
        if item.id is not None:
            idList.append(item.id)
        if item.childCount() > 0:
            for x in range(item.childCount()):
                idList.extend(getSubtreeIds(item.child(x)))
        return idList


    def deleteLeaf(self, item):
        self.deletedItemIds.extend(self.getSubtreeIds(item))

        parent = item.parent()
        if parent is None:
            parent = self.invisibleRootItem()
        parent.removeChild(item)



class ApplicationSettingsDialog(QtGui.QDialog):
    def  __init__(self):
        QtGui.QDialog.__init__(self)
        self.tabs = []                 #All child-tabWidgets
        self.tabedits = []              #All QLineEdits per tabWidget in a list
        self.tabboxes = []              #All QCheckBoxes per tabWidget in a list
        self.moreObjects = []
        self.setupUi()

    def setupUi(self):
        self.resize(550, 550)
        self.setWindowTitle('Settings')

        #create tabWidget that holds the tabs
        self.tabWidget = QtGui.QTabWidget(self)
        self.tabWidget.setGeometry(QRect(10, 20, 500, 480))
        self.tabWidget.setObjectName('tabWidget')
        tab0labels=[['Name',(50, 50, 56, 17)], ['Description', (50,100,70,25)], ['Language', (50, 150, 56, 17)]]
        tab1labels = [['Which tools/ buttons shall be activated in the application:', (50, 25, 56, 17)]]
        tab2labels = [['Center:', (50, 50, 70, 17)], ['X:', (160, 53, 10, 10)], ['Y:', (320, 53, 10, 10)], ['Zoom:', (50, 100, 70, 17)],
                        ['Extent:', (50, 363, 70, 17)], ['MinX:', (132, 367, 40, 17)], ['MinY:', (222, 327, 40, 17)], ['MaxX:', (306, 367, 40, 17)],
                        ['MaxY:', (222, 407, 40, 17)]]
        tab3labels = [['All Layers', (90, 40, 80, 30)], ['Layer Tree', (325, 40, 80, 30)]]
        tab4labels = [['Users', (100, 10, 50, 20)], ['Groups', (320, 10, 50, 20)]]
        tabwidgets = [['General', tab0labels], ['Tools', tab1labels], ['Homeview', tab2labels], ['Layer', tab3labels], ['Permissions', tab4labels]]

        #first set the labes for all tabwwidgets in a loop:
        for tab in tabwidgets:
            t = QtGui.QWidget()
            t.setObjectName(tab[0])
            self.tabs.append(t)
            self.tabWidget.addTab(t, tab[0])

            for label in tab[1]:
                l = QtGui.QLabel(t)
                l.setText(label[0])
                l.setGeometry(QRect(label[1][0],label[1][1],label[1][2],label[1][3]))
                if (tab[0] == 'Layer'):
                    font = QFont('Arial',12)
                    font.setBold(True)
                    l.setFont(font)


        self.tabWidget.setCurrentIndex(0)

        #then populate the specific tabwidgets with other QObjects:
        #tab 0 = 'General':
        self.nameEdit = QtGui.QLineEdit(self.tabs[0])
        self.nameEdit.setGeometry(QRect(250, 40, 150, 27))
        self.tabedits.append(self.nameEdit)

        self.descriptionEdit = QtGui.QLineEdit(self.tabs[0])
        self.descriptionEdit.setGeometry(QRect(250, 90, 150,27))
        self.tabedits.append(self.descriptionEdit)

        self.languageBox = QtGui.QComboBox(self.tabs[0])
        self.languageBox.setGeometry(QRect(250, 140, 113,27))
        self.languageBox.addItems(['en','de'])
        self.tabedits.append(self.languageBox)

        self.boxPublic = QtGui.QCheckBox(self.tabs[0])
        self.boxPublic.setGeometry(QRect(250, 180, 80, 17))
        self.boxPublic.setText('Public')
        self.tabboxes.append(self.boxPublic)

        self.boxActive = QtGui.QCheckBox(self.tabs[0])
        self.boxActive.setGeometry(QRect(250, 230, 80, 17))
        self.boxActive.setText('Active')
        self.tabboxes.append(self.boxActive)


        #tab 1 = 'Tools':
        toollist = ['Zoom in button', 'Zoom out button', 'Zoom to extent button', 'Step back to previous extent button',
                'Step forward to next extent button', 'Activate hover-select tool', 'Print button', 'Show measure tools button',
                'Show redlining tools button', 'Show workstate tools button', 'Show addwms tools button', 'Show meta toolbar button']
        y = 50
        self.tools = {}
        # a dictonary with toolbutton id as key and reference to the QCheckBox
        # as value, i.e.: {58: -Reference to QCheckBox Object-}
        tcount = 57
        for tool in toollist:
            t = QtGui.QCheckBox(self.tabs[1])
            t.setGeometry(QRect(60, y, 180, 17))
            t.setText(tool)
            self.tools[tcount] = t
            y += 30
            tcount += 1


        #tab 2 = 'Homeview':
        self.homeviewCenterEditX = QtGui.QLineEdit(self.tabs[2])
        self.homeviewCenterEditX.setGeometry(QRect(170, 50, 125, 25))
        self.tabedits.append(self.homeviewCenterEditX)
        self.homeviewCenterEditY = QtGui.QLineEdit(self.tabs[2])
        self.homeviewCenterEditY.setGeometry(QRect(330, 50, 125, 25))
        self.tabedits.append(self.homeviewCenterEditY)

        self.homeviewZoomBox = QtGui.QSpinBox(self.tabs[2])
        self.homeviewZoomBox.setGeometry(QRect(170, 100, 40, 25))
        self.moreObjects.append(self.homeviewZoomBox)

        self.extentEdits = []
        minX = QtGui.QLineEdit(self.tabs[2])
        minX.setGeometry(175, 360, 120, 25)
        self.extentEdits.append(minX)

        minY = QtGui.QLineEdit(self.tabs[2])
        minY.setGeometry(265, 320, 120, 25)
        self.extentEdits.append(minY)

        maxX = QtGui.QLineEdit(self.tabs[2])
        maxX.setGeometry(350, 360, 120, 25)
        self.extentEdits.append(maxX)

        maxY = QtGui.QLineEdit(self.tabs[2])
        maxY.setGeometry(265, 400, 120, 25)
        self.extentEdits.append(maxY)

        style = 'QLineEdit { background-color : #a6a6a6; color : white; }'
        for edit in self.extentEdits:
            edit.setReadOnly(True)
            edit.lower()
            edit.setStyleSheet(style)

        self.origExtentButton = QtGui.QPushButton(self.tabs[2])
        self.origExtentButton.setGeometry(100, 150, 190, 30)
        self.origExtentButton.setText('Set original homview')
        self.moreObjects.append(self.origExtentButton)

        self.qgsExtentButton = QtGui.QPushButton(self.tabs[2])
        self.qgsExtentButton.setGeometry(290, 150, 190, 30)
        self.qgsExtentButton.setText('Set current QGIS view')
        self.moreObjects.append(self.qgsExtentButton)

        self.homeviewEpsgWarning = QtGui.QLabel(self.tabs[2])
        self.homeviewEpsgWarning.setGeometry(QRect(50, 220, 435, 80))
        self.homeviewEpsgWarning.setFont(QFont('Arial', 9))

        self.jumpButtonOrig = QtGui.QPushButton(self.tabs[2])
        self.jumpButtonOrig.setGeometry(QRect(115, 192, 160, 20))
        self.jumpButtonOrig.setText('Jump to original homeview')
        self.jumpButtonOrig.setStyleSheet('QPushButton { background-color : #a6a6a6; color : white; }')

        self.jumpButtonNew = QtGui.QPushButton(self.tabs[2])
        self.jumpButtonNew.setGeometry(QRect(305, 192, 160, 20))
        self.jumpButtonNew.setText('Jump to new homeview')
        self.moreObjects.append(self.jumpButtonNew)


        #tab 3 = 'Layer' (layertree)

        self.layerlistwidget = LayerListWidget(self.tabs[3])
        self.layerlistwidget.setGeometry(QRect(25, 70, 210, 350))

        self.layertreewidget = LayerTreeWidget(self.tabs[3])
        self.layertreewidget.setGeometry(QRect(260, 70, 210, 350))


        #tab 4 = 'Permissions'
        self.usertabel = QtGui.QTableWidget(self.tabs[4])
        self.usertabel.setGeometry(QRect(10, 30, 230, 300))
        self.usertabel.setColumnCount(3)
        self.usertabel.setHorizontalHeaderLabels(['Read', 'Update', 'Delete'])
        self.moreObjects.append(self.usertabel)

        self.groupstabel = QtGui.QTableWidget(self.tabs[4])
        self.groupstabel.setGeometry(QRect(250, 30, 230, 300))
        self.groupstabel.setColumnCount(3)
        self.groupstabel.setHorizontalHeaderLabels(['Read', 'Update', 'Delete'])
        self.moreObjects.append(self.groupstabel)


        #create Gui surrounding the tabs
        self.editCheckBox = QtGui.QCheckBox(self)
        self.editCheckBox.setGeometry(QRect(420, 10, 50, 17))
        self.editCheckBox.setText('Edit')

        self.pushButtonOk = QtGui.QPushButton(self)
        self.pushButtonOk.setGeometry(QRect(420, 500, 85, 27))
        self.pushButtonCancel = QtGui.QPushButton(self)
        self.pushButtonCancel.setGeometry(QRect(320, 500, 85, 27))
        self.pushButtonCancel.setText('Cancel')

        self.warnLabel = QtGui.QLabel(self)
        self.warnLabel.setGeometry(QRect(300, 505, 80, 15))
        self.warnLabel.setText('Please fill out all mandatory fields')
        self.warnLabel.setHidden(True)
        self.warnLabel.setStyleSheet('QLabel { color : #ff6666; }')

    def setEditState(self, b):      #b = true or false
        if b:
            self.pushButtonOk.setText('Save Changes')
            self.pushButtonCancel.setHidden(False)

            for editable in self.getAllEditables():
                editable.setEnabled(b)


        else:
            self.pushButtonCancel.setHidden(True)
            self.pushButtonOk.setText('OK')

            for editable in self.getAllEditables():
                editable.setEnabled(b)

    def getAllEditables(self):
        list = []
        for edit in self.tabedits:
            list.append(edit)
        for box in self.tabboxes:
            list.append(box)
        for object in self.moreObjects:
            list.append(object)
        for box in self.tools.values():
            list.append(box)
        list.append(self.layerlistwidget)
        list.append(self.layertreewidget)
        return list


    def populateTable(self, table, usersList):
        if table == 'users':
            table = self.usertabel
        else:
            table = self.groupstabel

        tableRowCount = len(usersList)
        table.setRowCount(tableRowCount)

        for row in range(tableRowCount):
            user = usersList[row]
            table.setVerticalHeaderItem(row, QtGui.QTableWidgetItem(user['displayTitle']))
            permissions = user['permissions']
            permList = ['Read', 'Update', 'Delete']
            if not permissions:
                for x in permList:
                    item = QtGui.QTableWidgetItem(x)
                    item.setCheckState(Qt.Unchecked)
                    table.setItem(row, permList.index(x), item)
            else:
                for x in permList:
                    item = QtGui.QTableWidgetItem(x)
                    if x.upper() in permissions['permissions']:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                    table.setItem(row, permList.index(x), item)

    def noPermissionAccess(self):
        self.usertabel.setHidden(True)
        self.groupstabel.setHidden(True)
        self.noPermissionAccessLabel = QtGui.QLabel(self.tabs[4])
        self.noPermissionAccessLabel.setGeometry(QRect(50, 50, 420, 50))
        self.noPermissionAccessLabel.setText('Could not access application '
            'permissions. User permission is not high enough')

    def newAppCreation(self):
        self.usertabel.setHidden(True)
        self.groupstabel.setHidden(True)
        self.noPermissionAccessLabel = QtGui.QLabel(self.tabs[4])
        self.noPermissionAccessLabel.setGeometry(QRect(50, 50, 420, 100))
        self.noPermissionAccessLabel.setText('You have to save and upload the '
            'new application once\nfirst, then you can edit it\'s permissions')

    def showEpsgWarning(self, currentCrs, applicationCrs):
        self.homeviewEpsgWarning.setHidden(False)
        txt = 'Note: The coordinate reference system CRS of the current QGIS \n'
        txt += 'project: ' + currentCrs +' is different from this application\'s'
        txt += ' CRS: ' + applicationCrs + '\nIt is strongly recommended to '
        txt += 'change the QGIS Project CRS\nto ' + applicationCrs + ' before '
        txt += 'working with the homeview'
        self.homeviewEpsgWarning.setText(txt)

    def hideEpsgWarning(self):
        self.homeviewEpsgWarning.setHidden(True)
