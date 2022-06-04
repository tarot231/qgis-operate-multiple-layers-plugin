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

from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsVectorLayer, Qgis, QgsLayerTreeNode
from .watcher import WatcherBase


class SelectAllAndInvertWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)
        for act in self.iface.editMenu().findChild(QMenu, 'mMenuSelect').actions():
            name = act.objectName()
            if name == 'mActionSelectAll':
                self.actionSelectAll = act
                self.lambdaSelectAll = lambda: self.slot_triggered(invert=False)
                self.actionSelectAll.triggered.connect(self.lambdaSelectAll)
            elif name == 'mActionInvertSelection':
                self.actionInvertSelection = act
                self.lambdaInvertSelection = lambda: self.slot_triggered(invert=True)
                self.actionInvertSelection.triggered.connect(self.lambdaInvertSelection)

    def unload(self):
        self.actionSelectAll.triggered.disconnect(self.lambdaSelectAll)
        self.actionInvertSelection.triggered.disconnect(self.lambdaInvertSelection)

    def slot_triggered(self, invert):
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

            if invert:
                lyr.invertSelection()
            else:
                lyr.selectAll()
