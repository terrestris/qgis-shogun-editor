# -*- coding: utf-8 -*-
'''
(c) 2018 Terrestris GmbH & CO. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'Juli 2018'

from PyQt4.QtCore import QRect
from PyQt4.QtGui import QDialog, QLabel, QLineEdit, QPushButton

class ConnectDialog(QDialog):
    def  __init__(self):
        QDialog.__init__(self)
        self.resize(400, 300)
        self.setWindowTitle('Connection Dialog')

        self.label = QLabel(self)
        self.label.setGeometry(QRect(140, 150, 81, 20))
        self.label.setText('username')
        self.label2 = QLabel(self)
        self.label2.setGeometry(QRect(140, 190, 81, 20))
        self.label2.setText('password')
        self.label3 = QLabel(self)
        self.label3.setGeometry(QRect(40, 32, 151, 20))
        self.label3.setText('Name of the Shogun Client')
        self.label4 = QLabel(self)
        self.label4.setGeometry(QRect(40, 82, 151, 20))
        self.label4.setText('URL:')

        self.nameIn = QLineEdit(self)
        self.nameIn.setGeometry(QRect(200, 30, 180, 27))
        self.nameIn.setText('Default Shogun Client')
        self.urlIn = QLineEdit(self)
        self.urlIn.setGeometry(QRect(122, 80, 258, 27))
        self.urlIn.setPlaceholderText('i. e.: http(s)://.../shogun2-webapp')
        self.userIn = QLineEdit(self)
        self.userIn.setGeometry(QRect(230, 150, 150, 27))
        self.passwordIn = QLineEdit(self)
        self.passwordIn.setGeometry(QRect(230, 190, 150, 27))
        self.passwordIn.setEchoMode(QLineEdit.Password)
        self.okButton = QPushButton(self)
        self.okButton.setGeometry(QRect(270, 240, 85, 27))
        self.okButton.setText('OK')
        self.cancelButton = QPushButton(self)
        self.cancelButton.setGeometry(QRect(180, 240, 85, 27))
        self.cancelButton.setText('Cancel')
