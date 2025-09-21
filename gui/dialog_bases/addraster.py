# -*- coding: utf-8 -*-
'''
(c) 2018 terrestris GmbH & Co. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'July 2018'

import sys

if sys.version_info[0] >= 3:
    from qgis.PyQt.QtWidgets import QDialog, QPushButton, QLabel
    from qgis.PyQt import QtCore
else:
    from PyQt4.QtGui import QDialog, QPushButton, QLabel
    from PyQt4 import QtCore

class AddRasterDialog(QDialog):
    def __init__(self):
        super(QDialog, self).__init__()
        self.resize(410, 200)
        self.setWindowTitle('Add Raster Layer Dialog')
        self.label = QLabel(self)
        self.label.setGeometry(QtCore.QRect(20,20,300,100))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setText('The requested ressource is a raster layer. \n'
            'Depending on it\'s size\', downloading \nand importing it to QGIS'
            'may \ntake while. You can also consider to only import the\n'
            'layer as a WMS if you only need to view it')
        self.cancelbutton = QPushButton(self)
        self.cancelbutton.setText('Cancel')
        self.cancelbutton.setGeometry(QtCore.QRect(20,150,125,30))
        self.wmsbutton = QPushButton(self)
        self.wmsbutton.setText('Add as WMS Layer')
        self.wmsbutton.setGeometry(QtCore.QRect(150,150,125,30))
        self.rasterbutton = QPushButton(self)
        self.rasterbutton.setText('Add as Raster Layer')
        self.rasterbutton.setGeometry(QtCore.QRect(280,150,125,30))

        # we reconfigure the already existing slot self.done() (inherited
        # from QDialog to emit different ints - self.done() is called by
        # exec_())
        self.cancelbutton.clicked.connect(lambda: self.done(0))
        self.wmsbutton.clicked.connect(lambda: self.done(1))
        self.rasterbutton.clicked.connect(lambda: self.done(2))
