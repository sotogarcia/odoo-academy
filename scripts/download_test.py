# -*- coding: utf-8 -*-
#pylint: disable=I0011,W0703,R0903,R0902
""" Import files into Odoo ir.attachement records
"""


# --------------------------- REQUIRED LIBRARIES ------------------------------


from pprint import pprint
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
import mimetypes
if sys.version_info >= (3, 0):
    import urllib.parse as urlparse
else:
    import urlparse


WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

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
        self._server = None
        self._port = None
        self._database = None
        self._user = None
        self._password = None
        self._odoo = None

        self._title = None
        self._id = None
        self._report = None
        self._output = None
        self._resources = None
        self._downloaded = []
        self._verbose = False
        self._attachments = False
        self._solutions = False

        self._cp = locale.getpreferredencoding()

    def _argparse(self):
        """ Detines an user-friendly command-line interface and proccess its
        arguments.
        """

        description = u'Import a files into Odoo ir.attachement records'

        parser = argparse.ArgumentParser(description)
        # parser.add_argument('file', metavar='file', type=str,
        #                     help=u'path of the resource file will be stored')

        msg = u'Odoo server address will be used to connect'
        parser.add_argument('-s', '--server', type=str, dest='server',
                            default=u'localhost', help=msg)

        msg = u'Odoo server port will be used to connect'
        parser.add_argument('-n', '--port', type=str, dest='port',
                            default=u'8069', help=msg)

        msg = u'user will be used to login in Odoo server'
        parser.add_argument('-u', '--user', type=str, dest='user',
                            default=u'admin', help=msg)

        msg = u'password will be used to login in Odoo server'
        parser.add_argument('-p', '--password', type=str, dest='password',
                            default=u'admin', help=msg)

        msg = u'name of the database will be used to store the resource'
        parser.add_argument('-d', '--database', type=str, dest='database',
                            default=u'odoo_service', help=msg)

        msg = u'test identifier'
        parser.add_argument('-i', '--id', type=int, dest='id',
                            default=0, help=msg)

        msg = u'test title'
        parser.add_argument('-t', '--tittle', type=str, dest='title',
                            default=None, help=msg)

        msg = u'available test report'
        # default=u'academy_tests.view_academy_tests_qweb',
        parser.add_argument('-r', '--report',
                            type=str, dest='report', help=msg)

        msg = u'destination file'
        parser.add_argument('-o', '--output', type=str, dest='output',
                            default=None, help=msg)

        msg = u'download all attachments'
        parser.add_argument('-a', '--attachs', dest='attachments',
                            action='store_true', help=msg)

        msg = u'create additional solutions table text file'
        parser.add_argument('-l', '--table', dest='solutions',
                            action='store_true', help=msg)

        msg = u'show process information'
        parser.add_argument('-v', '--verbose', dest='verbose',
                            action='store_true', help=msg)

        args = parser.parse_args()

        self._server = args.server
        self._port = args.port
        self._user = args.user
        self._password = args.password
        self._database = args.database
        self._report = args.report
        self._attachments = args.attachments
        self._verbose = args.verbose
        self._solutions = args.solutions

        self._ensure_paths(args)
        self._ensure_target(args)

    def _print(self, str_format, *args):
        if self._verbose:
            print(str_format.format(*args))

    def _ensure_paths(self, args):
        """ Computes output file path and resources folder path
        """
        if not args.output:
            ext = 'pdf' if self._report else 'txt'
            fname = 'Enunciado.{}'.format(ext)
            self._output = os.path.abspath(fname)
        else:
            self._output = os.path.abspath(args.output)

        dn = os.path.dirname(self._output)
        sep = os.path.sep
        self._resources = '{d}{s}Recursos{s}'.format(d=dn, s=sep)
        if not os.path.exists(self._resources):
            os.mkdir(self._resources)

    def _ensure_target(self, args):
        """ Test can be specified by ID, by title or by existing file
        """
        if args.id > 0:
            self._id = args.id
        elif not self._title:
            files = [item for item in os.listdir(u'.')
                     if item.endswith(u'.ID')]
            if files:
                self._id = int(files[0][:-3])
                self._read_id_file(files[0])
                print(u'Using file ' + files[0] + ' and ' + self._report)

        if args.title:
            self._title = args.title.decode(self._cp, errors=u'replace')

    def _read_id_file(self, fname):
        """ Read specifications from ID file """
        with open(fname, 'r') as finput:  # open the file
            lines = finput.readlines()
            for line_raw in lines:
                line = line_raw.decode('utf-8', errors='replace')
                if re.match(r'^report\= *[^ ]+ *$', line, re.IGNORECASE):
                    self._report = line.replace(u'report=', u'').strip()

    def _connect(self):
        """ Connects to a Odoo server """

        result = False

        try:
            self._odoo = odoorpc.ODOO(self._server, port=self._port)
            result = True
        except Exception as ex:
            print(ex)

        return result

    # def _connect(self):
    #     """ Connects to a Odoo server """

    #     result = False

    #     try:
    #         url = "https://test.octavioesxi.ddns.net"
    #         pwd_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    #         pwd_mgr.add_password(None, url, "sisgap", "Secretillo$4321")
    #         auth_handler = urllib.request.HTTPBasicAuthHandler(pwd_mgr)
    #         opener = urllib.request.build_opener(auth_handler)

    #         self._odoo = odoorpc.ODOO(
    #             'test.octavioesxi.ddns.net', protocol='jsonrpc+ssl', port=443, opener=opener)
    #         result = True
    #     except Exception as ex:
    #         print(ex)

    #     return result

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

        if self._title:
            domain.append(('name', 'ilike', self._title))

        test_ids = self._odoo.env['academy.tests.test'].search(domain)

        return test_ids[0] if test_ids else 0

    def _download_report(self, test_id):
        self._print('Using report {}', self._report)
        action = self._odoo.env.ref(self._report)

        if action.report_type == 'qweb-pdf':
            report = action.render_qweb_pdf([test_id])[0]
            report = report.encode('latin-1')

        elif action.report_type == 'qweb-text':
            report = action.render([test_id])[0]

            report = report.encode('utf-8')
            report = report.replace(UNIX_LINE_ENDING, WINDOWS_LINE_ENDING)

        return report

    def _save_report(self, report, test_id, binary=True):
        mode = 'wb' if binary else 'w'

        self._print('Writing test report to file {}', self._output)

        with open(self._output, mode) as report_file:
            report_file.write(report)

    def _preamble_to_string(self, question, text=None):
        if question.preamble:
            text = (text or '') + question.preamble + '\n'

        return (text or '')

    def _image_to_string(self, question, text=None):
        lines = ''
        for attach in question.ir_attachment_ids:
            ext = mimetypes.guess_extension(attach.mimetype)
            fname = '{}{}'.format(attach.id, ext)
            line = '![{}]({})\n'.format(attach.name, fname)
            lines = lines + line

        if lines:
            text = (text or '') + lines

        return (text or '')

    def _description_to_string(self, question, text=None):
        if question.description:
            desc = question.description
            lines = '> ' + re.sub(r'[\r\n]+', '\n> ', desc)
            text = (text or '') + lines + '\n'

        return (text or '')

    def _question_to_string(self, question, text=None):
        return '{}. {}\n'.format(question.id, question.name)

    def _answer_to_string(self, answer, index, text=None):
        letter = 'x' if answer.is_correct else chr(97 + index)
        return '{}) {}\n'.format(letter, answer.name)

    def _download_attachment(self, attach):
        ext = mimetypes.guess_extension(attach.mimetype)
        fname = '{}{}{}'.format(self._resources, attach.id, ext)
        with open(fname, 'wb') as f:
            f.write(base64.b64decode(attach.datas))

    def _download_attachments(self, question):
        for attach in question.ir_attachment_ids:
            if attach.id not in self._downloaded:
                self._print('Downloading attachment {}', attach.id)
                self._downloaded.append(attach.id)
                self._download_attachment(attach)
            else:
                self._print('Skiping attachment {}', attach.id)

    def _retain_solution(self, solutions, answer, qindex, aindex):
        if answer.is_correct:
            letter = chr(65 + aindex)
            qindex = qindex + 1

            # Answer can have more than one solution
            if qindex in solutions.keys():
                value = solutions[qindex] + ', ' + letter
                solutions[qindex] = value
            else:
                solutions[qindex] = letter

    def _write_solutions(self, solutions):
        padlen = len(str(list(solutions.keys())[-1]))
        pattern = '{:>%d} — {}\n' % padlen

        dirname = os.path.dirname(self._output)
        fpath = os.path.join(dirname, 'Solución.txt')
        self._print('Writing answers table to file {}', fpath)
        with open(fpath, 'w', encoding='utf8') as file:
            for k, v in solutions.items():
                line = pattern.format(k, v)
                file.write(line)

    def _write_statement(self, text):
        self._print('Writing statement to file {}', self._output)
        with open(self._output, 'w', encoding='utf8') as file:
            file.write(text)

    def _download_as_text(self, test_id):
        test = self._odoo.env['academy.tests.test']
        links = test.browse(test_id).question_ids

        title = test.browse(test_id).name
        self._print('Descargando {}'.format(title))

        text = ''  # Statement text
        solutions = {}
        for qindex, link in enumerate(links):
            question = link.question_id

            self._print('Reading question {}', question.id)

            if self._attachments:
                self._download_attachments(question)

            text = text + self._description_to_string(question)
            text = text + self._image_to_string(question)
            text = text + self._preamble_to_string(question)
            text = text + self._question_to_string(question)

            for aindex, answer in enumerate(question.answer_ids):
                text = text + self._answer_to_string(answer, aindex)
                self._retain_solution(solutions, answer, qindex, aindex)

            text = text + '\n'

        if text:
            self._write_statement(text)

        if self._solutions and solutions:
            self._write_solutions(solutions)

    def _resequence(self, test_id):
        test = self._odoo.env['academy.tests.test'].browse(test_id)
        test.resequence()

    def main(self):
        """ The main application behavior, this method should be used to
        start the application.
        """
        result = -1

        self._argparse()

        if (self._id or self._title) and self._connect():

            if self._login():

                test_id = self._search_one()

                if test_id > 0:

                    self._resequence(test_id)

                    if self._report:
                        report = self._download_report(test_id)
                        self._save_report(report, test_id)
                    else:
                        self._download_as_text(test_id)

                self._logout()

        else:
            print(u'Please type an ID or a title, see --help')

        sys.exit(result)

# --------------------------- SCRIPT ENTRY POINT ------------------------------


App().main()
