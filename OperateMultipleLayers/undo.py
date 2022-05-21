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

from qgis.core import QgsVectorLayer
from .watcher import WatcherBase


class UndoWatcher(WatcherBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.stack = self.current_layer.undoStack()
        self.prev_index = self.stack.index()
        self.last_command = self.stack.command(self.stack.count() - 1)
        self.stack.indexChanged.connect(self.slot_indexChanged)

    def slot_indexChanged(self, index):
        if index < self.prev_index:
            self.parent.is_undoing = True
            # Undo
            if index >= self.parent.undoable_index:
                self.undo(self.stack.text(index))
        elif (index < self.stack.count() or
                self.stack.command(index - 1) is self.last_command):
            self.parent.is_undoing = True
            # Redo
            if self.prev_index >= self.parent.undoable_index:
                self.undo(self.stack.text(self.prev_index), True)
        else:
            self.parent.is_undoing = False
            self.last_command = self.stack.command(index - 1)
        self.prev_index = index

    def undo(self, text, is_redo=False):
        layers = self.iface.layerTreeView().selectedLayers()
        
        for lyr in layers:
            if not (isinstance(lyr, QgsVectorLayer) and lyr.isEditable()):
                continue
            if lyr is self.iface.activeLayer():
                continue

            if is_redo:
                if lyr.undoStack().redoText() == text:
                    lyr.undoStack().redo()
            else:
                if lyr.undoStack().undoText() == text:
                    lyr.undoStack().undo()
