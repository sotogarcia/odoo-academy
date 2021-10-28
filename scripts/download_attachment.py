# -*- coding: utf-8 -*-
#pylint: disable=I0011,W0703,R0903,R0902
""" Download attachments from Odoo
"""


# --------------------------- REQUIRED LIBRARIES ------------------------------


import argparse
import uuid
import odoorpc
import magic
import os
import sys
import locale
import base64
import hashlib
import re
import urllib
import base64
if sys.version_info >= (3, 0):
    import urllib.parse as urlparse
else:
    import urlparse


# -------------------------- MAIN SCRIPT BEHAVIOR -----------------------------


class App(object):
    """ Application main controller, this class has been defined following the
    singleton pattern to ensures only one object can be instantiated.
    """

    __instance = None


    def __new__(cls):
        """ Prevent multiple instances from self (Singleton Pattern)
        """

        if cls.__instance == None:
            cls.__instance = object.__new__(cls)
            cls.__instance.name = "The one"
        return cls.__instance


    def __init__(self):
        self._server = None
        self._port = None
        self._database = None
        self._user = None
        self._password = None
        self._odoo = None

        self._id = None
        self._output = None

        self._cp = locale.getpreferredencoding()


    def _argparse(self):
        """ Detines an user-friendly command-line interface and proccess its
        arguments.
        """

        description = u'Import a files into Odoo ir.attachement records'

        parser = argparse.ArgumentParser(description)
        # parser.add_argument('file', metavar='file', type=str,
        #                     help=u'path of the resource file will be stored')

        parser.add_argument(metavar='id', type=int, dest='id',
                            help=u'attachment identifier')

        parser.add_argument('-s', '--server', type=str, dest='server',
                            default=u'localhost',
                            help=u'Odoo server address will be used to connect')

        parser.add_argument('-n', '--port', type=str, dest='port',
                            default=u'8069',
                            help=u'Odoo server port will be used to connect')

        parser.add_argument('-u', '--user', type=str, dest='user',
                            default=u'admin',
                            help=u'user will be used to login in Odoo server')

        parser.add_argument('-p', '--password', type=str, dest='password',
                            default=u'admin',
                            help=u'password will be used to login in Odoo server')

        parser.add_argument('-d', '--database', type=str, dest='database',
                            default=u'odoo_service',
                            help=u'name of the database will be used to store the resource')

        parser.add_argument('-o', '--output', type=str, dest='output',
                            default=u'Enunciado.pdf',
                            help=u'destination file')


        args = parser.parse_args()

        self._server = args.server
        self._port = args.port
        self._user = args.user
        self._password = args.password
        self._database = args.database
        self._id = args.id
        self._output = os.path.abspath(args.output)

    def _connect(self):
        """ Connects to a Odoo server """

        result = False


        try:
            self._odoo = odoorpc.ODOO(self._server, port=self._port)
            result = True
        except Exception as ex:
            print(ex)

        return result


    def _login(self):
        """ Tries to login with user and password or renew session
        """
        result = False

        self._odoo.logout()

        try:
            self._odoo.login(self._database, self._user, self._password)
            result = True
        except Exception:
            pass

        if not result:
            try:
                self._odoo.login(self._database)
                result = True
            except Exception:
                pass

        return result


    def _logout(self):
        """ Loggout from Odoo server """
        self._odoo.logout()

    def _search_one(self):
        domain = []

        if self._id:
            domain.append(('id', '=', self._id))

        test_ids = self._odoo.env['ir.attachment'].search(domain)

        return test_ids[0] if test_ids else 0


    def _download_attach(self, attach_id):
        return self._odoo.report.download(
            self._report,
            [attach_id]
        )


    def _save_attach(self, report):
        with open(self._output, 'wb') as report_file:
            report_file.write(report.read())


    def main(self):
        """ The main application behavior, this method should be used to
        start the application.
        """
        result = -1

        self._argparse()

        if self._id:
            if self._connect() and self._login():

                attach_id = self._search_one()
                if attach_id > 0:

                    attach = self._odoo.env['ir.attachment']
                    attach = attach.browse(attach_id)
                    # attach = self._download_attach(attach_id)

                    with open('d:\\file.png', 'wb') as f:
                        f.write(base64.b64decode(attach.datas))

                self._logout()

            else:
                print(u'Connection could not be established')

        else:
            print(u'Please type an ID or a title, see --help')

        sys.exit(result)

# --------------------------- SCRIPT ENTRY POINT ------------------------------

App().main()


