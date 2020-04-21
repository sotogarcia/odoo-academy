# -*- coding: utf-8 -*-
#pylint: disable=I0011,W0703,R0903
""" Perform an Odoo database and stored files backup
"""

# --------------------------- REQUIRED LIBRARIES ------------------------------

import argparse
import os
import odoorpc
import time


# -------------------------- MAIN SCRIPT BEHAVIOR -----------------------------


class App(object):
    """ Application main controller, this class has been defined following the
    singleton pattern to ensures only one object can be instantiated.
    """

    __instance = None

    def __new__(cls):
        """ Prevent multiple instances from self (Singleton Pattern)
        """

        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance.name = "The one"
        return cls.__instance

    def __init__(self):
        self._server_host = None
        self._server_port = None
        self._db_name = None
        self._admin_pwd = None
        self._file_path = None
        self._file_name = None

    def _argparse(self):
        """ Detines an user-friendly command-line interface and proccess its
        arguments.
        """

        description = u'Perform an Odoo database and stored files backup.'

        parser = argparse.ArgumentParser(description)
        parser.add_argument('database', metavar='database', type=str,
                            help='database name to perform a backup')

        parser.add_argument('-s', '--server', type=str, metavar='server',
                            help='odoo server host (ip or domain)',
                            default='127.0.0.1')

        parser.add_argument('-p', '--port', type=str, metavar='port',
                            help='odoo server port', default='8069')

        parser.add_argument('-a', '--password', type=str, metavar='password',
                            help='odoo admin password', default='admin')

        parser.add_argument('-d', '--directory', type=str, metavar='directory',
                            help='directory in which data will be saved',
                            default='.')

        parser.add_argument('-f', '--file', type=str, metavar='filename',
                            help='file in which data will be saved',
                            default=None)


        args = parser.parse_args()


        # Build and store name for output file
        if args.file is not None:
            self._file_name = args.file
        else:
            self._file_name = u'%s_%s.zip' % (
                args.database, time.strftime('%Y-%m-%d_%H-%M-%S'))

        # Store other variables
        self._server_host = args.server
        self._server_port = args.port
        self._db_name = args.database
        self._admin_pwd = args.password
        self._file_path = os.path.abspath(args.directory)


    def _backup(self):
        """ Performs the conversion from doc to docx
        """

        new_path = os.path.join(self._file_path, self._file_name)

        try:

            # print('server_host ' + self._server_host)
            # print('server_port ' + self._server_port)
            # print('db_name ' + self._db_name)
            # print('admin_pwd ' + self._admin_pwd)
            # print('file_path ' + self._file_path)
            # print('new_path ' + new_path)

            odoo = odoorpc.ODOO(self._server_host, port=self._server_port)

            timeout_backup = odoo.config['timeout']
            odoo.config['timeout'] = 600
            dump = odoo.db.dump(self._admin_pwd, self._db_name)
            odoo.config['timeout'] = timeout_backup

            with open(new_path, 'wb') as dump_zip:
                dump_zip.write(dump.read())

        except Exception as ex:
            print(ex)
        else:
            print(u'New file %s has been written.' % new_path)

    def main(self):
        """ The main application behavior, this method should be used to
        start the application.
        """

        self._argparse()
        self._backup()


# --------------------------- SCRIPT ENTRY POINT ------------------------------

App().main()
