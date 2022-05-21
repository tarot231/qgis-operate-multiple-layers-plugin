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

import math
from qgis.PyQt.QtCore import QObject, QEvent, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsVectorLayer, QgsProject, QgsCoordinateTransform
from qgis.gui import QgsMapMouseEvent, QgsDoubleSpinBox
from .watcher import WatcherBase


class ViewportFilter(QObject):
    mouseRelease = pyqtSignal(QObject, QEvent)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.MouseButtonRelease and
                event.button() == Qt.LeftButton):
            self.mouseRelease.emit(obj, event)
        return False


class RotateFeatureWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = self.iface.mapCanvas()
        self.fid = self.geom = self.params = None
        self.anchor = None
        self.rotation = self.roffset = 0

        self.filter = ViewportFilter()
        self.filter.mouseRelease.connect(self.slot_mouseRelease)
        self.canvas.viewport().installEventFilter(self.filter)

        self.current_layer.selectionChanged.connect(self.slot_selectionChanged)
        self.slot_selectionChanged(self.current_layer.selectedFeatureIds())
        self.current_layer.geometryChanged.connect(self.slot_geometryChanged)
        self.stack = self.current_layer.undoStack()
        self.stack.indexChanged.connect(self.slot_indexChanged)

    def slot_mouseRelease(self, obj, event):
        if not isinstance(obj, QObject) or obj.parent() != self.canvas:
            return
        pt = QgsMapMouseEvent(self.canvas, event).snapPoint()
        if event.modifiers() & Qt.ControlModifier:
            self.anchor = pt
        elif self.anchor is not None:
            dx = pt.x() - self.anchor.x()
            dy = pt.y() - self.anchor.y()
            angle = math.atan2(dx, dy) * (180 / math.pi)
            self.rotation = angle - self.roffset
            self.roffset = angle

    def slot_selectionChanged(self, fids):  # occurs from attribute table
        if len(fids):
            pt = self.current_layer.boundingBoxOfSelected().center()
            self.anchor = self.canvas.mapTool().toMapCoordinates(
                    self.current_layer, pt)
        else:
            self.anchor = None
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

        if self.anchor is None:
            return
        dock = self.iface.mainWindow().findChild(QWidget, 'UserInputDockWidget')
        spinbox = dock.findChild(QgsDoubleSpinBox)
        if spinbox is None:
            return
        angle = spinbox.value()
        if round(self.rotation, spinbox.decimals()) != angle:
            self.rotation = angle  # manual or magnet

        # Check
        prev_geom.rotate(self.rotation, self.anchor)
        if not geom.equals(prev_geom):
            return
        
        self.params = self.rotation, self.anchor

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
                    g.rotate(*self.params)
                    g.transform(ct, QgsCoordinateTransform.ReverseTransform)
                else:
                    g.rotate(*self.params)
                lyr.changeGeometry(f.id(), g)

            lyr.undoStack().endMacro()

        if flag_ct:
            self.push_crs_used()
        self.params = None
