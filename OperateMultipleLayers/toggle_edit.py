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

from qgis.core import QgsVectorLayer, Qgis
from .watcher import WatcherBase


class ToggleEditingWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)
        if Qgis.QGIS_VERSION_INT < 32200:
            self.iface.actionToggleEditing().toggled.connect(
                    self.slot_toggled)

    def slot_toggled(self, checked):
        tools = self.iface.vectorLayerTools()

        layers = self.iface.layerTreeView().selectedLayers()
        
        for lyr in layers:
            if not isinstance(lyr, QgsVectorLayer):
                continue
            if lyr is self.iface.activeLayer():
                continue

            if checked:
                if (not lyr.isEditable()
                        and lyr.dataProvider().capabilitiesString()):
                    tools.startEditing(lyr)
            else:
                if lyr.isEditable():
                    tools.stopEditing(lyr)
