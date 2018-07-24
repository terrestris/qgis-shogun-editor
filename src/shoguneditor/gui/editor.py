# -*- coding: utf-8 -*-
'''
(c) 2018 terrestris GmbH & Co. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'July 2018'

import sys

if sys.version_info[0] >= 3:
    from qgis.PyQt.QtCore import QObject, Qt, QTimer
    from qgis.PyQt.QtWidgets import QMenu, QAction, QMessageBox
    from qgis.PyQt.QtWidgets import QTreeWidgetItemIterator
else:
    from PyQt4.QtCore import QObject, Qt, QTimer
    from PyQt4.QtGui import QMenu, QAction, QMessageBox, QTreeWidgetItemIterator

from qgis.gui import QgsMessageBar
from qgis.core import QgsNetworkAccessManager

from .dialog_bases.connectdlg import ConnectDialog
from .dialog_bases.dockwidget import DockWidget
from .editoritems import EditorItem, EditorTopItem, QgisLayerItem, ApplicationItem, LayerItem
from shoguneditor.connection.shogunressource import ShogunRessource


class Editor(QObject):
    '''This class controls all plugin-related GUI elements.'''

    def __init__ (self, iface):
        '''initialize the GUI control'''
        QObject.__init__(self)
        self.iface = iface

        self.dock = DockWidget()
        self.connectdlg = ConnectDialog()
        self.iface.addDockWidget( Qt.RightDockWidgetArea, self.dock)
        self.dock.newConnectionButton.clicked.connect(lambda: self.showDialog(self.connectdlg))
        self.connectdlg.okButton.clicked.connect(self.setupNewConnection)
        self.topitem = EditorTopItem()
        self.connections = []
        self.dock.treeWidget.addTopLevelItem(self.topitem)
        self.dock.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dock.treeWidget.customContextMenuRequested.connect(self.on_context_menu)
        self.dock.treeWidget.itemDoubleClicked.connect(self.on_tree_item_double_clicked)

        self.timer = QTimer()

        '''
         WORKAROUND:
         When performing requests with self.http, it will call the
         QgsNetworkAccessManager.instance(). For some reason
         QgsNetworkAccessManager.instance() is connected with the QtCore SIGNAL
         'authenticationRequired' (inherited from QNetworkAccessManager) to a
         method where a dialog in QGIS pops up asking for the users credentials
         (when working with Basic Auth). We disable the signal here as the
         case of wrong identifacation credentials is treated separately
         in def: checkConnection(self)
         '''
        try:
            QgsNetworkAccessManager.instance().authenticationRequired.disconnect()
        except:
            pass


    def on_context_menu(self, point):

        item = self.dock.treeWidget.itemAt(point)
        if item is None:
            return
        if item.actiontype is None:
            return
        actionDict = {'application':
                        ('Copy Application', 'Load all layers to QGIS',
                        'Application Settings', 'View Application in web browser',
                         'Delete Application'),
                    'layer':
                        ('Add Layer to QGIS','Layer Settings', 'Delete Layer'),
                    'qgisLayerReference':
                        ('Upload New Style', 'Apply Original Style'),
                    'applicationsItem':
                        ('Create New Application', 'Refresh Applications'),
                    'layersItem':('Upload New Layer from QGIS', 'Refresh Layers'),
                    'connection':('Refresh Connection', 'Remove Connection'),
                    'topitem':['New Connection']}

        actions = actionDict[item.actiontype]
        menu = QMenu()
        acts = []
        for actionName in actions:
            action = QAction(actionName, None)
            self.connectAction(action, actionName, item)
            acts.append(action)
        menu.addActions(acts)
        point = self.dock.treeWidget.mapToGlobal(point)
        menu.exec_(point)

    # this could be re-written when refactoring:
    def connectAction(self, action, actionName, item):
        if actionName == 'Copy Application':
            action.triggered.connect(item.copyApplication)
        elif actionName == 'View Application in web browser':
            action.triggered.connect(lambda: item.ressource.viewApplicationOnline(item.id))
        elif actionName == 'New Connection':
            action.triggered.connect(lambda: self.showDialog(item))
        elif actionName == 'Application Settings':
            action.triggered.connect(lambda: self.showDialog(item))
        elif actionName == 'Layer Settings':
            action.triggered.connect(lambda: self.showDialog(item))
        elif actionName == 'Remove Connection':
            action.triggered.connect(lambda: self.removeConnection(item))
        elif actionName == 'Refresh Connection':
            action.triggered.connect(lambda: self.refreshConnection(item))
        elif actionName == 'Add Layer to QGIS':
            action.triggered.connect(lambda: item.addQgsLayer(self.iface))
        elif actionName == 'Upload New Style':
            action.triggered.connect(lambda: self.uploadStyle(item))
        elif actionName == 'Apply Original Style':
            action.triggered.connect(lambda: self.downloadStyle(item))
        elif actionName == 'Load all layers to QGIS':
            action.triggered.connect(lambda: self.loadAllAppLayers(item))
        elif actionName == 'Create New Application':
            action.triggered.connect(lambda: item.createNewApplication(self.iface))
        elif actionName == 'Upload New Layer from QGIS':
            action.triggered.connect(lambda: item.createNewLayer(self.iface))
        elif actionName == 'Delete Layer':
            action.triggered.connect(item.deleteLayer)
        elif actionName == 'Delete Application':
            action.triggered.connect(item.deleteApplication)
        elif actionName == 'Refresh Applications':
            action.triggered.connect(item.update)
        elif actionName == 'Refresh Layers':
            action.triggered.connect(item.update)


    def on_tree_item_double_clicked(self, item):
        if isinstance(item, QgisLayerItem):
            try:
                self.iface.showLayerProperties(item.layer)
            except:
                pass


    def showDialog(self, item):
        if not isinstance(item, ConnectDialog):
            if item.dlg is None:
                if isinstance(item, ApplicationItem):
                    item.createStaticSettings(self.iface)
                    item.populateSettings()
                elif isinstance(item, LayerItem):
                    item.createStaticSettings()
                    item.populateSettings()
            dialog = item.dlg
        else:
            dialog = self.connectdlg

        dialog.show()
        try:
            dialog.setWindowState(Qt.WindowActive)
            dialog.activateWindow()
        except:
            pass


    def setupNewConnection(self):
        # if the connect button gets clicked two times quickly it calls a new
        # test request before the old one is finished and making qgis crash
        # therefore we pause the signal for 1,5 seconds
        self.connectdlg.okButton.blockSignals(True)
        self.timer.timeout.connect(lambda: self.connectdlg.okButton.blockSignals(False))
        self.timer.start(1500)

        url = self.connectdlg.urlIn.text()
        name = self.connectdlg.nameIn.text()
        user = self.connectdlg.userIn.text()
        pw = self.connectdlg.passwordIn.text()

        if len(url) == 0 or len(name) == 0:
            self.showWarning(self.connectdlg, 'Please fill in all necessary '
                'fields')
            self.connectdlg.show()
            return

        if name in self.connections:
            self.showWarning(self.connectdlg, 'A connection with that name '
                'exists already, please fill in a different name')
            self.connectdlg.show()
            return

        newRessource = ShogunRessource(self.iface, url, name, user, pw)
        connectionOk = newRessource.checkConnection()
        if not connectionOk[0]:
            self.showWarning(self.connectdlg, connectionOk[1])
            self.connectdlg.show()
            return

        bool = newRessource.updateData()
        if not bool:
            self.showWarning(self.connectdlg, 'Error: Could not retrieve all '
                'data from Shogun')

        self.connectdlg.hide()

        newConnectionItem = EditorItem(newRessource)
        self.connections.append(name)
        self.topitem.addChild(newConnectionItem)
        self.topitem.setExpanded(True)
        newConnectionItem.applicationsitem.sortChildren(0, Qt.AscendingOrder)
        newConnectionItem.layersitem.sortChildren(0, Qt.AscendingOrder)
        self.expandEditorTree(newConnectionItem)

    def removeConnection(self, item):
        if item.name in self.connections:
            self.connections.remove(item.name)
        self.topitem.removeChild(item)

    def refreshConnection(self, item):
        item.ressource.updateData()
        item.update()
        self.topitem.setExpanded(True)
        self.expandEditorTree(item)

    def showWarning(self, parent, text):
        warn = QMessageBox.warning(parent, 'Warning',
                 text, QMessageBox.Ok)

    def uploadStyle(self, item):
        success = item.uploadStyle()
        if success:
            msg = 'New style of layer '+ item.parentShogunLayer.name
            msg += ' was successfully uploaded to Shogun.'
            self.iface.messageBar().pushSuccess('Success', msg)
        else:
            msg = 'New style of layer '+ item.parentShogunLayer.name
            msg += ' could not be uploaded to Shogun.'
            self.iface.messageBar().pushCritical('Error',msg)

    def downloadStyle(self, item):
        success = item.downloadStyle()
        if not success:
            msg = 'Could not download Style for layer'
            self.iface.messageBar().pushCritical('Error',msg)

    def loadAllAppLayers(self, item):
        layerIds, shogunConnectionItem = item.getAllAppLayersById()
        for layer in shogunConnectionItem.layersitem.layerlist:
            if layer.id in layerIds:
                layer.addQgsLayer(self.iface)

    def expandEditorTree(self, connectionItem):
        iter = QTreeWidgetItemIterator(connectionItem)
        val = iter.value()
        while val:
            val.setExpanded(True)
            iter += 1
            val = iter.value()
