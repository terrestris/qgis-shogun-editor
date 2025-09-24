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
    from qgis.PyQt.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, 
                                     QVBoxLayout, QHBoxLayout, QFormLayout, 
                                     QGroupBox, QSpacerItem, QSizePolicy)
    from qgis.PyQt.QtGui import QIcon, QFont
else:
    from PyQt4.QtCore import QRect, Qt
    from PyQt4.QtGui import (QDialog, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QGroupBox, QSpacerItem, QSizePolicy, QIcon, QFont)

class ConnectDialog(QDialog):
    def  __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle('Shogun Connection')
        self.setupUi()
        self.setupStyling()
        
    def setupUi(self):
        # Main layout
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(20, 20, 20, 20)
        
        # Title area with logo placeholder
        titleLayout = QHBoxLayout()
        logoLabel = QLabel()
        logoLabel.setText("🌐")  # Unicode globe as placeholder
        logoLabel.setStyleSheet("font-size: 32px; color: #0066cc;")
        logoLabel.setAlignment(Qt.AlignCenter)
        
        titleLabel = QLabel("Connect to Shogun Server")
        titleFont = QFont()
        titleFont.setPointSize(14)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignCenter)
        
        titleLayout.addWidget(logoLabel)
        titleLayout.addWidget(titleLabel)
        titleLayout.addStretch()
        mainLayout.addLayout(titleLayout)
        
        # Connection details group
        connectionGroup = QGroupBox("Connection Details")
        connectionGroup.setStyleSheet("""
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
        """)
        
        connectionLayout = QFormLayout(connectionGroup)
        connectionLayout.setSpacing(15)
        connectionLayout.setLabelAlignment(Qt.AlignRight)
        
        # Client name
        self.nameIn = QLineEdit()
        self.nameIn.setText('Default Shogun Client')
        self.nameIn.setToolTip('Enter a descriptive name for this connection')
        connectionLayout.addRow("Client Name:", self.nameIn)
        
        # URL
        self.urlIn = QLineEdit()
        self.urlIn.setPlaceholderText('e.g.: https://your-server.com/shogun2-webapp')
        self.urlIn.setToolTip('Enter the full URL to your Shogun server')
        connectionLayout.addRow("Server URL:", self.urlIn)
        
        mainLayout.addWidget(connectionGroup)
        
        # Authentication group
        authGroup = QGroupBox("Authentication")
        authGroup.setStyleSheet(connectionGroup.styleSheet())
        
        authLayout = QFormLayout(authGroup)
        authLayout.setSpacing(15)
        authLayout.setLabelAlignment(Qt.AlignRight)
        
        # Username
        self.userIn = QLineEdit()
        self.userIn.setToolTip('Enter your username')
        authLayout.addRow("Username:", self.userIn)
        
        # Password
        self.passwordIn = QLineEdit()
        self.passwordIn.setEchoMode(QLineEdit.Password)
        self.passwordIn.setToolTip('Enter your password')
        authLayout.addRow("Password:", self.passwordIn)
        
        mainLayout.addWidget(authGroup)
        
        # Add some spacing
        mainLayout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Button layout
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.setMinimumSize(90, 35)
        
        self.okButton = QPushButton('Connect')
        self.okButton.setMinimumSize(90, 35)
        self.okButton.setDefault(True)
        
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(self.okButton)
        
        mainLayout.addLayout(buttonLayout)
        
        # Set reasonable size
        self.setMinimumSize(450, 350)
        self.resize(450, 350)
        
    def setupStyling(self):
        # Modern dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus {
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
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QPushButton[text="Cancel"] {
                background-color: #6c757d;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #5a6268;
            }
            QLabel {
                color: #333;
            }
        """)
