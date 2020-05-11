# -*- coding: utf-8 -*-
#pylint: disable=I0011
""" Gets the text questions and answers from Odoo postgres database
"""

# --------------------------- REQUIRED LIBRARIES ------------------------------

import argparse
import psycopg2
import locale
import chardet
import io
import os

# ------------------------------- DECORATORS ----------------------------------

class ClassPropertyDescriptor(object):
    #pylint: disable=I0011,R0903,C0111

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self

def classproperty(func):
    #pylint: disable=I0011,C0111
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


# ----------------------------- ENTITY CLASSES --------------------------------

class Entity(object):
    #pylint: disable=I0011,E0213,C0111,R0903

    _conn = None

    @property
    def conn(self):
        return self._conn

    @conn.setter
    def conn(cls, value):
        cls._conn = value


class Attachment(Entity):
    #pylint: disable=I0011,R0903,C0111

    @property
    def name(self):
        return self._name

    @property
    def url(self):
        return self._is_correct

    def __init__(self, _id, name, url):
        super(Attachment, self).__init__()

        self._id = _id
        self._name = name
        self._url = url

    @classmethod
    def from_question(cls, question_id):
        attachments = []

        conn_pattern = u'''
            SELECT
                ata.id,
                ata.name,
                ata.store_fname  || regexp_replace(mimetype, '^[^/]+/', '.') as url
            FROM
                    ir_attachment AS ata
            inner join academy_tests_question_ir_attachment_rel as rel on rel.attachment_id = ata."id"
            INNER JOIN academy_tests_question AS atq ON rel.question_id = atq."id"
            WHERE atq."id" = {}
            ORDER BY
                    atq."id" ASC;
        '''
        conn_string = conn_pattern.format(question_id)
        cur = cls.conn.cursor()
        cur.execute(conn_string)
        rows = cur.fetchall()

        # assert rows, u'There is not any attachment in question %s' % question_id

        for row in rows:
            attachment = Attachment(row[0], row[1], row[2])
            attachments.append(attachment)

        return attachments

    def to_markdown(self):
        name = self._name or ''
        url = self._url or ''
        return '![' + name  + '](' + str(self._id) + ')\n'
        # To download attachment http://server:port/web/content/{id}

    def __str__(self):
        return self._name


class Answer(Entity):
    #pylint: disable=I0011,R0903,C0111

    @property
    def name(self):
        return self._name

    @property
    def is_correct(self):
        return self._is_correct


    def __init__(self, _id, name, is_correct=False):
        super(Answer, self).__init__()

        self._id = _id
        self._name = name
        self._is_correct = is_correct

    @classmethod
    def from_question(cls, question_id):
        answers = []

        conn_pattern = u'''
            SELECT
                ata.id,
                ata.name,
                ata.is_correct
            FROM
                academy_tests_answer AS ata
            INNER JOIN academy_tests_question AS atq ON ata.question_id = atq."id"
            WHERE atq."id" = {}
            ORDER BY
                atq."id" ASC,
                ata."sequence";
        '''
        conn_string = conn_pattern.format(question_id)
        cur = cls.conn.cursor()
        cur.execute(conn_string)
        rows = cur.fetchall()

        # assert rows, u'There is not any answer in question %s' % question_id

        for row in rows:
            answer = Answer(row[0], row[1], row[2])
            answers.append(answer)

        return answers

    def __str__(self):
        return self._name

class Question(Entity):
    #pylint: disable=I0011,R0903,C0111

    @property
    def name(self):
        return self._name

    @property
    def preamble(self):
        return self._preamble

    @property
    def description(self):
        return self._description

    @property
    def answers(self):
        return self._answers

    @property
    def attachments(self):
        return self._attachments

    #pylint: disable=I0011,R0913
    def __init__(self, _id, name, preamble=None, description=None, answers=None, attachments=None):
        super(Question, self).__init__()

        self._id = _id
        self._name = name
        self._preamble = preamble
        self._description = description
        self._answers = answers or []
        self._attachments = attachments or []

    @classmethod
    def from_test(cls, test_id):
        questions = []

        conn_pattern = u'''
            SELECT
                atq.id,
                atq.name,
                atq.preamble,
                atq.description
            FROM
                academy_tests_question AS atq
            INNER JOIN academy_tests_test_question_rel AS attqr ON attqr.question_id = atq."id"
            INNER JOIN academy_tests_test AS att ON attqr.test_id = att."id"
            WHERE att."id" = {}
            ORDER BY
                att."id" ASC,
                attqr."sequence";
        '''
        conn_string = conn_pattern.format(test_id)
        cur = cls.conn.cursor()
        cur.execute(conn_string)
        rows = cur.fetchall()

        assert rows, u'There is not any question in test %s' % test_id

        for row in rows:
            answers = Answer.from_question(row[0])
            attachments = Attachment.from_question(row[0])
            question = Question(row[0], row[1], row[2], row[3], answers, attachments)
            questions.append(question)

        return questions

    def __str__(self):
        return '{{ id : {}, name : "{}", preamble : "{}", description : "{}" }}'.format(
            self._id,
            self._name,
            self._preamble,
            self._description
        )

class Test(Entity):
    #pylint: disable=I0011,R0903,C0111

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def questions(self):
        return self._questions

    def __init__(self, _id, name, description=None, questions=None):
        super(Test, self).__init__()

        self._id = _id
        self._name = name
        self._description = description
        self._questions = questions or []

    @classmethod
    def browse(cls, test_id):
        conn_pattern = u'SELECT id, name, description FROM academy_tests_test WHERE "id" = {};'
        conn_string = conn_pattern.format(test_id)
        cur = cls.conn.cursor()
        cur.execute(conn_string)
        rows = cur.fetchall()

        assert rows, u'There is not any test with %s' % test_id

        row = rows[0]

        questions = Question.from_test(test_id)
        test = Test(row[0], row[1], row[2], questions)

        return test


    def __str__(self):
        return '{{ id : {}, name : "{}", description : "{}", questions : <{}> }}'.format(
            self._id,
            (self._name),
            (self._description),
            len(self._questions)
        )



# -------------------------- MAIN SCRIPT BEHAVIOR -----------------------------


class App(object):
    #pylint: disable=I0011,R0903
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
        self._host = None
        self._database = None
        self._password = None
        self._user = None
        self._test_id = None
        self._output = None

    def _argparse(self):
        """ Detines an user-friendly command-line interface and proccess its
        arguments.
        """

        # STEP 1: Define the arbument parser
        description = u'Gets questions and answers from Academy Test database'
        parser = argparse.ArgumentParser(description)

        # STEP 2: Determine positional arguments
        parser.add_argument('test_id', metavar='test_id', type=int,
                            help='identifier of the test')

        # STEP 3: Determine non positional arguments
        parser.add_argument('-s', '--server', type=str, dest='host',
                            default='localhost', help='data server host')

        # STEP 3: Determine non positional arguments
        parser.add_argument('-d', '--database', type=str, dest='database',
                            default='odoo_production', help='database name')

        # STEP 3: Determine non positional arguments
        parser.add_argument('-u', '--user', type=str, dest='user',
                            default='odoo', help='database user name')

        # STEP 3: Determine non positional arguments
        parser.add_argument('-p', '--password', type=str, dest='password',
                            default='odoo', help='database password')

        # STEP 3: Determine non positional arguments
        parser.add_argument('-o', '--output', type=str, dest='output',
                            default='output.txt', help='output filename')

        args = parser.parse_args()

        self._host = args.host
        self._database = args.database
        self._user = args.user
        self._password = args.password

        if args.test_id == 0:
            files = [item for item in os.listdir(u'.') if item.endswith(u'.ID')]
            if files:
                self._test_id = int(files[0][:-3])
        else:
            self._test_id = args.test_id

        self._output = args.output


    @staticmethod
    def _decode(string, codepage):
        #pylint: disable=I0011,W0702,W0703,C0111
        result = u''

        try:
            result = string.decode('utf-8', errors='replace')
        except:
            try:
                string.decode('utf-8', errors='ignore')
            except Exception as ex:
                print(ex)

        else:
            try:
                result = result.encode(codepage, errors='replace')
            except:
                try:
                    result = result.encode(codepage, errors='ignore')
                except Exception as ex:
                    print(ex)

        return result

    @staticmethod
    def _autodecode(_in_text):
        """ Encode text in UTF-8 """

        if _in_text:
            return _in_text #.decode('utf-8', errors='replace')

        return ''


    def _get_test(self):
        #pylint: disable=I0011,W0703
        """ Main method docstring
        """

        # try:

        conn_pattern = u'dbname=\'{}\' user=\'{}\' host=\'{}\' password=\'{}\''
        conn_string = conn_pattern.format(
            self._database,
            self._user,
            self._host,
            self._password
        )
        print(conn_string)
        conn = psycopg2.connect(conn_string)

        Entity.conn = conn
        test = Test.browse(self._test_id)

        os_encoding = locale.getpreferredencoding()

        with io.open(self._output, 'w', encoding='UTF-8') as text_file:
            text_file.write(self._autodecode(test.name))
            text_file.write(u'\n\n')
            text_file.write(self._autodecode(test.description))
            text_file.write(u'\n')

            question_count = 1
            for question in test.questions:
                # This works but I don't know why

                text_file.write(u'\n')
                for attachment in question.attachments:
                    markdown = attachment.to_markdown()
                    text_file.write(self._autodecode(markdown))

                if question.description:
                    text_file.write(u'\n> {}'.format(self._autodecode(question.description)))

                if question.preamble:
                    text_file.write(u'{}'.format(self._autodecode(question.preamble)))

                text_file.write(u'\n{}.- '.format(question_count))
                text_file.write(self._autodecode(question.name))
                text_file.write(u'\n')

                question_count += 1

                answer_count = 1
                for answer in question.answers:
                    letter = u' abcdefghijklmnopqrstuvwxyz'[answer_count]
                    text_file.write(u'{}) '.format(u'x' if answer.is_correct else letter))

                    text_file.write(self._autodecode(answer.name))
                    text_file.write(u'\n')

                    answer_count += 1



        print(os_encoding)

        # except Exception as ex:
        #     print ex

    def main(self):
        """ The main application behavior, this method should be used to
        start the application.
        """

        self._argparse()

        self._get_test()


# --------------------------- SCRIPT ENTRY POINT ------------------------------

App().main()
