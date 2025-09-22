#!/bin/bash

xhost +local:docker
docker run --rm -it --name qgis --net host \
     -e DISPLAY=$DISPLAY \
     -v /tmp/.X11-unix:/tmp/.X11-unix \
     -v ./:/root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/shogun_qgis_editor  \
    qgis/qgis:3.44 \
    qgis
