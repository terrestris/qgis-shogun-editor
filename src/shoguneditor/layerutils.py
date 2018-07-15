# -*- coding: utf-8 -*-
'''
(c) 2018 Terrestris GmbH & CO. KG, https://www.terrestris.de/en/
+ the last method "getLabelingAsSld()" was taken
+ from the qgis geoserver explorer plugin by
+ (C) 2016 Boundless, http://boundlessgeo.com
+ see: https://github.com/boundlessgeo/qgis-geoserver-plugin
'''

__author__ = 'Jonas Grieb'
__date__ = 'Juli 2018'


import urllib
import os.path
import zipfile
import tempfile

from qgis.core import QgsVectorLayer, QgsRasterLayer, QGis, QgsMapLayer, QgsCoordinateReferenceSystem
from qgis.core import QgsVectorFileWriter, QgsRasterFileWriter, QgsRasterPipe
from PyQt4.QtGui import QMessageBox, QDialog, QLabel, QPushButton
from PyQt4.QtCore import QRect
from PyQt4.QtXml import QDomDocument

from shoguneditor.gui.dialog_bases.addraster import AddRasterDialog

'''This module contains some helper functions for the shogun-editor plugin'''

def createLayer(layerItem, epsg):
    #Shogun Webapp saves all layers in the following espg, therefore the
    #variable can be static
    layerurl = layerItem.source['url']

    dataType = layerItem.datatype

    # every layerItem.source should have an attribute 'dataType'
    if dataType == 'Vector':
        url = layerItem.ressource.baseurl.rstrip('/shogun2-webapp/') + layerurl + '?'
        return createWfsLayer(layerItem, url, epsg)

    elif dataType == 'Raster':
        url = layerItem.ressource.baseurl.rstrip('/shogun2-webapp/') + layerurl + '?'
        return createRasterLayer(layerItem, url, epsg)

    elif dataType == 'WMS':
        if layerurl == '/shogun2-webapp/geoserver.action':
            url = layerItem.ressource.baseurl.rstrip('/shogun2-webapp/') + layerurl + '?'
            return createWmsLayerFromShogun(layerItem, url)
        else:
            return createWmsLayer(layerItem, layerurl, epsg)

    # if for any reason the parameter 'dataType' is not set correctly, we check the url
    # of the layer to determine if it's a WFS/WCS from the shogun-geoserver
    # (url has'shogun2-webapp') or if it's a WMS from an outer source (other url)
    elif dataType == 'unknown' or dataType == None or dataType == '':
        if layerurl.startswith('/shogun2-webapp'):
            url = layerItem.ressource.baseurl.rstrip('/shogun2-webapp/') + layerurl + '?'
            try:
                lyr = createWfsLayer(layerItem, url, epsg)
                if lyr.isValid():
                    return lyr
            except:
                pass
            try:
                lyr =  createWmsLayerFromShogun(layerItem, url, epsg)
                if lyr.isValid():
                    return lyr
            except:
                pass
            try:
                lyr =  createRasterLayer(layerItem, url, epsg)
                if lyr.isValid():
                    return lyr
            except:
                pass
        else:
            return createWmsLayerNormal(layerItem, layerurl, epsg)

    else:
        info = 'Layer source '+ url + ' could not be loaded'
        QMessageBox.warning(None, 'Warning', info, QMessageBox.Ok)



def createWfsLayer(layerItem, url, epsg):
    params = {
        'srsname': epsg,
        'typename': layerItem.source['layerNames'],
        'url': url + 'typename=' + layerItem.source['layerNames'],
        'version': 'auto'
        }

    uri = ''
    for i in params.items():
        uri += i[0] + '=\'' + i[1] + '\''
    layer = QgsVectorLayer(uri, 'SHOGUN-Layer: ' + layerItem.name, 'WFS')
    return layer


def createRasterLayer(layerItem, url, epsg):

    dlg = AddRasterDialog()
    dlg.show()
    userSelection = dlg.exec_()

    if userSelection == 0:
        return False

    elif userSelection == 1:
        return createWmsLayerFromShogun(layerItem, url, epsg)

    elif userSelection == 2:

        #workaround...
        ## TODO:  can this be made using the qgis wcs provider?
        layerName = layerItem.source['layerNames']

        params = {
            'request' : 'GetCoverage',
            'version' : '2.0.1',
            'coverageId' : layerName,
            'namespace' : 'SHOGUN',
            'identifier' : layerName
        }

        #build the fitting url from the baseurl ('http...geoserver.action?')
        #and the parameters
        baseurl = url + 'service=WCS&'
        url = baseurl + urllib.urlencode(params)

        #urlretrieve stores the downloaded file in /tmp/ and returns it's path:
        response = urllib.urlretrieve(url)
        file = response[0]
        #create a raster layer and return it
        return QgsRasterLayer(file, 'QGIS-Layer: ' + layerItem.name)


def createWmsLayerNormal(layerItem, url, epsg):
    params = {
        'crs': epsg,
        'dpiMode': '7',
        'format': 'image/png',
        'layers': layerItem.source['layerNames'],
        'styles': '',
        'url': url
        }

    uri = urllib.urlencode(params)

    layer = QgsRasterLayer(uri, 'QGIS-Layer: ' + layerItem.name, 'wms')
    if layer.isValid():
        return layer
    else:
        return False



def createWmsLayerFromShogun(layerItem, url, epsg):
    layerNames = layerItem.source['layerNames']
    params = {
        'IgnoreGetMapUrl' : 1,
        'crs': epsg,
        'format': 'image/png',
        'layers': layerNames.split(':')[1],
        'styles': '',
        'url': url + 'layers=' + layerNames
    }

    uri = urllib.urlencode(params)
    layer = QgsRasterLayer(uri, 'QGIS-Layer: ' + layerItem.name, 'wms')
    if layer.isValid():
        return layer
    else:
        return False


def createAndParseSld(qgisLayerItem):
    document = QDomDocument()
    header = document.createProcessingInstruction( 'xml', 'version=\'1.0\' encoding=\'UTF-8\'' )
    document.appendChild( header )
    root = document.createElementNS( 'http://www.opengis.net/sld', 'StyledLayerDescriptor' )
    root.setAttribute( 'version', '1.0.0' )
    root.setAttribute( 'xmlns:ogc', 'http://www.opengis.net/ogc' )
    root.setAttribute( 'xmlns:sld', 'http://www.opengis.net/sld' )
    root.setAttribute( 'xmlns:gml', 'http://www.opengis.net/gml' )
    document.appendChild( root )

    namedLayerNode = document.createElement( 'sld:NamedLayer' )
    root.appendChild( namedLayerNode )


    qgisLayerItem.layer.writeSld(namedLayerNode, document, '')  ## TODO: if could not be created...

    nameNode = namedLayerNode.firstChildElement('se:Name')
    oldNameText = nameNode.firstChild()
    newname = qgisLayerItem.parentShogunLayer.source['layerNames']
    newNameText = document.createTextNode(newname)
    nameNode.appendChild(newNameText)
    nameNode.removeChild(oldNameText)

    userStyleNode = namedLayerNode.firstChildElement('UserStyle')
    userStyleNameNode = userStyleNode.firstChildElement('se:Name')
    userStyleNameText = userStyleNameNode.firstChild()
    userStyleNameNode.removeChild(userStyleNameText)
    userStyleNameNode.appendChild(document.createTextNode(qgisLayerItem.stylename))

    titleNode = document.createElement('sld:Title')
    title = document.createTextNode('A QGIS-Style for '+qgisLayerItem.layer.name())
    titleNode.appendChild(title)
    userStyleNode.appendChild(titleNode)
    defaultNode = document.createElement('sld:IsDefault')
    defaultNode.appendChild(document.createTextNode('1'))
    userStyleNode.appendChild(defaultNode)

    featureTypeStyleNode = userStyleNode.firstChildElement('se:FeatureTypeStyle')
    featureTypeStyleNameNode = document.createElement('sld:Name')
    featureTypeStyleNameNode.appendChild(document.createTextNode('name'))
    featureTypeStyleNode.appendChild(featureTypeStyleNameNode)

    rules = featureTypeStyleNode.elementsByTagName('se:Rule')
    for x in range(rules.length()):
        rule = rules.at(x)
        rule.removeChild(rule.firstChildElement('se:Description'))

    # Check if custom icons are used in symbology and replace the text:
    # search if tag 'se:OnlineResource' is in the sld document
    listOfGraphics = rule.toElement().elementsByTagName('se:OnlineResource')
    if not listOfGraphics.isEmpty():
        for x in range(listOfGraphics.length()):
            graphicNode = listOfGraphics.at(x)
            currentIcon = graphicNode.attributes().namedItem('xlink:href').nodeValue()
            iconUrl = qgisLayerItem.ressource.prepareIconForUpload(currentIcon)
            graphicNode.toElement().setAttribute('xlink:href', iconUrl)
            graphicNode.toElement().setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')

    sld = document.toString()

    if qgisLayerItem.layer.labelsEnabled():
        labelSld = getLabelingAsSld(qgisLayerItem.layer)
        sld = sld.replace('</se:Rule>', labelSld + '</se:Rule>')

    sld = sld.replace('ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"', 'ogc:Filter')

    # the following fixes weird problems with the sld compability with the
    # shogun webapp
    sld = sld.replace('<ogc:And>', '')
    sld = sld.replace('</ogc:And>', '')
    sld = sld.replace('<se:Name> ', '<se:Name>')
    sld = sld.replace(' </se:Name>', '</se:Name>')

    sld = sld.replace('StyledLayerDescriptor', 'sld:StyledLayerDescriptor')
    sld = sld.replace('UserStyle', 'sld:UserStyle')
    sld = sld.replace('se:', 'sld:')
    sld = sld.replace('SvgParameter', 'CssParameter')
    sld = sld.replace('\n', '')
    sld = sld.replace('\t', '')

    return sld


def prepareLayerForUpload(layer, uploadDialog):
    tmpdir = tempfile.mkdtemp()
    zipfilePath = tmpdir + '/uploadzip.zip'

    if layer.type() == QgsMapLayer.VectorLayer:
        if layer.source().endswith('.shp'):
            file = layer.source()
            uploadDialog.log('...success\nZipping...')
            zipSuccess = createZipFromShapefile(file, zipfilePath, delete = False)
        else:
            path = os.path.join(tmpdir, 'VectorlayerFromQGisPlugin.shp')
            uploadDialog.log('Writing layer as shapefile...')
            file = writeShapefile(layer, path)
            if not file:
                uploadDialog.log('Error: Could not write the shapefile ')
                return
            uploadDialog.log('...success\nZipping...')
            zipSuccess = createZipFromShapefile(file, zipfilePath, delete = True)

    else:
        if layer.providerType() == 'wms':
            return True
        if layer.source().endswith('.tif'):
            rasterfile = layer.source()
            uploadDialog.log('Zipping...')
            zipSuccess = createZipFromRaster(rasterfile, zipfilePath, delete = False)
        else:
            path = os.path.join(tmpdir, 'RasterlayerFromQGisPlugin.tif')
            uploadDialog.log('Creating raster file from layer...')
            rasterfile = writeRasterFile(layer, path)
            uploadDialog.log('Zipping...')
            if not rasterfile:
                uploadDialog.log('Error: Could not write the raster file')
                return
            zipSuccess = createZipFromRaster(rasterfile, zipfilePath, delete = True)
    uploadDialog.log(zipSuccess)
    return zipfilePath, tmpdir


def writeShapefile(layer, path):
        ## TODO: here are some problems with the upload - also shogun-problems

    writeError = QgsVectorFileWriter.writeAsVectorFormat(
    layer, path,'utf-8', layer.crs(), 'ESRI Shapefile', False)
    if writeError != 0:     #0 = writing success
        return False
    return path


def createZipFromShapefile(filepath, zipfilePath, delete=False):
    # create a list with '/path/name.shp' as the first item
    shapefileParts = [filepath]
    for extension in ['.dbf', '.shx', '.prj']:
        newFilename = os.path.splitext(filepath)[0] + extension
        if os.path.isfile(newFilename):
            # append the further shapefile parts to the list
            shapefileParts.append(newFilename)
        else:
            return 'Error: Could not find ' + os.path.basename(newFilename)

    # create a new zip-archive at zipfilePath
    newZipfile = zipfile.ZipFile(zipfilePath, 'w', zipfile.ZIP_DEFLATED)
    for part in shapefileParts:
        # add the parts of the shapefile to the zip-archive
        newZipfile.write(part, arcname = os.path.basename(part))
        # then delete the parts because we do not need them anymore
        if delete:
            os.remove(part)
    newZipfile.close()

    # delete further created files belonging to the shapefile, because we
    # do not need them
    if delete:
        for extension in ['.cpg', '.qpj']:
            newFilename = os.path.splitext(filepath)[0] + extension
            if os.path.isfile(newFilename):
                os.remove(newFilename)
    return 'Written successfully'


def writeRasterFile(layer, filepath):
    pipe = QgsRasterPipe()
    provider = layer.dataProvider()
    pipe.set(provider.clone())

    writer = QgsRasterFileWriter(filepath)
    writeError = writer.writeRaster(pipe, provider.xSize(), provider.ySize(),
        provider.extent(), provider.crs())

    return filepath


def createZipFromRaster(pathToRaster, zipfilePath, delete = False):
    newZipfile = zipfile.ZipFile(zipfilePath, 'w', zipfile.ZIP_DEFLATED)
    newZipfile.write(pathToRaster, arcname = os.path.basename(pathToRaster))
    newZipfile.close()
    if delete:
        try:
            os.remove(pathToRaster)
        except:
            pass
    return 'Written successfully'



#the following function:
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
def getLabelingAsSld(layer):
    SIZE_FACTOR = 4
    try:
        s = "<sld:TextSymbolizer><sld:Label>"
        s += "<ogc:PropertyName>" + layer.customProperty("labeling/fieldName") + "</ogc:PropertyName>"
        s += "</sld:Label>"
        r = int(layer.customProperty("labeling/textColorR"))
        g = int(layer.customProperty("labeling/textColorG"))
        b = int(layer.customProperty("labeling/textColorB"))
        rgb = '#%02x%02x%02x' % (r, g, b)
        s += '<sld:Fill><sld:CssParameter name="fill">' + rgb + "</sld:CssParameter></sld:Fill>"
        s += "<sld:Font>"
        s += '<sld:CssParameter name="font-family">' + layer.customProperty("labeling/fontFamily") +'</sld:CssParameter>'
        s += ('<sld:CssParameter name="font-size">' +
                str(int(layer.customProperty("labeling/fontSize")))
                +'</sld:CssParameter>')

        italic = False
        bold = False
        if layer.customProperty("labeling/fontItalic") == "true":
            s += '<sld:CssParameter name="font-style">italic</sld:CssParameter>'
            italic = True
        if layer.customProperty("labeling/fontBold") == "true":
            bold = True
            s += '<sld:CssParameter name="font-weight">bold<sld:/CssParameter>'
        if not italic and not bold:
            s += '<sld:CssParameter name="font-style">normal</sld:CssParameter>'
        s += '<sld:CssParameter name="font-weight">normal</sld:CssParameter>'
        s += "</sld:Font>"
        s += "<sld:LabelPlacement>"
        if layer.geometryType() == QGis.Point:
            s += ("<sld:PointPlacement>"
                "<sld:AnchorPoint>"
                "<sld:AnchorPointX>0.5</sld:AnchorPointX>"
                "<sld:AnchorPointY>0.5</sld:AnchorPointY>"
                "</sld:AnchorPoint>")
            s += "<sld:Displacement>"
            s += "<sld:DisplacementX>" + str(int(layer.customProperty("labeling/xOffset"))) + "</sld:DisplacementX>"
            s += "<sld:DisplacementY>" + str(int(layer.customProperty("labeling/yOffset"))) + "</sld:DisplacementY>"
            s += "</sld:Displacement>"
            s += "<sld:Rotation>" + str(abs(int(layer.customProperty("labeling/angleOffset")))) + "</sld:Rotation>"
            s += "</sld:PointPlacement>"
        elif layer.geometryType() == QGis.Line:
            mode = layer.customProperty("labeling/placement")
            if mode != 4:
                follow = '<sld:VendorOption name="followLine">true</sld:VendorOption>' if mode == 3 else ''
                s += '''<sld:LinePlacement>
                        <Psld:erpendicularOffset>
                           %s
                        </sld:PerpendicularOffset>
                      </sld:LinePlacement>
                      %s''' %  (str(layer.customProperty("labeling/dist")), follow)
        s += "</sld:LabelPlacement>"

        if layer.customProperty("labeling/bufferDraw") == "true":
            r = int(layer.customProperty("labeling/bufferColorR"))
            g = int(layer.customProperty("labeling/bufferColorG"))
            b = int(layer.customProperty("labeling/bufferColorB"))
            rgb = '#%02x%02x%02x' % (r, g, b)
            haloSize = str(layer.customProperty("labeling/bufferSize"))
            opacity = str(float(layer.customProperty("labeling/bufferColorA")) / 255.0)
            s += "<sld:Halo><sld:Radius>%s</sld:Radius><sld:Fill>" % haloSize
            s +=  '<sld:CssParameter name="fill">%s</sld:CssParameter>' % rgb
            s += '<sld:CssParameter name="fill-opacity">%s</sld:CssParameter></sld:Fill></sld:Halo>' % opacity
        s +="</sld:TextSymbolizer>"
        return s
    except:
        return ""
