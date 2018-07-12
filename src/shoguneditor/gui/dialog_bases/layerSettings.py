# -*- coding: utf-8 -*-
'''
(c) 2018 Terrestris GmbH & CO. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'Juli 2018'

from PyQt4.QtCore import QRect, Qt
from PyQt4 import QtGui
from qgis.gui import QgsMapLayerComboBox

class LayerSettingsDialog(QtGui.QDialog):
    def  __init__(self):
        QtGui.QDialog.__init__(self)
        self.tabs = []                 #All child-tabWidgets
        self.tabedits = []              #All QLineEdits and QComboBox per tabWidget in a list
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
        tab0labels = [['Name', (50, 50, 56, 17)],['Layer Opacity',(50,100,80,25)], ['Hover Template', (50, 150, 120, 17)]]
        tab1labels = [['Until now "Metadata" has to be edited in the shogun2-webapp', (50, 50, 300, 17)]]
        tab2labels = [['explanation', (50, 50, 400, 200)]]
        tab3labels = [['Users', (100, 10, 50, 20)], ['Groups', (320, 10, 50, 20)]]
        tabwidgets = [['General', tab0labels], ['Metadata', tab1labels], ['Style', tab2labels], ['Permissions', tab3labels]]

        expl = 'To edit the style of layer in shogun, first add the layer to QGIS.\n'
        expl += 'Then style the layer via the QGIS layer properties.\nWhen finished, '
        expl += 'you can upload the current layer style \nto this layer in Shogun by '
        expl += 'right-clicking it in \nthe Shogun Editor menu'

        #first set the labes for all tabwwidgets in a loop:
        for tab in tabwidgets:
            t = QtGui.QWidget()
            t.setObjectName(tab[0])
            self.tabs.append(t)
            self.tabWidget.addTab(t, tab[0])

            for label in tab[1]:
                l = QtGui.QLabel(t)
                l.setGeometry(QRect(label[1][0],label[1][1],label[1][2],label[1][3]))
                if label[0] == 'explanation':
                    l.setText(expl)
                    l.setAlignment(Qt.AlignTop)
                else:
                    l.setText(label[0])


        self.tabWidget.setCurrentIndex(0)


        #then populate the specific tabwidgets with other QObjects:
        #tab 0 = 'General':
        self.nameEdit = QtGui.QLineEdit(self.tabs[0])
        self.nameEdit.setGeometry(QRect(180, 40, 113, 27))
        self.tabedits.append(self.nameEdit)

        self.sliderEdit = QtGui.QLineEdit(self.tabs[0])
        self.sliderEdit.setGeometry(QRect(400, 90, 30, 23))
        self.sliderEdit.setInputMask('9.99')
        self.sliderEdit.setValidator(QtGui.QDoubleValidator(-0.01, 1.01, 2))
        self.tabedits.append(self.sliderEdit)

        self.hoverEdit = QtGui.QLineEdit(self.tabs[0])
        self.hoverEdit.setGeometry(QRect(180, 140, 113,27))
        self.tabedits.append(self.hoverEdit)

        self.hoverBox = QtGui.QComboBox(self.tabs[0])
        self.hoverBox.setGeometry(QRect(320, 140, 80, 27))
        self.tabedits.append(self.hoverBox)

        self.hoverAddButton = QtGui.QPushButton(self.tabs[0])
        self.hoverAddButton.setGeometry(QRect(410, 140, 30, 27))
        self.hoverAddButton.setText('Add')
        self.tabedits.append(self.hoverAddButton)

        self.slider = QtGui.QSlider(self.tabs[0])
        self.slider.setGeometry(QRect(180, 90, 160, 18))
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMaximum(100)
        self.slider.setMinimum(-1)
        self.slider.setEnabled(False)
        self.moreObjects.append(self.slider)
        self.slider.valueChanged.connect(lambda: self.sliderEdit.setText(str(float(self.slider.value())/100)))
        self.sliderEdit.textEdited.connect(lambda: self.slider.setValue(int(float(self.sliderEdit.text())*100)))

        self.hoverAddButton.clicked.connect(self.addHoverAttribute)



        #tab 3 = 'Permissions':
        self.usertabel = QtGui.QTableWidget(self.tabs[3])
        self.usertabel.setGeometry(QRect(10, 30, 230, 300))
        self.usertabel.setColumnCount(3)
        self.usertabel.setHorizontalHeaderLabels(['Read', 'Update', 'Delete'])
        self.moreObjects.append(self.usertabel)

        self.groupstabel = QtGui.QTableWidget(self.tabs[3])
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


    def addHoverAttribute(self):
        attribute = self.hoverBox.currentText()
        if len(attribute) > 0:
            attribute = '{' + attribute + '}'
        text = self.hoverEdit.text() + attribute
        self.hoverEdit.setText(text)


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
        return list


    def deactivateHoverEditing(self):
        self.hoverBox.setHidden(True)
        self.hoverEdit.setHidden(True)
        self.hoverAddButton.setHidden(True)
        self.infoEdit = QtGui.QLineEdit(self.tabs[0])
        self.infoEdit.setEnabled(False)
        self.infoEdit.setText('only available for vector layers')
        self.infoEdit.setGeometry(QRect(180, 143, 200 ,27))


    def populateTable(self, table, usersList):
        if table == 'users':
            table = self.usertabel
        else:
            table = self.groupstabel

        usersList = sorted(usersList, key = lambda x : x['displayTitle'])
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
                perms = permissions['permissions']
                for x in permList:
                    item = QtGui.QTableWidgetItem(x)
                    if perms[0] == 'ADMIN' or x.upper() in perms:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                    table.setItem(row, permList.index(x), item)
        table.sortItems(0, Qt.AscendingOrder)


    def noPermissionAccess(self):
        self.usertabel.setHidden(True)
        self.groupstabel.setHidden(True)
        self.noPermissionAccessLabel = QtGui.QLabel(self.tabs[3])
        self.noPermissionAccessLabel.setGeometry(QRect(50, 50, 420, 50))
        self.noPermissionAccessLabel.setText('Could not access application '
            'permissions. User permission is not high enough')



class UploadLayerDialog(QtGui.QDialog):
    def  __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi()

    def setupUi(self):
        self.resize(400, 400)
        self.setWindowTitle('Upload layer to Shogun')

        title = QtGui.QLabel(self)
        title.setGeometry(50,30,300,70)
        title.setText('Please select the layer you wish to upload to the \n Shogun Server')

        self.layerBox = QgsMapLayerComboBox(self)
        self.layerBox.setGeometry(QRect(50, 100, 300, 30))

        self.uploadButton = QtGui.QPushButton(self)
        self.uploadButton.setGeometry(QRect(250, 160, 100, 35))
        self.uploadButton.setText('Upload Layer')

        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setGeometry(QRect(140, 160, 100, 35))
        self.cancelButton.setText('Cancel')
        self.cancelButton.clicked.connect(self.hide)

        self.logWindow = QtGui.QTextEdit(self)
        self.logWindow.setGeometry(QRect(50, 200, 300, 180))
        self.logWindow.setReadOnly(True)
        self.logWindow.setText('Upload Log:')

    def log(self, message):
        msg = ' - ' + message
        self.logWindow.append(msg)
