# -*- coding: utf-8 -*-
"""
***************************************************************************
    An httplib2 replacement that uses QgsNetworkAccessManager

    ---------------------
    Date                 : August 2016
    Copyright            : (C) 2016 Boundless, http://boundlessgeo.com
    Email                : apasotti at boundlessgeo dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

Minor changes by J. Grieb (jgrieb (at) terrestris.de) in 2018 for the
shogun-editor plugin by terrestris GmbH & Co. KG (https://www.terrestris.de/en/)
-> for re-using purposes better use the original code
"""


__author__ = 'Alessandro Pasotti'
__date__ = 'August 2016'

import sys

if sys.version_info[0] >= 3:
    from qgis.PyQt.QtCore import QUrl
    from qgis.PyQt.QtCore import pyqtSlot, QEventLoop
    from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
    import urllib
else:
    from PyQt4.QtCore import QUrl
    from PyQt4.QtCore import pyqtSlot, QEventLoop
    from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply
    import urllib2

from qgis.core import QgsNetworkAccessManager, QgsAuthManager, QgsMessageLog

# FIXME: ignored
DEFAULT_MAX_REDIRECTS = 4

class RequestsException(Exception):
    pass

class RequestsExceptionTimeout(RequestsException):
    pass

class RequestsExceptionConnectionError(RequestsException):
    pass

class Map(dict):
    """
    Example:
    m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """
    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]


class Response(Map):
    pass

PYTHON_VERSION = sys.version_info[0]

class NetworkAccessManager():
    """
    This class mimicks httplib2 by using QgsNetworkAccessManager for all
    network calls.

    The return value is a tuple of (response, content), the first being and
    instance of the Response class, the second being a string that contains
    the response entity body.

    Parameters
    ----------
    debug : bool
        verbose logging if True
    exception_class : Exception
        Custom exception class

    Usage
    -----
    ::
        nam = NetworkAccessManager(authcgf)
        try:
            (response, content) = nam.request('http://www.example.com')
        except RequestsException, e:
            # Handle exception
            pass


    """


    def __init__(self, authid=None, disable_ssl_certificate_validation=False, exception_class=None, debug=True):
        self.disable_ssl_certificate_validation = disable_ssl_certificate_validation
        self.authid = authid
        self.reply = None
        self.debug = debug
        self.exception_class = exception_class
        self.cookie = None
        self.basicauth = None

    def setBasicauth(self, encodedString):
        self.basicauth = encodedString

    def setCookie(self, cookie):
        self.cookie = cookie

    def msg_log(self, msg):
        if self.debug:
            QgsMessageLog.logMessage(msg, "NetworkAccessManager")

    def request(self, url, method="GET", body=None, headers=None, redirections=DEFAULT_MAX_REDIRECTS, connection_type=None, authenticate = True):
        """
        Make a network request by calling QgsNetworkAccessManager.
        redirections argument is ignored and is here only for httplib2 compatibility.
        """
        self.msg_log(u'http_call request: {0}'.format(url))
        self.http_call_result = Response({
            'status': 0,
            'status_code': 0,
            'status_message': '',
            'text' : '',
            'ok': False,
            'headers': {},
            'reason': '',
            'exception': None,
        })
        req = QNetworkRequest()
        req.setAttribute(QNetworkRequest.CookieSaveControlAttribute, QNetworkRequest.Manual)
        req.setAttribute(QNetworkRequest.CookieLoadControlAttribute, QNetworkRequest.Manual)
        # Avoid double quoting form QUrl
        if PYTHON_VERSION >= 3:
            url = urllib.parse.unquote(url)
        else:
            url = urllib2.unquote(url)
        req.setUrl(QUrl(url))

        if self.cookie is not None:
            if headers is not None:
                headers['Cookie'] = self.cookie
            else:
                headers = {'Cookie':self.cookie}

        if self.basicauth is not None and authenticate:
            if headers is not None:
                headers['Authorization'] = self.basicauth
            else:
                headers = {'Authorization':self.basicauth}

        if headers is not None:
            # This fixes a wierd error with compressed content not being correctly
            # inflated.
            # If you set the header on the QNetworkRequest you are basically telling
            # QNetworkAccessManager "I know what I'm doing, please don't do any content
            # encoding processing".
            # See: https://bugs.webkit.org/show_bug.cgi?id=63696#c1
            try:
                del headers['Accept-Encoding']
            except KeyError:
                pass
            for k, v in headers.items():
                if PYTHON_VERSION >= 3:
                    if isinstance(k, str):
                        k = k.encode('utf-8')
                    if isinstance(v, str):
                        v = v.encode('utf-8')
                req.setRawHeader(k, v)

        if self.authid:
            self.msg_log("Update request w/ authid: {0}".format(self.authid))
            QgsAuthManager.instance().updateNetworkRequest(req, self.authid)
        if self.reply is not None and self.reply.isRunning():
            self.reply.close()
        if method.lower() == 'delete':
            func = getattr(QgsNetworkAccessManager.instance(), 'deleteResource')
        else:
            func = getattr(QgsNetworkAccessManager.instance(), method.lower())
        # Calling the server ...
        # Let's log the whole call for debugging purposes:
        self.msg_log("Sending %s request to %s" % (method.upper(), req.url().toString()))
        headers = {str(h): str(req.rawHeader(h)) for h in req.rawHeaderList()}
        for k, v in headers.items():
            self.msg_log("%s: %s" % (k, v))
        if method.lower() in ['post', 'put']:
            if PYTHON_VERSION >= 3:
                if isinstance(body, str):
                    body = body.encode('utf-8')
            self.reply = func(req, body)
        else:
            self.reply = func(req)
        if self.authid:
            self.msg_log("Update reply w/ authid: {0}".format(self.authid))
            QgsAuthManager.instance().updateNetworkReply(self.reply, self.authid)

        self.reply.sslErrors.connect(self.sslErrors)
        self.reply.finished.connect(self.replyFinished)

        # Call and block
        self.el = QEventLoop()
        self.reply.finished.connect(self.el.quit)
        self.reply.downloadProgress.connect(self.downloadProgress)

        # Catch all exceptions (and clean up requests)
        try:
            self.el.exec_()
            # Let's log the whole response for debugging purposes:
            self.msg_log("Got response %s %s from %s" % \
                        (self.http_call_result.status_code,
                         self.http_call_result.status_message,
                         self.reply.url().toString()))
            headers = {str(h): str(self.reply.rawHeader(h)) for h in self.reply.rawHeaderList()}
            for k, v in headers.items():
                self.msg_log("%s: %s" % (k, v))
            if len(self.http_call_result.text) < 1024:
                self.msg_log("Payload :\n%s" % self.http_call_result.text)
            else:
                self.msg_log("Payload is > 1 KB ...")
        except Exception as e:
            raise e
        finally:
            if self.reply is not None:
                if self.reply.isRunning():
                    self.reply.close()
                self.msg_log("Deleting reply ...")
                self.reply.deleteLater()
                self.reply = None
            else:
                self.msg_log("Reply was already deleted ...")
        if not self.http_call_result.ok:
            if self.http_call_result.exception and not self.exception_class:
                raise self.http_call_result.exception
            else:
                raise self.exception_class(self.http_call_result.reason)
        return (self.http_call_result, self.http_call_result.text)

    #@pyqtSlot()
    def downloadProgress(self, bytesReceived, bytesTotal):
        """Keep track of the download progress"""
        #self.msg_log("downloadProgress %s of %s ..." % (bytesReceived, bytesTotal))
        pass

    #@pyqtSlot()
    def replyFinished(self):
        err = self.reply.error()
        httpStatus = self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        httpStatusMessage = self.reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute)
        self.http_call_result.status_code = httpStatus
        self.http_call_result.status = httpStatus
        self.http_call_result.status_message = httpStatusMessage
        for k, v in self.reply.rawHeaderPairs():
            self.http_call_result.headers[str(k)] = str(v)
            self.http_call_result.headers[str(k).lower()] = str(v)
        if err != QNetworkReply.NoError:
            msg = "Network error #{0}: {1}".format(
                self.reply.error(), self.reply.errorString())
            self.http_call_result.reason = msg
            self.http_call_result.ok = False
            self.msg_log(msg)
            if err == QNetworkReply.TimeoutError:
                self.http_call_result.exception = RequestsExceptionTimeout(msg)
            elif err == QNetworkReply.ConnectionRefusedError:
                self.http_call_result.exception = RequestsExceptionConnectionError(msg)
            else:
                self.http_call_result.exception = RequestsException(msg)
        else:
            # since Python 3 readAll() returns a PyQt5.QByteArray, we
            # want only the data
            if PYTHON_VERSION >= 3:
                self.http_call_result.text = self.reply.readAll().data().decode('utf-8')
            else:
                self.http_call_result.text = str(self.reply.readAll())
            self.http_call_result.ok = True
        self.reply.deleteLater()

    #@pyqtSlot()
    def sslErrors(self, reply, ssl_errors):
        """
        Handle SSL errors, logging them if debug is on and ignoring them
        if disable_ssl_certificate_validation is set.
        """
        if ssl_errors:
            for v in ssl_errors:
                self.msg_log("SSL Error: %s" % v)
        if self.disable_ssl_certificate_validation:
            reply.ignoreSslErrors()
