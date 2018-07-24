# -*- coding: utf-8 -*-
'''
(c) 2018 terrestris GmbH & Co. KG, https://www.terrestris.de/en/
 This code is licensed under the GPL 2.0 license.
'''

__author__ = 'Jonas Grieb'
__date__ = 'July 2018'

import sys
from base64 import b64encode
import urllib
import json
import os
import webbrowser

if sys.version_info[0] >= 3:
    from qgis.PyQt.QtGui import QIcon
    from qgis.PyQt.QtXml import QDomDocument
    from qgis.PyQt.QtNetwork import QNetworkRequest, QHttpPart, QHttpMultiPart
    from qgis.PyQt.QtCore import QFile, QIODevice, QSize
else:
    from PyQt4.QtGui import QIcon
    from PyQt4.QtXml import QDomDocument
    from PyQt4.QtNetwork import QNetworkRequest, QHttpMultiPart, QHttpPart
    from PyQt4.QtCore import QFile, QIODevice, QSize

from qgis.core import QgsApplication
from qgis.gui import QgsMessageBar

from .networkaccessmanager import NetworkAccessManager, RequestsExceptionConnectionError, RequestsException
from shoguneditor.layerutils import createAndParseSld


PYTHON_VERSION = sys.version_info[0]

class ShogunRessource:
    ''' This class controls all interactions between QGIS and the Shogun ressource,
    apart from creating wfs/wms layers (see layerutils for this). It makes use of the
    class NetworkAccessManager, which calls QgsNetworkAccessManager for all http
    requests'''

    def __init__(self, iface, url, name, user = None, pw = None):
        self.iface = iface
        if url.endswith('webapp'):
            url+='/'
        elif url.endswith('rest/'):
            url = url[:-5]
        elif url.endswith('rest'):
            url = url[:-4]

        self.baseurl = url      #url should have the format: 'https:.../shogun2-webapp/'
        self.name = name
        self.applications = []
        self.layers = []
        self.mapconfigs = []
        self.extents = []
        self.http = NetworkAccessManager(debug = False)

        self.icondir =  os.path.join(os.path.dirname(__file__), '..', 'images', 'custom-symbols')
        if not os.path.isdir(self.icondir):
            os.makedirs(self.icondir)


        if user is not None and pw is not None:
            if PYTHON_VERSION >= 3:
                bytes = (user + ':' + pw).encode('utf-8')
                self.basicauth = b64encode(bytes)
                self.http.setBasicauth('Basic '.encode('utf-8') + self.basicauth)
            else:
                self.basicauth = b64encode(user + ':' + pw)
                self.http.setBasicauth('Basic ' + self.basicauth)


    def checkConnection(self):
    # returning a tuple of ('true/false', 'message')

    # # TODO: here we check only the cases of http/https faults in the user's
    #  input. Maybe there should be more error checks for in case the user has
    #  written an url which is completely different (no http/ https at beginning)

        testurl = self.baseurl + 'rest/applications'
        try:
            testresponse = self.http.request(testurl, method = 'HEAD')
            if testresponse[0]['status'] > 199 and testresponse[0]['status'] < 210:
                return (True, '')
        except RequestsException as e:
            if self.baseurl.startswith('https'):
            # if the first try with 'https' was not successfull try http:
                testurl = 'http' + testurl[5:]
                try:
                    testresponse = self.http.request(testurl, method = 'HEAD')
                    if testresponse[0]['status'] > 199 and testresponse[0]['status'] < 210:
                        self.baseurl = 'http' + self.baseurl[5:]
                        return (True, '')
                except RequestsException as e:
                    pass
        return (False, 'Error : Failed to connect to the server')



    def userInfo(self, status, objectName, method):
        #method = 'created'/'updated'/'deleted'
        if status > 199 and status < 300:
            msg = objectName + ' was successfully ' + method
            self.iface.messageBar().pushSuccess('Shogun Editor Info:', msg)
        else:
            msg = 'Error: ' + objectName + ' could not be ' + method
            self.iface.messageBar().pushCritical('Shogun Editor Info:', msg)


    def editApplication(self, id, data):
        data = json.dumps(data)
        url = self.baseurl + 'rest/applications/' +str(id)
        header = {'Content-type':'application/json'}
        response = self.http.request(url, method='PUT', body = data, headers = header)
        self.userInfo(response[0]['status'], 'Application', 'edited')
        return response[0]['status']


    def editLayer(self, id, data):
        data = json.dumps(data)
        url = self.baseurl + 'rest/layers/' +str(id)
        header = {'Content-type':'application/json'}
        response = self.http.request(url, method='PUT', body = data, headers = header)
        self.userInfo(response[0]['status'], 'Layer', 'edited')
        return response[0]['status']


    def uploadNewApplication(self, data):
    #data as a json-like dict
        url = self.baseurl + 'projectapps/create.action'
        header = {'Content-type' : 'application/json'}
        body = json.dumps(data)
        response = self.http.request(url, method='POST', body = body, headers = header)
        name = 'Application ' + data['name']
        self.userInfo(response[0]['status'], name, 'created')
        if response[0]['status'] == 200 or response[0]['status'] == 201:
            return True
        else:
            return False


    def editMapConfig(self, id, data):
        edit = None
        for mapconfig in self.mapconfigs:
            if mapconfig['id'] == id:
                edit = mapconfig

        url = self.baseurl+'mapconfigs/'+str(id)
        body = '{"id":'+str(id)+',"center":{"x":'+str(data['center']['x'])+',"y":'
        body += str(data['center']['y'])+'},"zoom":'+str(data['zoom'])+'}'
        h = {'Content-type':'application/json'}
        response = self.http.request(url, method='PUT', body = body, headers = h)
        self.userInfo(response[0]['status'], 'Homeview', 'updated')

    def editObjectPermission(self, id, objectType, permissionType, data):
        url = self.baseurl + 'rest/entitypermission/' + objectType + '/' + str(id)
        if permissionType == 'User':
            url += '/ProjectUser'
        elif permissionType == 'UserGroup':
            url += '/ProjectUserGroup'
        else:
            return

        header = {'Content-type' : 'application/json'}
        body = json.dumps(data)
        response = self.http.request(url, method='POST', body = body, headers = header)
        if response[0]['status'] == 200 or response[0]['status'] == 201:
            return True
        else:
            return False

    def updateData(self):
        try:
            self.updateApplications()
            self.updateLayers()
            self.updateExtentsAndMapConfigs()
            return True
        except RequestsExceptionConnectionError:
            self.iface.messageBar().pushCritical('Connection Error:',
            'Could not connect to given SHOGUN host application - Please review url')
            return False

    def updateApplications(self):
        url = self.baseurl + 'rest/applications'
        response = self.http.request(url)
        self.applications = json.loads(response[1])

    def updateLayers(self):
        url = self.baseurl + 'rest/layers'
        response = self.http.request(url)
        self.layers = json.loads(response[1])

    def updateSingleApplication(self, id):
        url = self.baseurl + 'rest/applications/' + str(id)
        response = self.http.request(url)
        updatedApplication = json.loads(response[1])
        for app in enumerate(self.applications):
            if app[1]['id'] == id:
                self.layers[app[0]] = updatedApplication
        return updatedApplication

    def updateSingleLayer(self, id):
        url = self.baseurl + 'rest/layers/' + str(id)
        response = self.http.request(url)
        updatedLayer = json.loads(response[1])
        for layer in enumerate(self.layers):
            if layer[1]['id'] == id:
                self.layers[layer[0]] = updatedLayer
        return updatedLayer

    #one method for retrieving user and groups permissions (permissionType)
    #for layers or applications (objectType)
    def getObjectPermissions(self, id, objectType, permissionType):
        url = self.baseurl + 'rest/entitypermission/Project' + objectType
        # objectType = 'Application' or 'Layer'
        # permissionType = 'User' or 'UserGroup'
        url += '/'+ str(id) + '/Project' + permissionType + '?'
        response = self.http.request(url)
        return json.loads(response[1])


    def updateExtentsAndMapConfigs(self):
        url = self.baseurl + 'rest/extents'
        response = self.http.request(url)
        self.extents = json.loads(response[1])
        url = self.baseurl + 'rest/mapconfigs'
        response = self.http.request(url)
        self.mapconfigs = json.loads(response[1])

    def getHomeviewByIds(self, mapconfigid, extentid):
        homeview = {}
        for mapcf in self.mapconfigs:
            if mapcf['id'] == mapconfigid:
                homeview['mapconfig']=mapcf
        for ext in self.extents:
            if ext['id'] == extentid:
                homeview['extent']=ext
        return homeview

    def getApplicationIdsAndNames(self, reload = False):
        if reload:
            self.updateApplications()
        return [(x['id'], x['name']) for x in self.applications]

    def getLayerIdsAndNames(self, reload = False):
        if reload:
            self.updateLayers()
        return [(x['id'], x['name'], x['dataType'], x['source']) for x in self.layers]

    def getApplicationAttrsById(self, id):
       for x in self.applications:
           if x['id'] == id:
               return x

    def getLayerAttrsById(self, id):
        for x in self.layers:
            if x['id'] == id:
                return x

    def getGroupNames(self):
        return [x['name'] for x in self.groups]

    def getUserNames(self):
        return [(x['lastName']+', '+x['firstName']) for x in self.users]


    def downloadStyle(self, qgisLayerItem):
        #this downloads the layer's style, saves it as an sld and returns two
        #things: 1. the path to the .sld, 2. the specific name of the style
        #as it is saved in the background geoserver from shogun, obtained from
        #the xml-node sld:UserStyle - sld:Name
        #the specific name is later needed for re-uploading the edited style


        ## TODO:
        # maybe a better implementation would be to pass the QDomDocument directly
        # to the layer and set it's style from sld...

        # unfortunately for a not known reason this does not work and we first
        # have to save the sld to a file, then do layer.loadSldStyle(file)
        # can someone fix it?#


        shogunlayer = qgisLayerItem.parentShogunLayer
        url = shogunlayer.source['url']
        if url.startswith('/shogun2-webapp'):
            url = self.baseurl.rstrip('/shogun2-webapp/rest/') + url
            url += '?service=WMS&request=GetStyles&version=1.1.1&layers='
            url += shogunlayer.source['layerNames']
        response = self.http.request(url)

        mydoc = QDomDocument()
        mydoc.setContent(response[1])
        root = mydoc.firstChildElement('sld:StyledLayerDescriptor')
        namedLayerNode = root.firstChildElement('sld:NamedLayer')
        userStyleNode = namedLayerNode.firstChildElement('sld:UserStyle')
        sldNameNode = userStyleNode.firstChildElement('sld:Name')
        geoServerStyleName = sldNameNode.text()

        # # TODO: implement more than point style
        # check if custom icons are used in the style:

        # # NOTE: this is the beginning of a larger implementation of
        # exchange of icons
        # problem is that shogun2 only serves png icons, and qgis needs
        # svg to turn them into a style


        if '<sld:ExternalGraphic>' in response[1]:
            self.iface.messageBar().pushInfo('Info',
            'The downloaded style for the current layer contains custom icons '
            'from SHOGUN, which only serves them as PNG pictures, but QGIS '
            'can only read SVG. Until this is fixed, you see a default QGIS '
            'style for the layer')

        '''
            featureTypeStyleNode = userStyleNode.firstChildElement('sld:FeatureTypeStyle')
            rules = featureTypeStyleNode.elementsByTagName('sld:Rule')
            for x in range(rules.length()):
                rule = rules.at(x).toElement()
                listOfGraphics = rule.elementsByTagName('sld:OnlineResource')
                    for x in range(listOfGraphics.length()):
                        graphicNode = listOfGraphics(x)
                        attributes = graphicNode.attributes()
                        url = attributes.namedItem('xlink:href').nodeValue()
                        id = url.split('getThumbnail.action?id=')[1]
                        iconPath = self.downloadIconThumbnail(id)
        '''

        dirpath = os.path.dirname(__file__)
        filename = os.path.join(dirpath, 'latest-symbology.sld')
        with open(filename, 'w') as file:
            file.write(response[1])
        return filename, geoServerStyleName


    def uploadStyle(self, qgisLayerItem):
        url = self.baseurl.rstrip('rest/') + '/sld/update.action'
        h = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        sld = createAndParseSld(qgisLayerItem)
        b = 'sld=' + sld + '&sldName=' + qgisLayerItem.stylename + '&layerId='
        b += str(qgisLayerItem.parentShogunLayer.id)
        response = self.http.request(url, method = 'POST', body = b, headers = h)
        if json.loads(response[1])['success']:
            return True
        else:
            return False


    def prepareIconForUpload(self, svgIconName):
        svgPaths = QgsApplication.svgPaths()
        svgIconPath = None
        for dir in svgPaths:
            if os.path.isfile(os.path.join(dir, svgIconName)):
                svgIconPath = os.path.join(dir, svgIconName)
        if svgIconPath is None or not svgIconPath.endswith('svg'):
            return False
        name = os.path.splitext(svgIconName)[0]
        outputPath = os.path.join(self.icondir, 'qgis-' + name +'.png')
        img = QIcon(svgIconPath).pixmap(QSize(100,100)).toImage()
        if img.save(outputPath):
            newId = self.uploadImage(outputPath)
            if newId:
                iconUrl = self.baseurl + 'projectimage/getThumbnail.action?id='
                iconUrl += str(newId)
                return iconUrl
        self.userInfo(400, 'Custom symbology icon', 'uploaded')
        return False


    # # NOTE: the following method is still not used:
    def downloadIconThumbnail(self, id):
        iconPath = os.path.join(self.icondir, str(icon['id']) + '.png')
        if os.path.isfile(iconPath):
            return iconPath
        else:
            url = self.baseurl + 'projectimage/getThumbnail.action?id=' + str(id)
            urlretrieve(url, iconPath)
            return iconPath


    def uploadImage(self, pathToImage):
        img = QFile(pathToImage)
        img.open(QIODevice.ReadOnly)
        imgPart = QHttpPart()
        txt = 'form-data; name="file"; filename="' + os.path.basename(pathToImage) + '"'
        imgPart.setHeader(QNetworkRequest.ContentDispositionHeader, txt)
        imgPart.setHeader(QNetworkRequest.ContentTypeHeader, 'image/zip')
        imgPart.setBodyDevice(img)

        multiPart = QHttpMultiPart(QHttpMultiPart.FormDataType)
        multiPart.append(imgPart)

        url = self.baseurl + 'projectimage/upload.action?'

        response = self.http.request(url, method = 'POST', body = multiPart)
        if response[0]['status'] > 199 and response[0]['status'] < 210:
            # if icon upload was successfull, server returns id of the new icon
            # in it's database
            id = json.loads(response[1])['data']['id']
            return id
        else:
            return False



    def publishWmsLayer(self, wmsUri):
        url = self.baseurl + '/ogcservicehelper/publishlayer.action?'
        url += wmsUri
        #header = {'Cookie': self.cookie}
        response = self.http.request(url, method = 'GET')
        self.userInfo(response[0]['status'], 'New WMS layer', 'published')


    def uploadLayer(self, pathToZipFile, dataType):
        url = self.baseurl + '/import/create-layer.action'

        # the following creates a QHttpMultiPart with 2 parts, one defining the
        # dataType (i.e. Vector or Raster) and one with the binary file data itself

        textpart = QHttpPart()
        textpart.setHeader(QNetworkRequest.ContentDispositionHeader, 'form-data; name="dataType"')
        if PYTHON_VERSION >= 3:
            textpart.setBody(dataType.encode('utf-8'))
        else:
            textpart.setBody(dataType)

        file = QFile(pathToZipFile)
        file.open(QIODevice.ReadOnly)
        lyr = 'form-data; name="file"; filename="' + os.path.basename(pathToZipFile) + '"'
        layerpart = QHttpPart()
        layerpart.setHeader(QNetworkRequest.ContentTypeHeader, 'application/zip')
        layerpart.setHeader(QNetworkRequest.ContentDispositionHeader, lyr)
        layerpart.setBodyDevice(file)

        multipart = QHttpMultiPart(QHttpMultiPart.FormDataType)
        multipart.append(textpart)
        multipart.append(layerpart)

        response = self.http.request(url, method = 'POST', body = multipart)
        res = json.loads(response[1])
        if res['success']:
            self.userInfo(response[0]['status'], 'New Vector Layer', 'uploaded')
        else:
            if res['error'] == 'NO_CRS':
                self.requestCrsUpdateOnLayer(res['importJobId'])
            else:
                self.userInfo(response[0]['status'], 'New Vector Layer', 'uploaded')
        return response[0]['status']

    def requestCrsUpdateOnLayer(self, importJobId):
        url = self.baseurl + '/import/update-crs-for-import.action'
        data = 'importJobId=' + str(importJobId) + '&taskId=0&fileProjection=EPSG%3A3857&layerName=&dataType=Vector'
        h = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = self.http.request(url, method = 'POST', body = data, headers = h)

    def getFieldNamesFromWfs(self, layerRessourceName):
        url = self.baseurl + 'geoserver.action?service=WFS&request=DescribeFeatureType&typeName='
        url += layerRessourceName + '&outputFormat=application/json'
        response = self.http.request(url)
        if response[0]['status'] == 200 or response[0]['status'] == 201:
            fieldNames = []
            answer = json.loads(response[1])
            if answer['featureTypes'][0]['properties']:
                for prop in answer['featureTypes'][0]['properties']:
                    fieldNames.append(prop['name'])
            if len(fieldNames) > 0:
                return fieldNames
        return False


    def deleteLayer(self, id):
        url = self.baseurl + 'rest/projectlayers/' + str(id)
        response = self.http.request(url, method = 'DELETE')
        self.userInfo(response[0]['status'], 'Layer', 'deleted')


    def deleteApplication(self, id):
        url = self.baseurl + 'rest/projectapps/' + str(id)
        response = self.http.request(url, method = 'DELETE')
        self.userInfo(response[0]['status'], 'Application', 'deleted')


    def copyApplication(self, id, applicationName):
        url = self.baseurl + 'projectapps/copy.action'
        data = 'appId=' + str(id) + '&appName=' + applicationName + '-Copy'
        h = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = self.http.request(url, method = 'POST', body = data, headers = h)
        self.userInfo(response[0]['status'], 'Application', 'copied')


    def viewApplicationOnline(self, id):
        url = self.baseurl + 'client/?id=' + str(id)
        webbrowser.open(url)


    def createLayerTreeItem(self, data):
        url = self.baseurl + 'rest/layertree'
        header = {'Content-type':'application/json'}
        body = json.dumps(data)
        response = self.http.request(url, method = 'POST', body = data, headers = h)
        return response[0]['status']


    def updateLayerTreeItem(self, layerTreeItemId, data):
        url = self.baseurl + 'rest/layertree/' + str(layerTreeItemId)
        header = {'Content-type':'application/json'}
        body = json.dumps(data)
        response = self.http.request(url, method = 'Put', body = data, headers = h)
        return response[0]['status']
