# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisShogunEditor
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
import json
import time
from typing import Dict, Optional

from qgis.PyQt.QtCore import QObject, pyqtSignal, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import (
    Qgis,
    QgsMessageLog,
    QgsNetworkAccessManager
)


class KeycloakAuth(QObject):
    """OIDC Password Grant Flow Handler with auto-refresh."""

    login_successful = pyqtSignal(str)
    login_failed = pyqtSignal(str)

    DEFAULT_PROVIDER_URL = "https://gdaw-intern2024.intranet.terrestris.de/realms/gdawasser"
    DEFAULT_CLIENT_ID = "qgis-shogun-editor"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._provider_url = self.DEFAULT_PROVIDER_URL
        self._client_id = self.DEFAULT_CLIENT_ID
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._discovery_doc: Optional[Dict] = None
        self._userinfo: Optional[Dict] = None

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None and time.time() < self._token_expires_at

    @property
    def userinfo(self) -> Optional[Dict]:
        return self._userinfo

    def configure(self, provider_url: str, client_id: str) -> None:
        self._provider_url = provider_url.rstrip('/')
        self._client_id = client_id

    def get_provider_url(self) -> str:
        return self._provider_url

    def get_client_id(self) -> str:
        return self._client_id

    def _load_discovery(self) -> bool:
        discovery_url = f"{self._provider_url}/.well-known/openid-configuration"
        request = QNetworkRequest(QUrl(discovery_url))

        reply = self._sync_request(request)

        if reply is None or reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) != 200:
            error = f"Failed to load OIDC discovery from {discovery_url}"
            QgsMessageLog.logMessage(error, 'QgisShogunEditor', Qgis.Warning)
            return False

        try:
            data = reply.readAll().data()
            self._discovery_doc = json.loads(data)
            QgsMessageLog.logMessage(
                f"OIDC discovery loaded: {self._discovery_doc.get('issuer')}",
                'QgisShogunEditor',
                Qgis.Info
            )
            return True
        except json.JSONDecodeError as e:
            error = f"Failed to parse OIDC discovery: {e}"
            QgsMessageLog.logMessage(error, 'QgisShogunEditor', Qgis.Warning)
            return False

    def _sync_request(self, request: QNetworkRequest, data: bytes = None, timeout_ms: int = 10000):
        from qgis.PyQt.QtCore import QEventLoop, QTimer
        from qgis.core import QgsNetworkAccessManager

        loop = QEventLoop()
        reply = QgsNetworkAccessManager.instance().post(request, data) if data else QgsNetworkAccessManager.instance().get(request)
        reply.finished.connect(loop.quit)

        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        timeout.start(timeout_ms)

        loop.exec_()
        timeout.stop()

        if reply.error() != 0 and reply.error() != QgsNetworkAccessManager.NoError:
            QgsMessageLog.logMessage(f"Network error: {reply.errorString()}", 'QgisShogunEditor', Qgis.Warning)

        return reply

    def _get_token_url(self) -> Optional[str]:
        if not self._discovery_doc and not self._load_discovery():
            return None
        return self._discovery_doc.get('token_endpoint')

    def _get_userinfo_url(self) -> Optional[str]:
        if not self._discovery_doc and not self._load_discovery():
            return None
        return self._discovery_doc.get('userinfo_endpoint')

    def login(self, username: str, password: str) -> bool:
        token_url = self._get_token_url()
        if not token_url:
            self.login_failed.emit("Could not determine token endpoint")
            return False

        post_data = f"grant_type=password"
        post_data += f"&client_id={self._client_id}"
        post_data += f"&username={username}"
        post_data += f"&password={password}"

        request = QNetworkRequest(QUrl(token_url))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            'application/x-www-form-urlencoded'
        )

        reply = self._sync_request(request, post_data.encode(), 30000)

        if reply is None:
            self.login_failed.emit("Network error: No response")
            return False

        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if status == 200:
            try:
                response = json.loads(reply.readAll().data())
                self._access_token = response.get('access_token')
                self._refresh_token = response.get('refresh_token')
                expires_in = response.get('expires_in', 300)
                self._token_expires_at = time.time() + expires_in - 30

                self._fetch_userinfo()

                QgsMessageLog.logMessage(
                    f"Login successful, token expires in {expires_in}s",
                    'QgisShogunEditor',
                    Qgis.Info
                )
                self.login_successful.emit(self._access_token)
                return True
            except json.JSONDecodeError:
                self.login_failed.emit("Invalid token response")
                return False
        elif status == 401 or status == 400:
            try:
                error_data = json.loads(reply.readAll().data())
                error_desc = error_data.get('error_description', error_data.get('error', 'Login failed'))
                self.login_failed.emit(error_desc)
            except json.JSONDecodeError:
                self.login_failed.emit(f"Login failed (HTTP {status})")
            return False
        else:
            self.login_failed.emit(f"HTTP error {status}")
            return False

    def _fetch_userinfo(self) -> None:
        userinfo_url = self._get_userinfo_url()
        if not userinfo_url or not self._access_token:
            return

        request = QNetworkRequest(QUrl(userinfo_url))
        request.setRawHeader(b'Authorization', f'Bearer {self._access_token}'.encode())

        reply = self._sync_request(request, timeout_ms=10000)

        if reply and reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) == 200:
            try:
                self._userinfo = json.loads(reply.readAll().data())
            except json.JSONDecodeError:
                pass

    def refresh_token(self) -> bool:
        if not self._refresh_token:
            return False

        token_url = self._get_token_url()
        if not token_url:
            return False

        post_data = f"grant_type=refresh_token"
        post_data += f"&client_id={self._client_id}"
        post_data += f"&refresh_token={self._refresh_token}"

        request = QNetworkRequest(QUrl(token_url))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            'application/x-www-form-urlencoded'
        )

        reply = self._sync_request(request, post_data.encode(), 15000)

        if reply and reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute) == 200:
            try:
                response = json.loads(reply.readAll().data())
                self._access_token = response.get('access_token')
                self._refresh_token = response.get('refresh_token', self._refresh_token)
                expires_in = response.get('expires_in', 300)
                self._token_expires_at = time.time() + expires_in - 30
                return True
            except json.JSONDecodeError:
                return False
        return False

    def is_token_expiring_soon(self) -> bool:
        return time.time() >= self._token_expires_at

    def get_token_remaining_seconds(self) -> int:
        remaining = int(self._token_expires_at - time.time())
        return max(0, remaining)

    def logout(self) -> None:
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = 0
        self._userinfo = None

    def get_auth_header(self) -> Dict[str, str]:
        if not self._access_token:
            return {}

        if self.is_token_expiring_soon() and self._refresh_token:
            if self.refresh_token():
                QgsMessageLog.logMessage(
                    f"Token refreshed, {self.get_token_remaining_seconds()}s remaining",
                    'QgisShogunEditor',
                    Qgis.Info
                )

        if self._access_token:
            return {'Authorization': f'Bearer {self._access_token}'}
        return {}
