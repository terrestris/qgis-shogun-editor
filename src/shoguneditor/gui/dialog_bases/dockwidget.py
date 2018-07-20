# -*- coding: utf-8 -*-
'''
(c) 2018 Terrestris GmbH & CO. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'Juli 2018'

import sys

if sys.version_info[0] >= 3:
    from qgis.PyQt.QtCore import QRect, Qt
    from qgis.PyQt.QtWidgets import QWidget, QPushButton, QDockWidget, QTreeWidget
else:
    from PyQt4.QtCore import QRect, Qt
    from PyQt4.QtGui import QWidget, QPushButton, QDockWidget, QTreeWidget

class DockWidget(QDockWidget):
    def  __init__(self):
        QDockWidget.__init__(self)
        self.setWindowTitle('Shogun Editor')
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setLayoutDirection(Qt.LeftToRight)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFloating(False)

        self.dockWidgetContents = QWidget(self)
        self.dockWidgetContents.setGeometry(QRect(20, 30, 320, 700))
        self.newConnectionButton = QPushButton(self.dockWidgetContents)
        self.newConnectionButton.setGeometry(QRect(10, 0, 141, 27))
        self.newConnectionButton.setText('New Connection')
        self.treeWidget = QTreeWidget(self.dockWidgetContents)
        self.treeWidget.setGeometry(QRect(10, 40, 300, 650))
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setColumnCount(1)
