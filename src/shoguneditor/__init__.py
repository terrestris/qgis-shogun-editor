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


def classFactory(iface):
    """Load ShogunEditorclass from file shogun_editor.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .shogun_editor import ShogunEditor
    return ShogunEditor(iface)
