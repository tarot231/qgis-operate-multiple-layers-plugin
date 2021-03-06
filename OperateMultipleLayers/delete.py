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

from qgis.core import QgsVectorLayer, Qgis, QgsLayerTreeNode
from .watcher import WatcherBase


class DeleteFeatureWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_layer.featuresDeleted.connect(self.slot_featuresDeleted)

    def slot_featuresDeleted(self):
        if self.parent.is_undoing:
            return

        config = self.parent.config.getValue()
        if (Qgis.QGIS_VERSION_INT >= 30400 and config['recursive']):
            layers = self.iface.layerTreeView().selectedLayersRecursive()
        else:
            layers = self.iface.layerTreeView().selectedLayers()
        root = self.iface.layerTreeCanvasBridge().rootGroup()
        undo_text = self.current_layer.undoStack().undoText()

        for lyr in layers:
            if not (isinstance(lyr, QgsVectorLayer) and lyr.isEditable()):
                continue
            if lyr is self.iface.activeLayer():
                continue

            if config['skip_invisible']:
                node = root.findLayer(lyr)
                if (not isinstance(node, QgsLayerTreeNode) or
                        not node.isVisible()):
                    continue

            lyr.undoStack().beginMacro(undo_text)

            lyr.deleteSelectedFeatures()

            lyr.undoStack().endMacro()
