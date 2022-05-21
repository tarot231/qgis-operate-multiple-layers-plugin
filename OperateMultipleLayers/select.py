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

from qgis.PyQt.QtCore import QObject, QEvent, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import (QgsVectorLayer, Qgis,
                       QgsRectangle, QgsGeometry, QgsProject, QgsFeatureRequest)
from qgis.gui import QgsMapMouseEvent
from .watcher import WatcherBase


class ViewportFilter(QObject):
    mousePress = pyqtSignal(QObject, QEvent)
    mouseRelease = pyqtSignal(QObject, QEvent)

    def eventFilter(self, obj, event):
        if isinstance(obj, QWidget):
            if (event.type() == QEvent.MouseButtonPress and
                    event.button() == Qt.LeftButton):
                self.mousePress.emit(obj, event)
            elif (event.type() == QEvent.MouseButtonRelease and
                    event.button() == Qt.LeftButton):
                self.mouseRelease.emit(obj, event)
        return False


class SelectFeaturesWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = self.iface.mapCanvas()
        self.pt = None

        self.filter = ViewportFilter()
        self.filter.mousePress.connect(self.slot_mousePress)
        self.filter.mouseRelease.connect(self.slot_mouseRelease)
        self.canvas.viewport().installEventFilter(self.filter)

    def slot_mousePress(self, obj, event):
        if not isinstance(obj, QObject) or obj.parent() != self.canvas:
            self.pt = None
        else:
            self.pt = QgsMapMouseEvent(self.canvas, event).mapPoint()

    def slot_mouseRelease(self, obj, event):
        if (not isinstance(obj, QObject) or obj.parent() != self.canvas
                or self.pt is None):
            return

        pt = QgsMapMouseEvent(self.canvas, event).mapPoint()
        rect = QgsRectangle(self.pt, pt)
        project = QgsProject.instance()
        request = QgsFeatureRequest(rect)
        request.setDestinationCrs(project.crs(), project.transformContext())
        doContains = bool(event.modifiers() & Qt.AltModifier)
        # BAD
        #engine = QgsGeometry.createGeometryEngine(QgsGeometry.fromRect(rect).constGet())
        geom = QgsGeometry.fromRect(rect)
        engine = QgsGeometry.createGeometryEngine(geom.constGet())
        engine.prepareGeometry()
        _ = (Qgis.SelectBehavior
                if Qgis.QGIS_VERSION_INT >= 32200 else QgsVectorLayer)
        if event.modifiers() & Qt.ShiftModifier:
            if event.modifiers() & Qt.ControlModifier:
                behavior = _.IntersectSelection
            else:
                behavior = _.AddToSelection
        elif event.modifiers() & Qt.ControlModifier:
            behavior = _.RemoveFromSelection
        else:
            behavior = _.SetSelection

        layers = self.iface.layerTreeView().selectedLayers()
        
        for lyr in layers:
            if not isinstance(lyr, QgsVectorLayer):
                continue
            if lyr is self.iface.activeLayer():
                continue

            ids = []
            for f in lyr.getFeatures(request):
                if doContains:
                    g = f.geometry()
                    if not engine.contains(g.constGet()):
                        continue
                ids.append(f.id())
            lyr.selectByIds(ids, behavior)
