
# Shogun Editor for QGIS. A plugin

A QGIS plugin for editing a SHOGun GIS client instance. See [https://github.com/terrestris/shogun](https://github.com/terrestris/shogun)

After connecting with SHOGun, the user can edit applications and layers on the SHOGun server, in interaction with the QGIS interface.

# Features

* Add layers from SHOGun to QGIS (as WFS, WMS or raw data)

* Upload new layers (vector and raster format) from QGIS to the SHOGun server

* Upload layer style (vector layers only) from QGIS and apply to the layers in SHOGun
    -> most basic styling is implemented, also the upload of custom symbols for point layers

* Edit static data like names, descriptions, ...

* Create new SHOGun applications

* Set applications homeview directly from the QGIS interface

# Installation

You can install the plugin via the QGIS plugin repository or manually.
Manually installing: Copy the "shoguneditor directory to your
qgis plugins directory which you should find at:

## QGIS 2.x

usually in your home directory you find: .qgis2/python/plugins/
->  if you need more details see this link (chapter "The Copy Method")

## QGIS 3.x

To find the plugins folder, open up QGIS, in the menu go to Settings->User Profiles -> Open active profile folder
In the file explorer, go to python/plugins/ and paste the folder there

After copying just open up QGIS, activate the plugin in the plugin manager and you are done

# Development

Create a symlink:

```bash
# move to your your plugins directory:
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins
# link your workspace with the plugins directory:
ln -s  ~/workspace/qgis-shogun-editor/src/shoguneditor shoguneditor
```

## Debugging in VSCode

### Install QGIS plugins

* install `Plugin Reloader` (experimental)
* install `debugvs`

### Install python dependencies

* install ptvsd `(sudo) pip3 install ptvsd (--user)` (needed by `debugvs`)
* add qgis to python path: `export PYTHONPATH=/usr/share/qgis/python` (depends on location of `qgis/python`)

### Install VSCode extensions

* install `python` extension from marketplace

### Debug setup

* in QGIS open `Plugins > Plugin Reloader > Configure`
* select plugin that should be reloaded
* start `debugvs`: In QGIS open `Plugins > Enable debug for visual studio > Enable debug for visual studio`
* in VSCode go to `Debug` tab and start debugging in `attach` mode
* make sure that property `pathMappings.remoteRoot` is set in launch.json as absolute path or VSCode variable

# Important notes & missing features

* The plugin works with QGIS 2.x and 3.x, but currently there is a problem with adding wfs layers
to QGIS ins 3.x, which has to be resolved

* As already mentioned, the plugin works with basic authentication requests and therefore
can only be used with SHOGun installations which support basic  authentication

* Layer styles based on custom icons in SHOGun currently cannot be imported to QGIS, but styles with custom icons created in QGIS can be uploaded to SHOGun

* Layer styles based on font symbols are currently not supported by the plugin
