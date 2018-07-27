Shogun Editor for QGIS. A plugin


Info:
A QGIS plugin for editing a Shogun GIS client instance. See https://github.com/terrestris/shogun2
--Link will be replaced when Shogun2-webapp will be released--
After connecting with the Shogun ressource (note: that ressource needs to have basic authentication possibility),
the user can edit applications and layers on the Shogun server, in interaction with the QGIS interface.


Features:

    Add layers from Shogun to QGIS (as WFS, WMS or raw data)
    Upload new layers (vector and raster format) from QGIS to the Shogun server
    Upload layer style (vector layers only) from QGIS and apply to the layers in Shogun -> most basic styling is implemented, also the upload of custom symbols for point layers
    Edit static data like names, descriptions, ...
    Create new Shogun applications
    Set applications homeview directly from the QGIS interface

Installation
You can install the plugin via the QGIS plugin repository or manually. Manually installing: Copy the shogun-editor directory to your qgis plugins directory which you should find at:

    QGIS 2.x:
    usually in your home directory you find: .qgis2/python/plugins/ - if you need more details see this link (chapter "The Copy Method")
    QGIS 3.x:
    To find the plugins folder, open up QGIS, in the menu go to Settings->User Profiles -> Open active profile folder
    In the file explorer, go to python/plugins/ and paste the folder there


After copying just open up QGIS, activate the plugin in the plugin manager and you are done

Important notes & missing features

    The plugin works with QGIS 2.x and 3.x, but currently there is a problem with adding wfs layers
    to QGIS ins 3.x, which has to be resolved.
    As already mentioned, the plugin works with basic authentication requests and therefore can only be used with Shogun2-Webapp installations which support basic authentication
    Layer styles based on custom icons in Shogun currently cannot be imported to QGIS, but styles with custom icons created in QGIS can be uploaded to Shogun
    Layer styles based on font symbols are currently not supported by the plugin
