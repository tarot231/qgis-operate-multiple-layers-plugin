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

import os
from qgis.PyQt.QtCore import QObject, QTranslator, QLocale
from qgis.PyQt.QtWidgets import qApp
from qgis.core import QgsApplication, QgsVectorLayer
from .toggle_edit import ToggleEditingWatcher
from .undo import UndoWatcher
from .delete import DeleteFeatureWatcher
from .select import SelectFeaturesWatcher
from .move import MoveFeatureWatcher
from .rotate import RotateFeatureWatcher
from .scale import ScaleFeatureWatcher


class OperateMultipleLayers(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.translator = QTranslator()
        if self.translator.load(QLocale(QgsApplication.locale()),
                '', '', os.path.join(os.path.dirname(__file__), 'i18n')):
            qApp.installTranslator(self.translator)
        self.plugin_name = self.tr('Operate Multiple Layers')

    def initGui(self):
        self.is_undoing = False
        self.canvas = self.iface.mapCanvas()
        self.canvas.currentLayerChanged.connect(self.slot_currentLayerChanged)
        self.canvas.mapToolSet.connect(self.slot_mapToolSet)
        self.slot_currentLayerChanged(self.iface.activeLayer())
        self.toggle_edit_watcher = ToggleEditingWatcher(self)

    def unload(self):
        self.toggle_edit_watcher = None
        self.undo_watcher = None
        self.delete_watcher = None
        self.tool_watcher = None

    def slot_currentLayerChanged(self, layer):
        self.current_layer = layer
        is_vector = isinstance(self.current_layer, QgsVectorLayer)
        self.undoable_index = self.current_layer.undoStack().index() if is_vector else None
        self.undo_watcher = UndoWatcher(self) if is_vector else None
        self.delete_watcher = DeleteFeatureWatcher(self) if is_vector else None
        if is_vector:
            self.slot_mapToolSet()
        else:
            self.tool_watcher = None

    def slot_mapToolSet(self):
        self.tool_watcher = None
        if self.canvas.mapTool() is None:
            return
        name = self.canvas.mapTool().action().objectName()
        if name =='mActionSelectFeatures':
            self.tool_watcher = SelectFeaturesWatcher(self)
        elif name =='mActionMoveFeature':
            self.tool_watcher = MoveFeatureWatcher(self)
        elif name =='mActionRotateFeature':
            self.tool_watcher = RotateFeatureWatcher(self)
        elif name =='mActionScaleFeature':
            self.tool_watcher = ScaleFeatureWatcher(self)


def classFactory(iface):
    return OperateMultipleLayers(iface)
