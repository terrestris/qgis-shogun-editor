# -*- coding: utf-8 -*-
'''
/***************************************************************************
 ShogunEditor
                                 A QGIS plugin to connect with a Shogun
                                 GIS client instance on a remote or local server
                                 and edit it's content from QGIS

                             -------------------
        begin                : 2018-05-11
        copyright            : (C) 2018 by terrestris GmbH & Co. KG
        email                : jgrieb (at) terrestris.de, info (at) terrestris.de
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
'''

__author__ = 'Jonas Grieb'
__date__ = 'July 2018'

import os.path

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction, QIcon

import resources
from .gui.editor import Editor


class ShogunEditor:
    '''This class establishes the plugin icon in the qgis gui and menu, and
    calls the class Editor() when the plugin is opened'''

    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

    # the following would be needed to add internationalization, maybe in a
    # future release

    #    locale = QSettings().value('locale/userLocale')[0:2]
    #    locale_path = os.path.join(
    #        self.plugin_dir,
    #        'i18n',
    #        'ShogunEditorPrototyp_{}.qm'.format(locale))

    #    if os.path.exists(locale_path):
    #        self.translator = QTranslator()
    #        self.translator.load(locale_path)

    #        if qVersion() > '4.3.3':
    #            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = '&Shogun Editor'
        self.toolbar = self.iface.addToolBar(u'ShogunEditor')
        self.toolbar.setObjectName(u'ShogunEditor')

        self.pluginIsActive = False
        self.editor = None


    def initGui(self):

        iconPath = ':/plugins/shoguneditor/shogun-logo-50x50px-round-blue.png'
        openEditorAction = QAction(
            QIcon(iconPath), 'Shogun Editor', self.iface.mainWindow())
        self.actions.append(openEditorAction)
        openEditorAction.triggered.connect(self.openEditor)
        self.toolbar.addAction(openEditorAction)
        self.iface.addPluginToWebMenu(self.menu, openEditorAction)


    def onClosePlugin(self):
        if self.editor is None:
            return
        connections_nr = self.editor.topitem.childCount()
        for x in range(connections_nr):
            try:
                connection = self.editor.topitem.child(x)
                connection.disconnectSignals()
            except:
                pass


    def unload(self):
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.menu,
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar


    def openEditor(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True

            self.editor = Editor(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.editor.dock)
            self.editor.dock.show()

        else:
            self.editor.dock.show()
