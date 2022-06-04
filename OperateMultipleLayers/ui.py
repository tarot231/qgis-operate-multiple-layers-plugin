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

from qgis.PyQt.QtWidgets import *
from qgis.core import Qgis


class ConfigDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.checkInvisible = QCheckBox(self.tr('Skip invisible layers (except current layer)'))
        self.checkRecursive = QCheckBox(self.tr('Apply operations to layers in selected groups'))
        if Qgis.QGIS_VERSION_INT < 30400:
            self.checkRecursive.setEnabled(False)

        buttonBox = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                accepted=self.accept, rejected=self.reject)

        vbox = QVBoxLayout()
        vbox.addWidget(self.checkInvisible)
        vbox.addWidget(self.checkRecursive)
        vbox.addWidget(buttonBox)

        self.setLayout(vbox)
        # https://stackoverflow.com/q/696209
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def setValue(self, dict_value):
        if 'skip_invisible' in dict_value:
            self.checkInvisible.setChecked(dict_value['skip_invisible'])
        if 'recursive' in dict_value:
            self.checkRecursive.setChecked(dict_value['recursive'])

    def getValue(self):
        dict_value = {}
        dict_value['skip_invisible'] = self.checkInvisible.isChecked()
        dict_value['recursive'] = self.checkRecursive.isChecked()
        return dict_value


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    ConfigDialog().exec()
