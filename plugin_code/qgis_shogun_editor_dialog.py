# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisShogunEditorDialog
                                  A QGIS plugin
                              -------------------
        begin                : 2025-09
        git sha              : $Format:%H$
        copyright            : (C) 2025 by terrestris
        email                : info@terrestris.de
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
from typing import Optional

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QPixmap

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgis_shogun_editor_dialog_base.ui'))


class QgisShogunEditorDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(QgisShogunEditorDialog, self).__init__(parent)
        self.setupUi(self)
        self._setup_table()
        self._connect_checkbox()

    def _connect_checkbox(self):
        self.checkPublicApps.stateChanged.connect(self._on_public_apps_changed)

    def _on_public_apps_changed(self, state):
        is_public = state == 2
        enabled = not is_public
        self.labelConnectionHeader.setEnabled(enabled)
        self.labelKeycloakUrl.setEnabled(enabled)
        self.entryKeycloakUrl.setEnabled(enabled)
        self.labelClientId.setEnabled(enabled)
        self.entryClientId.setEnabled(enabled)
        self.labelUsername.setEnabled(enabled)
        self.entryUsername.setEnabled(enabled)
        self.labelPassword.setEnabled(enabled)
        self.entryPassword.setEnabled(enabled)
        self.btnLogin.setEnabled(enabled)
        self.labelLoginStatus.setEnabled(enabled)

    def is_public_apps(self) -> bool:
        return self.checkPublicApps.isChecked()

    def _setup_table(self):
        self.applicationsTable.setColumnCount(4)
        self.applicationsTable.setHorizontalHeaderLabels(['Name', 'Erstellt', 'Geändert', 'Layer'])
        self.applicationsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.applicationsTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.applicationsTable.horizontalHeader().setStretchLastSection(True)

    def set_logo(self, pixmap: QPixmap):
        self.labelLogo.setPixmap(pixmap.scaled(
            self.labelLogo.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def get_keycloak_url(self) -> str:
        return self.entryKeycloakUrl.text().strip()

    def set_keycloak_url(self, url: str):
        self.entryKeycloakUrl.setText(url)

    def get_client_id(self) -> str:
        return self.entryClientId.text().strip()

    def set_client_id(self, client_id: str):
        self.entryClientId.setText(client_id)

    def get_username(self) -> str:
        return self.entryUsername.text().strip()

    def get_password(self) -> str:
        return self.entryPassword.text()

    def clear_credentials(self):
        self.entryUsername.clear()
        self.entryPassword.clear()

    def get_graphql_url(self) -> str:
        return self.entryUrl.text().strip()

    def set_graphql_url(self, url: str):
        self.entryUrl.setText(url)

    def set_login_status(self, status: str, is_logged_in: bool):
        self.labelLoginStatus.setText(status)
        if is_logged_in:
            self.labelLoginStatus.setStyleSheet("color: green;")
        else:
            self.labelLoginStatus.setStyleSheet("color: gray;")

    def populate_applications_table(self, applications):
        self.applicationsTable.setRowCount(0)
        for app in applications:
            row_position = self.applicationsTable.rowCount()
            self.applicationsTable.insertRow(row_position)
            row_data = app.to_table_row()
            for col, value in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, app._id)
                self.applicationsTable.setItem(row_position, col, item)

    def get_selected_application_id(self) -> Optional[int]:
        selected_items = self.applicationsTable.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.UserRole)
        return None

    def connect_login_button(self, callback):
        self.btnLogin.clicked.connect(callback)

    def connect_load_button(self, callback):
        self.btnLoad.clicked.connect(callback)

    def connect_cancel_button(self, callback):
        self.btnCancel.clicked.connect(callback)

    def connect_table_double_click(self, callback):
        self.applicationsTable.itemDoubleClicked.connect(callback)

    def switch_to_applications_tab(self):
        self.tabWidget.setCurrentIndex(1)
