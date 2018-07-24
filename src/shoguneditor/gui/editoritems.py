# -*- coding: utf-8 -*-
'''
(c) 2018 terrestris GmbH & Co. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'July 2018'

import sys

if sys.version_info[0] >= 3:
    from qgis.PyQt.QtWidgets import QLabel, QLineEdit, QLabel, QMessageBox, QTreeWidgetItem
    from qgis.PyQt.QtGui import QFont, QIcon
    from qgis.PyQt.QtCore import QRect, Qt
    from qgis.core import QgsPointXY, QgsProject, QgsWkbTypes
    import shoguneditor.resources3
else:
    from PyQt4.QtGui import QLabel, QLineEdit, QFont, QLabel, QMessageBox, QTreeWidgetItem, QIcon
    from PyQt4.QtCore import QRect, Qt
    from qgis.core import QgsPoint, QgsMapLayerRegistry, QGis
    import shoguneditor.resources2

from qgis.core import QgsMapLayer, QgsProject, QgsLayerItem
from qgis.core import QgsRectangle

from shoguneditor.layerutils import prepareLayerForUpload, createLayer
from .dialog_bases.applicationSettings import ApplicationSettingsDialog
from .dialog_bases.layerSettings import LayerSettingsDialog, UploadLayerDialog


PYTHON_VERSION = sys.version_info[0]

'''This file contains all classes used in the QTreeWidget representating the
structure of the connected shogun2-webapp ressource'''

## TODO: the classes LayerItem and ApplicationItem could be merged or inherit
# from a common abstract class, the same is LayerSettingsDialog and
# ApplicationSettingsDialog. Note when refactoring for future release

class TreeItem(QTreeWidgetItem):
    ''' This class works as a kind of 'abstract class' from which all other
    classes in this module inherit'''
    def __init__(self, icon = None, text = None):
        QTreeWidgetItem.__init__(self)
        self.setText(0, text)
        if icon is not None:
            if isinstance(icon, QIcon):
                self.setIcon(0, icon)
            elif isinstance(icon, str):
                iconPath = ':/plugins/shoguneditor/' + icon
                self.setIcon(0, QIcon(iconPath))
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.actiontype = None



class EditorTopItem(TreeItem):
    def __init__(self):
        TreeItem.__init__(
            self, 'shogun-logo-50x50px-round-blue.png', 'Shogun Connections')
        self.actiontype = 'topitem'
        font = QFont('Arial',14)
        font.setBold(True)
        self.setFont(0,font)



class EditorItem(TreeItem):
    def __init__(self, shogunRessource):
        self.ressource = shogunRessource
        self.name = shogunRessource.name
        TreeItem.__init__(self, 'shogun-logo-25x-25px.png', self.name)
        self.isConnected = False
        self.actiontype = 'connection'
        font = QFont('Arial',12)
        font.setBold(True)
        self.setFont(0,font)
        self.populateTree(shogunRessource)

    def disconnectSignals(self):
        if self.layersitem is not None:
            for layer in self.layersitem.layerlist:
                if PYTHON_VERSION >= 3:
                    try:
                        QgsProject.instance().layerRemoved.disconnect(layer.updateLayerList)
                    except:
                        pass
                else:
                    try:
                        QgsMapLayerRegistry.instance().layerRemoved.disconnect(layer.updateLayerList)
                    except:
                        pass

    def update(self):
        for x in [self.applicationsitem, self.layersitem]:
            self.removeChild(x)
        self.populateTree(self.ressource)

    def populateTree(self, shogunRessource):
        self.applicationsitem = ApplicationsItem(shogunRessource)
        self.layersitem = LayersItem(shogunRessource)

        self.addChildren([self.applicationsitem, self.layersitem])



class ApplicationsItem(TreeItem):
    def __init__(self, ressource):
        TreeItem.__init__(self, 'applications-logo.png', 'Applications')
        self.ressource = ressource
        self.applications = self.ressource.getApplicationIdsAndNames()
        self.applicationlist = []
        self.actiontype = 'applicationsItem'
        font = QFont('Arial',10)
        font.setBold(True)
        self.setFont(0,font)
        self.populate()


    def createNewApplication(self, iface):
        self.newApplication = ApplicationItem(None, '', self.ressource)
        self.newApplication.createStaticSettings(iface)
        self.dlg = self.newApplication.dlg
        self.dlg.setEditState(True)
        self.dlg.editCheckBox.setHidden(True)
        self.dlg.pushButtonOk.setText('Create')
        self.dlg.pushButtonOk.clicked.disconnect(self.dlg.hide)
        self.dlg.pushButtonOk.clicked.connect(self.checkNewApplicationSettings)
        self.dlg.pushButtonCancel.clicked.disconnect(self.newApplication.stopEditing)
        self.dlg.pushButtonCancel.clicked.connect(self.dlg.hide)
        self.dlg.pushButtonCancel.setHidden(False)

        for toolbox in self.dlg.tools.values():
            toolbox.setChecked(True)

        exampleHomeview = {'mapconfig' : {
            'id' : None,
            'center' : {'x' : 0.0, 'y' : 0.0},
            'zoom' : 18,
            'resolutions': [156543.03390625, 78271.516953125, 39135.7584765625,
            19567.87923828125, 9783.939619140625, 4891.9698095703125, 2445.9849047851562,
            1222.9924523925781, 611.4962261962891, 305.74811309814453, 152.87405654907226,
            76.43702827453613, 38.218514137268066, 19.109257068634033, 9.554628534317017,
            4.777314267158508, 2.388657133579254, 1.194328566789627, 0.5971642833948135]
            }
        }

        self.newApplication.homeview = exampleHomeview
        self.newApplication.setQgsExtent(iface)
        self.dlg.origExtentButton.setEnabled(False)
        self.dlg.jumpButtonOrig.setEnabled(False)
        self.dlg.homeviewZoomBox.setMaximum(18)

        allLayers = self.ressource.getLayerIdsAndNames()
        self.dlg.layerlistwidget.populateList(allLayers)
        self.dlg.layertreewidget.setupNewTree()

        self.dlg.newAppCreation()

        self.dlg.show()

    def checkNewApplicationSettings(self):
        name = self.dlg.nameEdit.text()

        if len(name) == 0:
            self.dlg.nameEdit.setStyleSheet('QLineEdit { background-color: #ff3333; }')
            self.dlg.warnLabel.setHidden(False)
            return
        else:
            self.dlg.nameEdit.setStyleSheet('QLineEdit { border-color : #000000; }')
            self.dlg.warnLabel.setHidden(True)

        newhomeview = self.newApplication.getHomeViewChanges()
        if newhomeview is None:
            newhomeview = self.newApplication.homeview['mapconfig']
        data = {
            'id' : None,
            'name' : name,
            'description' : self.dlg.descriptionEdit.text(),
            'language' : self.dlg.languageBox.currentText(),
            'isPublic' : self.dlg.boxPublic.isChecked(),
            'isActive' : self.dlg.boxActive.isChecked(),
            'activeTools' : [x['id'] for x in self.newApplication.getActiveToolsChanges()],
            'projection' : 'EPSG:3857',
            'center' : {'x' : newhomeview['center']['x'], 'y' : newhomeview['center']['y']},
            'zoom' : newhomeview['zoom'],
            'layerTree': 4535
            }

        self.dlg.hide()
        uploaded = self.ressource.uploadNewApplication(data)
        if uploaded:
            self.update()

    def populate(self):
        for app in self.applications:
            item = ApplicationItem(app[0], app[1], self.ressource)
            self.addChild(item)
            self.applicationlist.append(item)
        self.sortChildren(0, Qt.AscendingOrder)

    def update(self):
        self.applications = self.ressource.getApplicationIdsAndNames(reload = True)
        for item in self.applicationlist:
            self.removeChild(item)
        self.applicationlist = []
        for app in self.applications:
            item = ApplicationItem(app[0], app[1], self.ressource)
            self.addChild(item)
            self.applicationlist.append(item)
        self.sortChildren(0, Qt.AscendingOrder)



class ApplicationItem(TreeItem):
    def __init__(self, id, name, ressource):
        TreeItem.__init__(self, None, name)
        self.actiontype = 'application'
        self.id = id
        self.name = name
        self.dlg = None
        self.ressource = ressource
        self.activeTools = []
        self.homeview = None
        self.settings = {
            'id' : 0,
            'name' : '',
            'description' : '',
            'language' : '',
            'open' : False,
            'active' : False,
            'activeTools' : [],
            }

    def createStaticSettings(self, iface):
        self.dlg = ApplicationSettingsDialog()
        self.dlg.setEditState(False)
        self.dlg.pushButtonOk.clicked.connect(self.dlg.hide)
        self.dlg.editCheckBox.clicked.connect(self.startEditing)
        self.dlg.pushButtonCancel.clicked.connect(self.stopEditing)

        self.iface = iface

        self.dlg.origExtentButton.clicked.connect(self.setOriginalExtent)
        self.dlg.qgsExtentButton.clicked.connect(lambda: self.setQgsExtent())
        self.dlg.jumpButtonOrig.clicked.connect(lambda: self.zoomToOrigExtent())

        self.dlg.homeviewZoomBox.valueChanged.connect(lambda: self.zoomToNewExtent())
        self.dlg.homeviewCenterEditX.textEdited.connect(lambda: self.zoomToNewExtent())
        self.dlg.homeviewCenterEditY.textEdited.connect(lambda: self.zoomToNewExtent())
        self.dlg.jumpButtonNew.clicked.connect(lambda: self.zoomToNewExtent())


    def setOriginalExtent(self):
        disableSignals = [self.dlg.homeviewZoomBox, self.dlg.homeviewCenterEditX]
        disableSignals.append(self.dlg.homeviewCenterEditY)
        disableSignals.append(self.dlg.jumpButtonNew)

        for qobject in disableSignals:
            qobject.blockSignals(True)

        self.dlg.homeviewCenterEditX.setText(str(self.homeview['mapconfig']['center']['x']))
        self.dlg.homeviewCenterEditY.setText(str(self.homeview['mapconfig']['center']['y']))
        self.dlg.homeviewZoomBox.setValue(self.homeview['mapconfig']['zoom'])
        self.populateExtentEdits(self.origExtRect)

        for qobject in disableSignals:
            qobject.blockSignals(False)


    def populateExtentEdits(self, extent):
        self.dlg.extentEdits[0].setText(str(extent.xMinimum()))
        self.dlg.extentEdits[1].setText(str(extent.yMinimum()))
        self.dlg.extentEdits[2].setText(str(extent.xMaximum()))
        self.dlg.extentEdits[3].setText(str(extent.yMinimum()))


    def setQgsExtent(self):
        rect = self.iface.mapCanvas().extent()
        self.populateExtentEdits(rect)
        center = self.iface.mapCanvas().center()
        self.dlg.homeviewCenterEditX.setText(str(center.x()))
        self.dlg.homeviewCenterEditY.setText(str(center.y()))

        zoom = self.iface.mapCanvas().mapUnitsPerPixel()
        #get shogun resolutions as enumerated list
        resolutions = list(enumerate(self.homeview['mapconfig']['resolutions']))
        cursor = resolutions[0]
        for res in resolutions:
            if abs(zoom - res[1]) < abs(zoom - cursor[1]):
                cursor = res
        # cursor is now the Shogun resolution closest to the qgis resolution

        self.dlg.homeviewZoomBox.setValue(cursor[0])


    def zoomToOrigExtent(self):
        #first set the original homeview center as the new canvas center
        center = self.homeview['mapconfig']['center']
        if PYTHON_VERSION >= 3:
            point = QgsPointXY(center['x'],center['y'])
        else:
            point = QgsPoint(center['x'],center['y'])
        self.iface.mapCanvas().setCenter(point)

        zoomlvl = self.homeview['mapconfig']['zoom']
        zoom = self.homeview['mapconfig']['resolutions'][zoomlvl]

        currentResolution = self.iface.mapCanvas().mapUnitsPerPixel()
        if currentResolution != zoom:
            diff = zoom/currentResolution
            self.iface.mapCanvas().zoomByFactor(diff)

        self.iface.mapCanvas().refresh()


    def zoomToNewExtent(self):
        x = float(self.dlg.homeviewCenterEditX.text())
        y = float(self.dlg.homeviewCenterEditY.text())
        if PYTHON_VERSION >= 3:
            point = QgsPointXY(x, y)
        else:
            point = QgsPoint(x, y)
        self.iface.mapCanvas().setCenter(point)

        zoomlvl = self.dlg.homeviewZoomBox.value()
        zoom = self.homeview['mapconfig']['resolutions'][zoomlvl]

        currentResolution = self.iface.mapCanvas().mapUnitsPerPixel()
        if currentResolution != zoom:
            diff = zoom/currentResolution
            self.iface.mapCanvas().zoomByFactor(diff)

        self.iface.mapCanvas().refresh()



    def populateSettings(self):
        # get application settings as a dict representing the json
        settings = self.ressource.getApplicationAttrsById(self.id)
        for attr in self.settings:
            self.settings[attr] = settings[attr]

        # set the general settings
        self.dlg.nameEdit.setText(settings['name'])
        self.dlg.descriptionEdit.setText(settings['description'])
        self.dlg.languageBox.setCurrentIndex(self.dlg.languageBox.findText(
            settings['language']))
        self.dlg.boxPublic.setChecked(settings['open'])
        self.dlg.boxActive.setChecked(settings['active'])


        # set the configured homeview
        self.mapConfigId = settings['viewport']['subModules'][0]['subModules'][0]['mapConfig']['id']
        self.extentId = settings['viewport']['subModules'][0]['subModules'][0]['mapConfig']['extent']['id']
        # getHomeviewByIds returns homeview as dict {'mapconfig':XY,'extent':XY}
        self.homeview = self.ressource.getHomeviewByIds(self.mapConfigId, self.extentId)

        self.dlg.homeviewZoomBox.setMaximum(len(self.homeview['mapconfig']['resolutions'])-1)
        origExtent = list(self.homeview['extent']['lowerLeft'].values())+list(self.homeview['extent']['upperRight'].values())
        self.origExtRect = QgsRectangle(origExtent[0],origExtent[1],origExtent[2],origExtent[3])
        self.setOriginalExtent()

        self.epsg = self.homeview['mapconfig']['projection']
        if PYTHON_VERSION >= 3:
            currentQgsCrs = QgsProject.instance().crs().authid()
        else:
            currentQgsCrs = self.iface.mapCanvas().mapRenderer().destinationCrs().authid()

        if self.epsg != currentQgsCrs:
            self.dlg.showEpsgWarning(currentQgsCrs, self.epsg)
        else:
            self.dlg.hideEpsgWarning()

        # set the application tools
        self.activeTools = [{'id' : tool['id']} for tool in settings['activeTools']]
        for tool in self.activeTools:
            self.dlg.tools[tool['id']].setChecked(True)

        # populate the layer tree and the table of available layers
        layerTree = settings['layerTree']
        self.dlg.layertreewidget.populateTree(layerTree)

        allLayers = self.ressource.getLayerIdsAndNames()
        self.dlg.layerlistwidget.populateList(allLayers)

        # populate the permissions tables
        self.userPermissions = self.ressource.getObjectPermissions(self.id, 'Application', 'User')
        self.groupPermissions = self.ressource.getObjectPermissions(self.id, 'Application', 'UserGroup')

        if not self.userPermissions['success'] or not self.groupPermissions['success']:
            self.dlg.noPermissionAccess()
        else:
            self.dlg.populateTable('users', self.userPermissions['data']['permissions'])
            self.dlg.populateTable('groups', self.groupPermissions['data']['permissions'])

    def getAllAppLayersById(self):
        rootConnectionItem = self.parent().parent()
        settings = self.ressource.getApplicationAttrsById(self.id)
        listOfIds = []
        layerTree = settings['layerTree']

        # for reasons of simplicity we only search for belonging layers down to the
        # third level of the tree
        if layerTree['leaf']:
            listOfIds.append(layerTree['layer']['id'])
            return listOfIds, rootConnectionItem
        else:
            children = layerTree['children']
            for child in children:
                if child['leaf']:
                    listOfIds.append(child['layer']['id'])
                else:
                    children = child['children']
                    for child in children:
                        if child['leaf']:
                            listOfIds.append(child['layer']['id'])
                        else:
                            children = child['children']
                            for child in children:
                                if child['leaf']:
                                    listOfIds.append(child['layer']['id'])
            return listOfIds, rootConnectionItem


    def getAllChanges(self):
        allChanges = {}
        if self.getGeneralChanges() is not None:
            allChanges['general'] = self.getGeneralChanges()

        if self.getActiveToolsChanges() is not None:
            if not 'general' in allChanges:
                allChanges['general'] = {}
            allChanges['general']['activeTools'] = self.getActiveToolsChanges()

        if self.getHomeViewChanges() is not None:
            allChanges['homeview'] = self.getHomeViewChanges()

        layerTreeChanges = self.dlg.layertreewidget.getLayerTreeChanges()
        if layerTreeChanges is not None:
            allChanges['layerTree'] = layerTreeChanges

        userPermissionChanges = self.getPermissionChanges('User')
        if userPermissionChanges is not None:
            allChanges['permissions'] = {'User' : userPermissionChanges}
        groupPermissionChanges = self.getPermissionChanges('UserGroup')
        if groupPermissionChanges is not None:
            if not 'permissions' in allChanges:
                allChanges['permissions'] = {}
            allChanges['permissions']['UserGroup'] = groupPermissionChanges

        return allChanges


    def getGeneralChanges(self):
        changes = {}
        if self.dlg.nameEdit.text() != self.settings['name']:
            changes['name'] = self.dlg.nameEdit.text()
        if self.dlg.descriptionEdit.text() != self.settings['description']:
            changes['description'] = self.dlg.descriptionEdit.text()
        if self.dlg.languageBox.currentText() != self.settings['language']:
            changes['languae'] = self.dlg.languageBox.currentText()
        if self.dlg.boxPublic.isChecked() != self.settings['open']:
            changes['open'] = self.dlg.boxPublic.isChecked()
        if self.dlg.boxActive.isChecked() != self.settings['active']:
            changes['active'] = self.dlg.boxActive.isChecked()

        if len(changes) == 0:
            return None
        else:
            return changes


    def getActiveToolsChanges(self):
        toolsCheckedInGui = []
        for toolid in self.dlg.tools.keys():
            if self.dlg.tools[toolid].isChecked():
                toolsCheckedInGui.append(toolid)

        #convert the lists to set for in case they have different orders
        if set(toolsCheckedInGui) != set([tool['id'] for tool in self.activeTools]):
            return [{'id': toolid} for toolid in toolsCheckedInGui]
        else:
            return None


    def getHomeViewChanges(self):
        zoom = self.dlg.homeviewZoomBox.value()
        x = float(self.dlg.homeviewCenterEditX.text())
        y = float(self.dlg.homeviewCenterEditY.text())
        conf = self.homeview['mapconfig']
        newhomeview = None

        if (conf['zoom'] != zoom or
            conf['center']['x'] != x or
            conf['center']['y'] != y):
            newhomeview = {
            'id': self.homeview['mapconfig']['id'], 'zoom': zoom,
            'center':{'x':x, 'y':y} }
        return newhomeview


    def getPermissionChanges(self, type):
        if type == 'User':
            permissions = self.userPermissions['data']
            table = self.dlg.usertabel
        elif type == 'UserGroup':
            permissions = self.groupPermissions['data']
            table = self.dlg.groupstabel
        else:
            return
        oldPermissionList = permissions['permissions']
        newPermissionList = []
        for entry in oldPermissionList:
            name = entry['displayTitle']
            row = None
            for x in range(table.rowCount()):
                if table.verticalHeaderItem(x).text() == name:
                    row = x
                    break
            if row is None:
                return

            currentPermissionsInTable = []
            for p in enumerate(['READ', 'UPDATE', 'DELETE']):
                if table.item(row, p[0]).checkState() == 2:
                    currentPermissionsInTable.append(p[1])

            if entry['permissions'] == None:
                oldPermissions = []
            else:
                oldPermissions = entry['permissions']['permissions']
                if oldPermissions == ['ADMIN']:
                    oldPermissions = ['READ', 'UPDATE', 'DELETE']

            if set(currentPermissionsInTable) != set(oldPermissions):
                newEntry = {
                    'targetEntity' : permissions['targetEntity'],
                    'permissions' : [{
                        'permissions' : {
                            'permissions' : currentPermissionsInTable
                            },
                        'targetEntity' : entry['targetEntity']
                        }]
                    }
                newPermissionList.append(newEntry)
        if len(newPermissionList) == 0:
            newPermissionList = None
        return newPermissionList


    def startEditing(self):
        self.dlg.setEditState(True)
        self.dlg.editCheckBox.clicked.disconnect(self.startEditing)
        self.dlg.pushButtonOk.clicked.disconnect(self.dlg.hide)
        self.dlg.editCheckBox.clicked.connect(self.stopEditing)
        self.dlg.pushButtonOk.clicked.connect(self.saveChanges)


    def stopEditing(self):
        changes = self.getAllChanges()
        print(changes)
        if len(changes) > 0:
            warn = QMessageBox.warning(self.dlg, 'Warning','All changes will be'
                ' lost. Continue?', QMessageBox.Cancel, QMessageBox.Ok)
            if warn == QMessageBox.Ok:
                self.populateSettings()
            else:
                self.dlg.editCheckBox.setChecked(True)
                return
        self.stoppedEditing()


    def saveChanges(self):
        changes = self.getAllChanges()
        if len(changes) > 0:
            print(changes)
            conf = QMessageBox.warning(self.dlg, 'Confirm', 'Please confirm you'
                ' want to save the changes', QMessageBox.Cancel, QMessageBox.Ok)
            if conf == QMessageBox.Ok:
                if 'general' in changes:
                    #'changes' will be sent as the data, therefore append the id
                    #as a key, so that the data will be recognized
                    changes['general']['id'] = self.id
                    responseCode = self.ressource.editApplication(self.id,
                        changes['general'])
                    #update the name in the tree view:
                    if 'name' in changes['general'] and responseCode > 199 and responseCode < 299:
                        self.name = changes['general']['name']
                        self.setText(0, self.name)

                if 'homeview' in changes:
                    self.ressource.editMapConfig(
                        self.mapConfigId, changes['homeview'])

                    #update the homeview after the changes
                    self.ressource.updateExtentsAndMapConfigs()
                    self.homeview = self.ressource.getHomeviewByIds(
                            self.mapConfigId, self.extentId)

                if 'layerTree' in changes:
                    deletedItemIds = changes['layerTree']['deleteItems']
                    responses = []
                    if len(deletedItemIds) > 0:
                        for id in deletedItemIds:
                            responses.append(self.ressource.deleteLayerTreeItem(id))
                    newItems = changes['layerTree']['newItems']
                    if len(newItems) > 0:
                        for item in newItems:
                            responses.append(self.ressource.createLayerTreeItem(item))
                    changeItems = changes['layerTree']['changeItems']
                    if len(changeItems) > 0:
                        for item in changeItems:
                            id = item['id']
                            responses.append(
                                self.ressource.updateLayerTreeItem(id, item))
                    res = 200
                    for x in responses:
                        if not 199 < x < 210:
                            res = x
                    self.ressource.userInfo(res, 'Layertree', 'updated')

                if 'permissions' in changes:
                    responses = 200
                    for x in changes['permissions'].keys():
                        for entry in changes['permissions'][x]:
                            responseBool = self.ressource.editObjectPermission(
                                self.id, 'ProjectApplication', x, entry)
                            if not responseBool:
                                responses = 400

                    self.userPermissions = self.ressource.getObjectPermissions(
                            self.id, 'Application', 'User')
                    self.groupPermissions = self.ressource.getObjectPermissions(
                            self.id, 'Application', 'UserGroup')
                    self.ressource.userInfo(responses,
                        'Application permissions', 'updated')

                #update the class internal copy of the general settings
                newSettings = self.ressource.updateSingleApplication(self.id)
                for attr in self.settings:
                    self.settings[attr] = newSettings[attr]
                self.dlg.layertreewidget.populateTree(newSettings['layerTree'])
            # if the user clicked 'cancel', just return and stay in edit mode:
            else:
                return

        else:
            info = QMessageBox.information(self.dlg, 'Note',
                'No changes were found', QMessageBox.Ok)
        self.stoppedEditing()


    def stoppedEditing(self):
        self.dlg.editCheckBox.clicked.disconnect(self.stopEditing)
        self.dlg.pushButtonOk.clicked.disconnect(self.saveChanges)
        self.dlg.pushButtonOk.clicked.connect(self.dlg.hide)
        self.dlg.editCheckBox.clicked.connect(self.startEditing)
        self.dlg.editCheckBox.setChecked(False)
        self.dlg.setEditState(False)


    def deleteApplication(self):
        txt = 'Please confirm you want to permanently delete '
        txt += 'the selected application in Shogun'
        conf = QMessageBox.warning(self.dlg, 'Confirm',txt , QMessageBox.Cancel, QMessageBox.Ok)
        if conf == QMessageBox.Ok:
            self.ressource.deleteApplication(self.id)
            self.ressource.updateApplications()
            self.parent().update()


    def copyApplication(self):
        self.ressource.copyApplication(self.id, self.name)
        self.parent().update()


class LayersItem(TreeItem):
    def __init__(self, ressource):
        TreeItem.__init__(self, 'layers-logo.png', 'Layers')
        self.ressource = ressource
        self.layers = self.ressource.getLayerIdsAndNames()
        self.layerlist = []
        self.actiontype = 'layersItem'
        font = QFont('Arial',10)
        font.setBold(True)
        self.setFont(0,font)
        self.populate()

    def populate(self):
        for layer in self.layers:
            item = LayerItem(layer[0], layer[1], layer[2], layer[3], self.ressource)
            self.addChild(item)
            self.layerlist.append(item)
        self.sortChildren(0, Qt.AscendingOrder)

    def update(self):
        #update the list of current shogun layers:
        self.layers = self.ressource.getLayerIdsAndNames(reload = True)
        layerIdList = [layer[0] for layer in self.layers]
        #remove every item that is not in the updated list:
        for layer in self.layerlist:
            if layer.id not in layerIdList:
                self.removeChild(layer)
                self.layerlist.remove(layer)

        #check if new layers appeared and append them:
        currentLayerIdList = [layer.id for layer in self.layerlist]
        for layer in self.layers:
            if layer[0] not in currentLayerIdList:
                item = LayerItem(layer[0], layer[1], layer[2], layer[3], self.ressource)
                self.addChild(item)
                self.layerlist.append(item)
        self.sortChildren(0, Qt.AscendingOrder)



    def createNewLayer(self, iface):
        self.uploadDialog = UploadLayerDialog()
        #mapLayers = QgsMapLayerRegistry.instance().mapLayers().values()
        #self.uploadDialog.layerBox.addItems([layer.name() for layer in mapLayers])
        self.uploadDialog.uploadButton.clicked.connect(self.uploadLayerAction)
        self.uploadDialog.show()

    def uploadLayerAction(self):
        layer = self.uploadDialog.layerBox.currentLayer()
        print("current layer is:", layer)
        # layerutils
        pathToZipFile, pathToTempDir = prepareLayerForUpload(layer, self.uploadDialog)
        print("over")
        if pathToZipFile:
            if layer.type() == QgsMapLayer.VectorLayer:
                type = 'Vector'
            else:
                if layer.providerType() == 'wms':
                    success = self.ressource.publishWmsLayer()
                    if success:
                        self.uploadDialog.log('WMS layer ' + layer.name() + ''
                            'was successfully published')
                        self.update()
                    else:
                        self.uploadDialog.log('Publishing WMS '
                            'layer ' + layer.name() + ' was not successfull')

                    return

                else:
                    type = 'Raster'
            success = self.ressource.uploadLayer(pathToZipFile, type)
            if success:
                self.uploadDialog.log('Layer ' + layer.name() + ' was successfully uploaded')
                self.update()
            else:
                self.uploadDialog.log('Uploading layer ' + layer.name() + ' was not successfull')
            # after the process has finished we delete the created zipfile and
            # temporary directory for cleaning up
            try:
                os.remove(pathToZipFile)
                os.rmdir(pathToTempDir)
            except:
                pass



class LayerItem(TreeItem):
    def __init__(self, id, name, datatype, source, ressource):

        # unfortunately there is no option to retrieve the layer geometry (i. e.
        # point/line/polygon for vectorlayers) just from the json object.
        # Therefore they get a default polygon icon which will be updated as soon as
        # layer is added as WFS to QGIS - see def addQgsLayer()
        if datatype == 'Raster':
            self.icon = QgsLayerItem.iconRaster()
        elif datatype == 'Vector':
            self.icon = QgsLayerItem.iconPolygon()
        else:
            self.icon = QgsLayerItem.iconDefault()
        TreeItem.__init__(self, self.icon, name)
        self.id = id
        self.actiontype = 'layer'
        self.ressource = ressource
        self.dlg = None
        self.name = name
        self.source = source
        self.datatype = datatype
        self.qgisLayers = []
        self.settings = {
            'name' : '',
            'appearance' : {
                'hoverTemplate' : None,
                'opacity' : 1
            }
        }
        if PYTHON_VERSION >= 3:
            QgsProject.instance().layerRemoved.connect(self.updateLayerList)
        else:
            QgsMapLayerRegistry.instance().layerRemoved.connect(self.updateLayerList)


    def updateLayerList(self):
        if self.qgisLayers == []:
            return
        if PYTHON_VERSION >= 3:
            currentMapLayers = QgsProject.instance().mapLayers()
        else:
            currentMapLayers = QgsMapLayerRegistry.instance().mapLayers()
        for qgisLayerItem in self.qgisLayers:
            if qgisLayerItem.id not in currentMapLayers:
                self.qgisLayers.remove(qgisLayerItem)
                self.removeChild(qgisLayerItem)


    def addQgsLayer(self, iface):
        currentCrs = iface.mapCanvas().mapSettings().destinationCrs()
        if currentCrs.isValid():
            epsg = currentCrs.authid()
        else:
            epsg = 'EPSG:3857'
        # layerutils
        layer = createLayer(self, epsg)
        if not layer:
            return
        qgisLayerItem = QgisLayerItem(layer, self, self.ressource)
        self.qgisLayers.append(qgisLayerItem)
        self.addChild(qgisLayerItem)
        self.setExpanded(True)

        #for an odd reason there appears a warning below the layer if it is a
        #wms layer from shogun - workaround to hide this:
        if layer.dataProvider().name() == 'wms' and self.source['url'].startswith('/shogun2-webapp/'):
            root = QgsProject.instance().layerTreeRoot()
            layerNode = root.findLayer(layer.id())
            layerNode.setExpanded(False)

        # when the layer has loaded for the first time and it's icon
        # is still on iconDefault, update the icon with the correct geometry
        if not self.datatype == 'Raster':
            if layer.type() == QgsMapLayer.VectorLayer:
                geom = layer.geometryType()
                if PYTHON_VERSION >= 3:
                    if geom == QgsWkbTypes.PointGeometry:
                        self.icon = QgsLayerItem.iconPoint()
                    elif geom == QgsWkbTypes.LineGeometry:
                        self.icon = QgsLayerItem.iconLine()
                    elif geom == QgsWkbTypes.PolygonGeometry:
                        self.icon = QgsLayerItem.iconPolygon()
                else:
                    if geom == QGis.Point:
                        self.icon = QgsLayerItem.iconPoint()
                    elif geom == QGis.Line:
                        self.icon = QgsLayerItem.iconLine()
                    elif geom == QGis.Polygon:
                        self.icon = QgsLayerItem.iconPolygon()
            else:
                self.icon = QgsLayerItem.iconRaster()
            self.setIcon(0, self.icon)


    def createStaticSettings(self):
        self.dlg = LayerSettingsDialog()
        self.dlg.setEditState(False)
        self.dlg.pushButtonOk.clicked.connect(self.normalClose)
        self.dlg.editCheckBox.clicked.connect(self.startEditing)
        self.dlg.pushButtonCancel.clicked.connect(self.stopEditing)
        if self.datatype == 'Vector' or self.datatype == '':
            fieldNames = self.ressource.getFieldNamesFromWfs(self.source['layerNames'])
            if fieldNames:
                self.dlg.hoverBox.addItems(fieldNames)
        else:
            self.dlg.deactivateHoverEditing()


    def populateSettings(self):
        settings = self.ressource.getLayerAttrsById(self.id)
        for attr in self.settings:
            self.settings[attr] = settings[attr]

        self.dlg.nameEdit.setText(settings['name'])

        opac = settings['appearance']['opacity']
        if opac is None:
            opac = 0
        self.dlg.sliderEdit.setText(str(opac))
        self.dlg.slider.setValue(int(opac * 100))
        if settings['appearance']['hoverTemplate'] is not None:
            self.dlg.hoverEdit.setText(settings['appearance']['hoverTemplate'])

        self.userPermissions = self.ressource.getObjectPermissions(self.id, 'Layer', 'User')
        self.groupPermissions = self.ressource.getObjectPermissions(self.id, 'Layer', 'UserGroup')

        if not self.userPermissions['success'] or not self.groupPermissions['success']:
            self.dlg.noPermissionAccess()
        else:
            self.dlg.populateTable('users', self.userPermissions['data']['permissions'])
            self.dlg.populateTable('groups', self.groupPermissions['data']['permissions'])


    def getPermissionChanges(self, type):
        if type == 'User':
            permissions = self.userPermissions['data']
            table = self.dlg.usertabel
        elif type == 'UserGroup':
            permissions = self.groupPermissions['data']
            table = self.dlg.groupstabel
        else:
            return
        oldPermissionList = permissions['permissions']
        newPermissionList = []
        for entry in oldPermissionList:
            name = entry['displayTitle']
            row = None
            for x in range(table.rowCount()):
                if table.verticalHeaderItem(x).text() == name:
                    row = x
                    break
            if row is None:
                return

            currentPermissionsInTable = []
            for p in enumerate(['READ', 'UPDATE', 'DELETE']):
                if table.item(row, p[0]).checkState() == 2:
                    currentPermissionsInTable.append(p[1])

            if entry['permissions'] == None:
                oldPermissions = []
            else:
                oldPermissions = entry['permissions']['permissions']
                if oldPermissions == ['ADMIN']:
                    oldPermissions = ['READ', 'UPDATE', 'DELETE']

            if set(currentPermissionsInTable) != set(oldPermissions):
                newEntry = {
                    'targetEntity' : permissions['targetEntity'],
                    'permissions' : [{
                        'permissions' : {
                            'permissions' : currentPermissionsInTable
                            },
                        'targetEntity' : entry['targetEntity']
                        }]
                    }
                newPermissionList.append(newEntry)
        if len(newPermissionList) == 0:
            newPermissionList = None
        return newPermissionList


    def getAllChanges(self):
        changes = {}
        generalChanges = self.getGeneralChanges()
        if generalChanges is not None:
            changes['general'] = generalChanges
        userPermissionChanges = self.getPermissionChanges('User')
        if userPermissionChanges is not None:
            changes['permissions'] = {'User' : userPermissionChanges}
        groupPermissionChanges = self.getPermissionChanges('UserGroup')
        if groupPermissionChanges is not None:
            if not 'permissions' in changes:
                changes['permissions'] = {}
            changes['permissions']['UserGroup'] = groupPermissionChanges

        if len(changes) == 0:
            return None
        else:
            return changes


    def getGeneralChanges(self):
        changes = {}
        if self.dlg.nameEdit.text() != self.settings['name']:
            changes['name'] = self.dlg.nameEdit.text()
        if float(self.dlg.sliderEdit.text()) != self.settings['appearance']['opacity']:
            changes['appearance'] = {}
            changes['appearance']['opacity'] = float(self.dlg.sliderEdit.text())
        hoverInput = self.dlg.hoverEdit.text()
        if len(hoverInput) == 0:
            hoverInput = None
        if hoverInput != self.settings['appearance']['hoverTemplate']:
            if not 'appearance' in changes:
                changes['appearance'] = {}
            changes['appearance']['hoverTemplate'] = self.dlg.hoverEdit.text()

        if len(changes) == 0:
            return None
        else:
            return changes

    def startEditing(self):
        self.dlg.setEditState(True)
        self.dlg.editCheckBox.clicked.disconnect(self.startEditing)
        self.dlg.pushButtonOk.clicked.disconnect(self.normalClose)
        self.dlg.editCheckBox.clicked.connect(self.stopEditing)
        self.dlg.pushButtonOk.clicked.connect(self.saveChanges)

    def stopEditing(self):
        changes = self.getAllChanges()
        if changes is not None:
            warn = QMessageBox.warning(self.dlg, 'Warning','All changes will be'
                ' lost. Continue?', QMessageBox.Cancel, QMessageBox.Ok)
            if warn == QMessageBox.Ok:
                self.populateSettings()
            else:
                self.dlg.editCheckBox.setChecked(True)
                return
        self.stoppedEditing()

    def saveChanges(self):
        changes = self.getAllChanges()
        if changes is not None:
            conf = QMessageBox.warning(self.dlg, 'Confirm','Please confirm you '
                'want to save the changes', QMessageBox.Cancel, QMessageBox.Ok)
            if conf == QMessageBox.Ok:
                if 'general' in changes:
                    data = changes['general']
                    data['id'] = self.id
                    responseCode = self.ressource.editLayer(self.id, data)
                    if 'name' in data and responseCode > 199 and responseCode < 299:
                        self.name = data['name']
                        self.setText(0, self.name)

                    #update the settings of the class:
                    newSettings = self.ressource.updateSingleLayer(self.id)
                    for attr in self.settings:
                        self.settings[attr] = newSettings[attr]
                if 'permissions' in changes:
                    responses = 200
                    for x in changes['permissions'].keys():
                        for entry in changes['permissions'][x]:
                            responseBool = self.ressource.editObjectPermission(
                                self.id, 'ProjectLayer', x, entry)
                            if not responseBool:
                                responses = 400

                    # update the class variable copy of the permissions
                    self.userPermissions = self.ressource.getObjectPermissions(
                            self.id, 'Layer', 'User')
                    self.groupPermissions = self.ressource.getObjectPermissions(
                            self.id, 'Layer', 'UserGroup')
                    self.ressource.userInfo(responses, 'Layer permissions', 'updated')

            # if the user clicked 'cancel' just return and stay in edit mode:
            else:
                return
        else:
            QMessageBox.information(self.dlg, 'Note','No changes were found',
                QMessageBox.Ok)
        self.stoppedEditing()

    def stoppedEditing(self):
        self.dlg.editCheckBox.clicked.disconnect(self.stopEditing)
        self.dlg.pushButtonOk.clicked.disconnect(self.saveChanges)
        self.dlg.pushButtonOk.clicked.connect(self.normalClose)
        self.dlg.editCheckBox.clicked.connect(self.startEditing)
        self.dlg.editCheckBox.setChecked(False)
        self.dlg.setEditState(False)

    def normalClose(self):
        self.dlg.hide()

    def deleteLayer(self):
        txt = 'Please confirm you want to permanently delete the selected layer in Shogun'
        conf = QMessageBox.warning(self.dlg, 'Confirm',txt , QMessageBox.Cancel, QMessageBox.Ok)
        if conf == QMessageBox.Ok:
            self.ressource.deleteLayer(self.id)
            self.parent().update()



class QgisLayerItem(TreeItem):
    def __init__(self, qgislayer, shogunLayerItem, ressource):
        TreeItem.__init__(self, None, qgislayer.name())
        self.layer = qgislayer
        self.id = self.layer.id()
        self.type = self.layer.type()
        self.stylename = None
        #make upload and download Style only available for vector layers:
        if self.type == 0:
            self.actiontype = 'qgisLayerReference'
        else:
            self.actiontype = None
        self.parentShogunLayer = shogunLayerItem
        self.ressource = ressource
        if PYTHON_VERSION >= 3:
            QgsProject.instance().addMapLayer(self.layer)
        else:
            QgsMapLayerRegistry.instance().addMapLayer(self.layer)
        if self.layer.type() == QgsMapLayer.VectorLayer:
            self.downloadStyle()
        self.layer.nameChanged.connect(self.on_name_changed)


    def uploadStyle(self):
        msg = 'Please confirm that you want to upload the style of the selected'
        msg += ' layer and overwrite the style of the corresponding layer in Shogun'
        confirm = QMessageBox.warning(None, 'Confirm', msg, QMessageBox.Cancel, QMessageBox.Ok)
        if not confirm:
            return
        else:
            return self.ressource.uploadStyle(self)


    def downloadStyle(self):
        sld, geoServerStyleName = self.ressource.downloadStyle(self)
        self.stylename = geoServerStyleName
        if sld is not None:
            self.layer.loadSldStyle(sld)
            self.layer.triggerRepaint()
            return True
        else:
            return False


    def uploadIcon(self):
        self.ressource.uploadCustomIcon(self.layer.rendererV2().symbol().symbolLayer(0))

    def on_name_changed(self):
        self.setText(0, self.layer.name())
