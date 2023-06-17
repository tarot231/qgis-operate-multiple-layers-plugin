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
from qgis.PyQt.QtCore import QObject, QTranslator, QLocale, QSettings
from qgis.PyQt.QtWidgets import qApp, QDialog, QAction
from qgis.core import QgsApplication, QgsVectorLayer
from .toggle_edit import ToggleEditingWatcher
from .select_all_invert import SelectAllAndInvertWatcher
from .undo import UndoWatcher
from .delete import DeleteFeatureWatcher
from .select import SelectFeaturesWatcher
from .move import MoveFeatureWatcher
from .rotate import RotateFeatureWatcher
from .scale import ScaleFeatureWatcher
from .ui import ConfigDialog


class OperateMultipleLayers(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.translator = QTranslator()
        if self.translator.load(QLocale(QgsApplication.locale()),
                '', '', os.path.join(os.path.dirname(__file__), 'i18n')):
            qApp.installTranslator(self.translator)

    def initGui(self):
        self.plugin_name = self.tr('Operate Multiple Layers')
        self.config = ConfigDialog(parent=self.iface.mainWindow())
        self.config.setWindowTitle('%s — %s' % 
                (self.tr('Configure'), self.plugin_name))
        self.plugin_act = QAction(
                self.tr('Configure…'), self.iface.mainWindow())
        self.plugin_act.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.plugin_name, self.plugin_act)
        self.restore_setting()

        self.is_undoing = False
        self.canvas = self.iface.mapCanvas()
        self.canvas.currentLayerChanged.connect(self.slot_currentLayerChanged)
        self.canvas.mapToolSet.connect(self.slot_mapToolSet)
        self.slot_currentLayerChanged(self.iface.activeLayer())

        self.toggle_edit_watcher = ToggleEditingWatcher(self)
        self.select_all_invert_watcher = SelectAllAndInvertWatcher(self)

    def unload(self):
        self.select_all_invert_watcher.unload()
        self.select_all_invert_watcher = None
        self.toggle_edit_watcher = None
        self.undo_watcher = None
        self.delete_watcher = None
        self.tool_watcher = None
        self.save_setting()
        self.iface.removePluginMenu(self.plugin_name, self.plugin_act)
        del self.plugin_act

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
        try:
            name = self.canvas.mapTool().action().objectName()
        except AttributeError:
            return
        if name =='mActionSelectFeatures':
            self.tool_watcher = SelectFeaturesWatcher(self)
        elif name =='mActionMoveFeature':
            self.tool_watcher = MoveFeatureWatcher(self)
        elif name =='mActionRotateFeature':
            self.tool_watcher = RotateFeatureWatcher(self)
        elif name =='mActionScaleFeature':
            self.tool_watcher = ScaleFeatureWatcher(self)

    def run(self):
        prev = self.config.getValue()
        if self.config.exec() != QDialog.Accepted:
            self.config.setValue(prev)

    def restore_setting(self):
        dict_value = {}
        keys = ('skip_invisible', 'recursive')
        for k in keys:
            v = QSettings().value('/'.join((self.__class__.__name__, k)))
            dict_value[k] = bool(v == 'true')
        self.config.setValue(dict_value)

    def save_setting(self):
        dict_value = self.config.getValue()
        for k in dict_value.keys():
            QSettings().setValue('/'.join((self.__class__.__name__, k)),
                    dict_value[k])


def classFactory(iface):
    return OperateMultipleLayers(iface)
