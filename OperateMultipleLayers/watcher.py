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

from qgis.PyQt.QtCore import QObject


class WatcherBase(QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.iface = parent.iface
        self.plugin_name = parent.plugin_name
        self.current_layer = parent.current_layer

    def push_crs_used(self):
        self.iface.messageBar().pushInfo(self.plugin_name,
                self.tr('Operated on current layer CRS (%s)') %
                        self.current_layer.crs().authid())
