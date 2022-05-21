# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Operate Multiple Layers
                                 A QGIS plugin
 Operate map tools with multiple layers
                             -------------------
        begin                : 2022-03-20
        copyright            : (C) 2022 by Tarot Osuji
        email                : tarot@sdf.org
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
"""

from qgis.core import QgsVectorLayer, QgsProject, QgsCoordinateTransform
from .watcher import WatcherBase


class MoveFeatureWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = self.iface.mapCanvas()
        self.fid = self.geom = self.params = None

        self.current_layer.selectionChanged.connect(self.slot_selectionChanged)
        self.slot_selectionChanged(self.current_layer.selectedFeatureIds())
        self.current_layer.geometryChanged.connect(self.slot_geometryChanged)    
        self.stack = self.current_layer.undoStack()
        self.stack.indexChanged.connect(self.slot_indexChanged)

    def slot_selectionChanged(self, fids):  # occurs from attribute table
        self.updateGeometryInfo(fids)

    def updateGeometryInfo(self, fids):
        if len(fids):
            self.fid = fids[0]
            self.geom = self.current_layer.getFeature(self.fid).geometry()
        else:
            self.fid = self.geom = None

    def slot_geometryChanged(self, fid, geom):
        if fid != self.fid:
            return

        prev_geom = self.geom
        self.updateGeometryInfo(self.current_layer.selectedFeatureIds())

        v0 = prev_geom.vertexAt(0)
        v = geom.vertexAt(0)
        self.params = v.x() - v0.x(), v.y() - v0.y()

    def slot_indexChanged(self):
        if self.parent.is_undoing or self.params is None:
            self.params = None
            return

        layers = self.iface.layerTreeView().selectedLayers()
        undo_text = self.stack.undoText()
        flag_ct = False

        for lyr in layers:
            if not (isinstance(lyr, QgsVectorLayer) and lyr.isEditable()):
                continue
            if lyr is self.iface.activeLayer():
                continue

            if lyr.crs() != self.current_layer.crs():
                flag_ct = True
                ct = QgsCoordinateTransform(lyr.crs(), self.current_layer.crs(),
                        QgsProject.instance())
            else:
                ct = None

            lyr.undoStack().beginMacro(undo_text)

            for f in lyr.getSelectedFeatures():
                g = f.geometry()
                if ct:
                    g.transform(ct)
                    g.translate(*self.params)
                    g.transform(ct, QgsCoordinateTransform.ReverseTransform)
                else:
                    g.translate(*self.params)
                lyr.changeGeometry(f.id(), g)

            lyr.undoStack().endMacro()

        if flag_ct:
            self.push_crs_used()
        self.params = None
