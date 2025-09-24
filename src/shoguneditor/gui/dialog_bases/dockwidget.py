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
    from qgis.PyQt.QtWidgets import (QWidget, QPushButton, QDockWidget, QTreeWidget,
                                     QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,
                                     QLabel, QFrame)
    from qgis.PyQt.QtGui import QFont
else:
    from PyQt4.QtCore import QRect, Qt
    from PyQt4.QtGui import (QWidget, QPushButton, QDockWidget, QTreeWidget,
                             QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,
                             QLabel, QFrame, QFont)

class DockWidget(QDockWidget):
    def  __init__(self):
        QDockWidget.__init__(self)
        self.setWindowTitle('Shogun Editor')
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setLayoutDirection(Qt.LeftToRight)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFloating(False)
        self.setupUi()
        self.setupStyling()

    def setupUi(self):
        # Main widget container
        self.dockWidgetContents = QWidget(self)
        self.setWidget(self.dockWidgetContents)
        
        # Main layout
        mainLayout = QVBoxLayout(self.dockWidgetContents)
        mainLayout.setSpacing(10)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        
        # Header with logo and title
        headerFrame = QFrame()
        headerFrame.setFrameStyle(QFrame.StyledPanel)
        headerFrame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        headerLayout = QHBoxLayout(headerFrame)
        headerLayout.setContentsMargins(10, 8, 10, 8)
        
        # Logo placeholder
        logoLabel = QLabel("🔗")
        logoLabel.setStyleSheet("font-size: 20px; color: #0066cc;")
        logoLabel.setAlignment(Qt.AlignCenter)
        
        # Title
        titleLabel = QLabel("Shogun Editor")
        titleFont = QFont()
        titleFont.setPointSize(12)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setStyleSheet("color: #333; margin-left: 5px;")
        
        headerLayout.addWidget(logoLabel)
        headerLayout.addWidget(titleLabel)
        headerLayout.addStretch()
        
        mainLayout.addWidget(headerFrame)
        
        # Connection button
        self.newConnectionButton = QPushButton('+ New Connection')
        self.newConnectionButton.setMinimumHeight(35)
        mainLayout.addWidget(self.newConnectionButton)
        
        # Tree widget
        self.treeWidget = QTreeWidget()
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setColumnCount(1)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setRootIsDecorated(True)
        self.treeWidget.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #e6f3ff;
            }
            QTreeWidget::branch:has-siblings:!adjoins-item {
                border-image: url() 0;
            }
            QTreeWidget::branch:has-siblings:adjoins-item {
                border-image: url() 0;
            }
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url() 0;
            }
        """)
        
        mainLayout.addWidget(self.treeWidget, 1)  # Give tree widget maximum space
        
        # Status/info area
        statusFrame = QFrame()
        statusFrame.setFrameStyle(QFrame.StyledPanel)
        statusFrame.setMaximumHeight(60)
        statusFrame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """)
        
        statusLayout = QVBoxLayout(statusFrame)
        statusLayout.setContentsMargins(8, 5, 8, 5)
        
        statusLabel = QLabel("Right-click items for options")
        statusLabel.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        statusLayout.addWidget(statusLabel)
        
        mainLayout.addWidget(statusFrame)
        
    def setupStyling(self):
        # Style the dock widget and its components
        self.setStyleSheet("""
            QDockWidget {
                background-color: #ffffff;
                color: #333;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QDockWidget::title {
                background-color: #0066cc;
                color: white;
                font-weight: bold;
                padding: 8px;
                text-align: center;
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
        """)
