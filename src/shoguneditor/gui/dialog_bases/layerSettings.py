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
    from qgis.PyQt.QtGui import QDoubleValidator
    # we are faking the old way of QtGui, not the best style, but makes it easier
    # for switching betweeng version 2 and 3
    from qgis.PyQt import QtWidgets as QtGui
    from qgis.PyQt.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, 
                                     QGroupBox, QSpacerItem, QSizePolicy, QTextEdit)
else:
    from PyQt4.QtCore import QRect, Qt
    from PyQt4 import QtGui
    from PyQt4.QtGui import (QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QGroupBox, QSpacerItem, QSizePolicy, QTextEdit)

from qgis.gui import QgsMapLayerComboBox

class LayerSettingsDialog(QtGui.QDialog):
    def  __init__(self):
        QtGui.QDialog.__init__(self)
        self.tabs = []                 #All child-tabWidgets
        self.tabedits = []              #All QLineEdits and QComboBox per tabWidget in a list
        self.tabboxes = []              #All QCheckBoxes per tabWidget in a list
        self.moreObjects = []
        self.setupUi()
        self.setupStyling()

    def setupUi(self):
        self.setWindowTitle('Layer Settings')
        self.setMinimumSize(600, 500)
        self.resize(600, 500)

        # Main layout
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(15, 15, 15, 15)
        mainLayout.setSpacing(10)

        # Create tabWidget that holds the tabs
        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.setObjectName('tabWidget')
        
        # Setup tabs
        self.setupGeneralTab()
        self.setupMetadataTab()
        self.setupStyleTab()
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
        basicGroup = QGroupBox("Layer Information")
        basicLayout = QFormLayout(basicGroup)
        basicLayout.setSpacing(10)
        basicLayout.setLabelAlignment(Qt.AlignRight)
        
        self.nameEdit = QtGui.QLineEdit()
        self.nameEdit.setToolTip("Enter the layer name")
        basicLayout.addRow("Name:", self.nameEdit)
        self.tabedits.append(self.nameEdit)
        
        # Layer Opacity with slider-style input
        opacityLayout = QHBoxLayout()
        self.sliderEdit = QtGui.QLineEdit()
        self.sliderEdit.setInputMask('9.99')
        self.sliderEdit.setMaximumWidth(60)
        self.sliderEdit.setToolTip("Layer opacity (0.00 to 1.00)")
        if sys.version_info[0] >= 3:
            validator = QDoubleValidator(-0.01, 1.01, 2)
        else:
            validator = QtGui.QDoubleValidator(-0.01, 1.01, 2)
        self.sliderEdit.setValidator(validator)
        self.tabedits.append(self.sliderEdit)
        
        opacityLayout.addWidget(self.sliderEdit)
        opacityLayout.addWidget(QtGui.QLabel("(0.00 = transparent, 1.00 = opaque)"))
        opacityLayout.addStretch()
        basicLayout.addRow("Layer Opacity:", opacityLayout)
        
        # Hover Template
        hoverLayout = QHBoxLayout()
        self.hoverEdit = QtGui.QLineEdit()
        self.hoverEdit.setToolTip("Enter hover template field name")
        hoverLayout.addWidget(self.hoverEdit)
        
        self.hoverBox = QtGui.QComboBox()
        self.hoverBox.setToolTip("Select from available fields")
        hoverLayout.addWidget(self.hoverBox)
        
        self.hoverAddButton = QtGui.QPushButton('Add')
        self.hoverAddButton.setMaximumWidth(60)
        self.hoverAddButton.setToolTip("Add the selected field to hover template")
        hoverLayout.addWidget(self.hoverAddButton)
        
        basicLayout.addRow("Hover Template:", hoverLayout)
        
        self.tabedits.extend([self.hoverEdit, self.hoverBox, self.hoverAddButton])
        
        layout.addWidget(basicGroup)
        layout.addStretch()

    def setupMetadataTab(self):
        """Setup the Metadata tab with improved layout"""
        tab = QtGui.QWidget()
        tab.setObjectName('Metadata')
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, 'Metadata')
        
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Info message
        infoGroup = QGroupBox("Metadata Information")
        infoLayout = QVBoxLayout(infoGroup)
        
        infoLabel = QtGui.QLabel('Until now "Metadata" has to be edited in the shogun2-webapp')
        infoLabel.setWordWrap(True)
        infoLabel.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        infoLayout.addWidget(infoLabel)
        
        layout.addWidget(infoGroup)
        layout.addStretch()

    def setupStyleTab(self):
        """Setup the Style tab with improved layout"""
        tab = QtGui.QWidget()
        tab.setObjectName('Style')
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, 'Style')
        
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Style Instructions Group
        styleGroup = QGroupBox("Style Instructions")
        styleLayout = QVBoxLayout(styleGroup)
        
        explanation = 'To edit the style of layer in shogun, first add the layer to QGIS.\n\n'
        explanation += 'Then style the layer via the QGIS layer properties.\n\n'
        explanation += 'When finished, you can upload the current layer style to this layer in Shogun by '
        explanation += 'right-clicking it in the Shogun Editor menu'
        
        explanationLabel = QtGui.QLabel(explanation)
        explanationLabel.setWordWrap(True)
        explanationLabel.setAlignment(Qt.AlignTop)
        explanationLabel.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
                line-height: 1.4;
            }
        """)
        styleLayout.addWidget(explanationLabel)
        
        layout.addWidget(styleGroup)
        layout.addStretch()

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
        usersLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
        usersLabel.setAlignment(Qt.AlignCenter)
        
        groupsLabel = QtGui.QLabel("Groups")
        groupsLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
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
                min-width: 80px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #0066cc;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
        """)

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
