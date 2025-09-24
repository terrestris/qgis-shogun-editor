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
    from qgis.PyQt.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, 
                                     QGroupBox, QSpacerItem, QSizePolicy)
else:
    from PyQt4.QtCore import QRect, Qt
    from PyQt4 import QtGui
    from PyQt4.QtGui import QFont
    from PyQt4.QtGui import (QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QGroupBox, QSpacerItem, QSizePolicy)

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
                newItem.setCheckState(0,Qt.Checked)
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
                newItem.setCheckState(0,Qt.Checked)
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
        self.setupStyling()

    def setupUi(self):
        self.setWindowTitle('Application Settings')
        self.setMinimumSize(600, 600)
        self.resize(600, 600)

        # Main layout
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(15, 15, 15, 15)
        mainLayout.setSpacing(10)

        # Create tabWidget that holds the tabs
        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.setObjectName('tabWidget')
        
        # Setup tabs
        self.setupGeneralTab()
        self.setupToolsTab()
        self.setupHomeviewTab()
        self.setupLayerTab()
        self.setupPermissionsTab()
        
        mainLayout.addWidget(self.tabWidget)
        
        # Button layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        
        cancelButton = QtGui.QPushButton('Cancel')
        cancelButton.setMinimumSize(80, 35)
        okButton = QtGui.QPushButton('OK')
        okButton.setMinimumSize(80, 35)
        okButton.setDefault(True)
        
        buttonLayout.addWidget(cancelButton)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(okButton)
        
        mainLayout.addLayout(buttonLayout)

    def setupGeneralTab(self):
        """Setup the General tab with improved layout"""
        tab = QtGui.QWidget()
        tab.setObjectName('General')
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, 'General')
        
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Basic Information Group
        basicGroup = QGroupBox("Basic Information")
        basicLayout = QFormLayout(basicGroup)
        basicLayout.setSpacing(10)
        basicLayout.setLabelAlignment(Qt.AlignRight)
        
        self.nameEdit = QtGui.QLineEdit()
        self.nameEdit.setToolTip("Enter the application name")
        basicLayout.addRow("Name:", self.nameEdit)
        self.tabedits.append(self.nameEdit)
        
        self.descriptionEdit = QtGui.QLineEdit()
        self.descriptionEdit.setToolTip("Enter a description for this application")
        basicLayout.addRow("Description:", self.descriptionEdit)
        self.tabedits.append(self.descriptionEdit)
        
        self.languageBox = QtGui.QComboBox()
        self.languageBox.addItems(['en', 'de'])
        self.languageBox.setToolTip("Select the application language")
        basicLayout.addRow("Language:", self.languageBox)
        self.tabedits.append(self.languageBox)
        
        layout.addWidget(basicGroup)
        
        # Settings Group
        settingsGroup = QGroupBox("Application Settings")
        settingsLayout = QVBoxLayout(settingsGroup)
        settingsLayout.setSpacing(10)
        
        self.boxPublic = QtGui.QCheckBox('Public')
        self.boxPublic.setToolTip("Make this application publicly accessible")
        settingsLayout.addWidget(self.boxPublic)
        self.tabboxes.append(self.boxPublic)
        
        self.boxActive = QtGui.QCheckBox('Active')
        self.boxActive.setToolTip("Enable this application")
        settingsLayout.addWidget(self.boxActive)
        self.tabboxes.append(self.boxActive)
        
        layout.addWidget(settingsGroup)
        layout.addStretch()

    def setupToolsTab(self):
        """Setup the Tools tab with improved layout"""
        tab = QtGui.QWidget()
        tab.setObjectName('Tools')
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, 'Tools')
        
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Tools Group
        toolsGroup = QGroupBox("Available Tools")
        toolsGroup.setToolTip("Select which tools/buttons to activate in the application")
        toolsLayout = QVBoxLayout(toolsGroup)
        toolsLayout.setSpacing(8)
        
        toollist = ['Zoom in button', 'Zoom out button', 'Zoom to extent button', 'Step back to previous extent button',
                    'Step forward to next extent button', 'Activate hover-select tool', 'Print button', 'Show measure tools button',
                    'Show redlining tools button', 'Show workstate tools button', 'Show addwms tools button', 'Show meta toolbar button']
        
        self.tools = {}
        tcount = 57
        for tool in toollist:
            checkbox = QtGui.QCheckBox(tool)
            checkbox.setToolTip(f"Enable/disable {tool.lower()}")
            toolsLayout.addWidget(checkbox)
            self.tools[tcount] = checkbox
            tcount += 1
            
        layout.addWidget(toolsGroup)
        layout.addStretch()

    def setupHomeviewTab(self):
        """Setup the Homeview tab with improved layout"""
        tab = QtGui.QWidget()
        tab.setObjectName('Homeview')
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, 'Homeview')
        
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Center Group
        centerGroup = QGroupBox("Map Center")
        centerLayout = QFormLayout(centerGroup)
        centerLayout.setSpacing(10)
        
        # Center coordinates in a horizontal layout
        coordLayout = QHBoxLayout()
        
        xLabel = QtGui.QLabel("X:")
        self.xEdit = QtGui.QLineEdit()
        self.xEdit.setToolTip("X coordinate for map center")
        
        yLabel = QtGui.QLabel("Y:")
        self.yEdit = QtGui.QLineEdit()
        self.yEdit.setToolTip("Y coordinate for map center")
        
        coordLayout.addWidget(xLabel)
        coordLayout.addWidget(self.xEdit)
        coordLayout.addSpacing(20)
        coordLayout.addWidget(yLabel)
        coordLayout.addWidget(self.yEdit)
        coordLayout.addStretch()
        
        centerLayout.addRow("Coordinates:", coordLayout)
        
        # Zoom
        self.zoomEdit = QtGui.QLineEdit()
        self.zoomEdit.setToolTip("Initial zoom level")
        centerLayout.addRow("Zoom:", self.zoomEdit)
        
        layout.addWidget(centerGroup)
        
        # Extent Group
        extentGroup = QGroupBox("Map Extent")
        extentLayout = QVBoxLayout(extentGroup)
        
        # Create extent edits
        self.extentEdits = []
        extentFormLayout = QFormLayout()
        
        extentCoordLayout = QHBoxLayout()
        
        minXLabel = QtGui.QLabel("MinX:")
        minX = QtGui.QLineEdit()
        minX.setReadOnly(True)
        self.extentEdits.append(minX)
        
        minYLabel = QtGui.QLabel("MinY:")
        minY = QtGui.QLineEdit()
        minY.setReadOnly(True)
        self.extentEdits.append(minY)
        
        maxXLabel = QtGui.QLabel("MaxX:")
        maxX = QtGui.QLineEdit()
        maxX.setReadOnly(True)
        self.extentEdits.append(maxX)
        
        maxYLabel = QtGui.QLabel("MaxY:")
        maxY = QtGui.QLineEdit()
        maxY.setReadOnly(True)
        self.extentEdits.append(maxY)
        
        # Arrange extent fields in a grid-like layout
        extentGrid1 = QHBoxLayout()
        extentGrid1.addWidget(minXLabel)
        extentGrid1.addWidget(minX)
        extentGrid1.addSpacing(20)
        extentGrid1.addWidget(maxXLabel)
        extentGrid1.addWidget(maxX)
        
        extentGrid2 = QHBoxLayout()
        extentGrid2.addWidget(minYLabel)
        extentGrid2.addWidget(minY)
        extentGrid2.addSpacing(20)
        extentGrid2.addWidget(maxYLabel)
        extentGrid2.addWidget(maxY)
        
        extentLayout.addLayout(extentGrid1)
        extentLayout.addLayout(extentGrid2)
        
        # Extent buttons
        buttonLayout = QHBoxLayout()
        
        self.origExtentButton = QtGui.QPushButton('Set to original extent')
        self.origExtentButton.setToolTip("Reset to the original map extent")
        buttonLayout.addWidget(self.origExtentButton)
        self.moreObjects.append(self.origExtentButton)
        
        self.jumpButtonOrig = QtGui.QPushButton('Jump to original homeview')
        self.jumpButtonOrig.setToolTip("Jump to the original homeview")
        buttonLayout.addWidget(self.jumpButtonOrig)
        self.moreObjects.append(self.jumpButtonOrig)
        
        extentLayout.addLayout(buttonLayout)
        
        self.jumpButtonNew = QtGui.QPushButton('Jump to new homeview')
        self.jumpButtonNew.setToolTip("Jump to the new homeview")
        extentLayout.addWidget(self.jumpButtonNew)
        self.moreObjects.append(self.jumpButtonNew)
        
        layout.addWidget(extentGroup)
        layout.addStretch()

    def setupLayerTab(self):
        """Setup the Layer tab with improved layout"""
        tab = QtGui.QWidget()
        tab.setObjectName('Layer')
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, 'Layer')
        
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        headerLayout = QHBoxLayout()
        
        allLayersLabel = QtGui.QLabel("All Layers")
        font = QFont('Arial', 12)
        font.setBold(True)
        allLayersLabel.setFont(font)
        allLayersLabel.setAlignment(Qt.AlignCenter)
        
        layerTreeLabel = QtGui.QLabel("Layer Tree")
        layerTreeLabel.setFont(font)
        layerTreeLabel.setAlignment(Qt.AlignCenter)
        
        headerLayout.addWidget(allLayersLabel)
        headerLayout.addWidget(layerTreeLabel)
        
        layout.addLayout(headerLayout)
        
        # Content layout
        contentLayout = QHBoxLayout()
        
        self.layerlistwidget = LayerListWidget(tab)
        self.layertreewidget = LayerTreeWidget(tab)
        
        contentLayout.addWidget(self.layerlistwidget)
        contentLayout.addWidget(self.layertreewidget)
        
        layout.addLayout(contentLayout)

    def setupPermissionsTab(self):
        """Setup the Permissions tab with improved layout"""
        tab = QtGui.QWidget()
        tab.setObjectName('Permissions')
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, 'Permissions')
        
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        headerLayout = QHBoxLayout()
        
        usersLabel = QtGui.QLabel("Users")
        font = QFont('Arial', 12)
        font.setBold(True)
        usersLabel.setFont(font)
        usersLabel.setAlignment(Qt.AlignCenter)
        
        groupsLabel = QtGui.QLabel("Groups")
        groupsLabel.setFont(font)
        groupsLabel.setAlignment(Qt.AlignCenter)
        
        headerLayout.addWidget(usersLabel)
        headerLayout.addWidget(groupsLabel)
        
        layout.addLayout(headerLayout)
        
        # Tables layout
        tablesLayout = QHBoxLayout()
        
        self.usertabel = QtGui.QTableWidget()
        self.grouptabel = QtGui.QTableWidget()
        
        tablesLayout.addWidget(self.usertabel)
        tablesLayout.addWidget(self.grouptabel)
        
        layout.addLayout(tablesLayout)

    def setupStyling(self):
        """Apply modern styling to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: white;
                border-radius: 4px;
            }
            QTabWidget::tab-bar {
                left: 5px;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                border: 1px solid #ccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background-color: #d4edda;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
                min-width: 120px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #0066cc;
            }
            QLineEdit:read-only {
                background-color: #f8f9fa;
                color: #666;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QCheckBox {
                spacing: 5px;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #0066cc;
                border-radius: 3px;
                background-color: #0066cc;
                image: url(data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'><path fill='white' d='M10.3 3.7L5 9l-3.3-3.3 1.4-1.4L5 6.2l3.9-3.9z'/></svg>);
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QListWidget, QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
        """)

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
