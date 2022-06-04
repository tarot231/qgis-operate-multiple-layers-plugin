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


class ToggleEditingWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.iface.actionToggleEditing().triggered.connect(
                self.slot_triggered)

    def slot_triggered(self):
        checked = self.iface.actionToggleEditing().isChecked()
        tools = self.iface.vectorLayerTools()
        config = self.parent.config.getValue()
        if (Qgis.QGIS_VERSION_INT >= 30400 and config['recursive']):
            layers = self.iface.layerTreeView().selectedLayersRecursive()
        else:
            layers = self.iface.layerTreeView().selectedLayers()
        root = self.iface.layerTreeCanvasBridge().rootGroup()

        for lyr in layers:
            if not isinstance(lyr, QgsVectorLayer):
                continue
            if lyr is self.iface.activeLayer():
                continue

            if config['skip_invisible']:
                node = root.findLayer(lyr)
                if (not isinstance(node, QgsLayerTreeNode) or
                        not node.isVisible()):
                    continue

            if checked:
                if (not lyr.isEditable()
                        and lyr.dataProvider().capabilitiesString()):
                    tools.startEditing(lyr)
            else:
                if lyr.isEditable():
                    tools.stopEditing(lyr)
