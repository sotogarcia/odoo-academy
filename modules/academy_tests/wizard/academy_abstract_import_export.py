# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################


from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _
from logging import getLogger

from io import BytesIO
from base64 import decodestring, b64encode
from zipfile import is_zipfile, ZipFile
from os import path, linesep
from chardet import detect
from enum import IntEnum, IntFlag
from re import sub as replace, search, MULTILINE, UNICODE, IGNORECASE
import hashlib
import json


_logger = getLogger(__name__)


class Mi(IntEnum):
    """ Enumerates regex group index un line processing
    """
    ALL = 0
    QUESTION = 1
    ANSWER = 2
    LETTER = 3
    FALSE = 4
    TRUE = 5
    DESCRIPTION = 6
    IMAGE = 7
    TITLE = 8
    URI = 9
    CONTENT = 10


class CatFlags(IntFlag):
    NONE = 0
    NAME = 1
    PREAMBLE = 2
    DESCRIPTION = 4
    RIGHT = 8
    WRONG = 16
    BASE = 7
    ANSWERS = 24
    ALL = 31


REGEX_PATTERN = r'((^[0-9]+)\. |(((^[a-wy-z])|(^x))\) )|(^> )|(^\!\[([^]]+)\]\(([^)]+)))?(.+)'  # noqa: E501


class AcademyAbstractImportExport(models.AbstractModel):
    """ Provides the required behavior to import and export questions
    """

    _name = 'academy.abstract.import.export'
    _description = u'Academy tests import export'

    @staticmethod
    def _get_special_files():
        statement = _('Statement')

        return [
            'changelog.txt',
            'manifest.json',
            '{}.txt'.format(statement),
            '{}.pdf'.format(statement)
        ]

    @staticmethod
    def _equal(str1, str2):
        str1 = (str1 or '').lower()
        str2 = (str2 or '').lower()

        return str1 == str2

    @staticmethod
    def _safe_cast(val, to_type, default=None):
        """ Performs a safe cast between `val` type to `to_type`
        """

        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_to_int(element):
        result = None

        try:
            result = int(element)
        except ValueError as ex:
            msg = _('{} could not be converted in a number. System says {}')
            _logger.info(msg.format(element, ex))

        return result

    @staticmethod
    def _get_real_ids(recordset):
        """ Sometimes the received recordset contains instances of NewID. This
        method get the real ID of these records.

        Args:
            recordset (model.Models): Odoo valid recordset which have NewID

        Returns:
            list: list of real ID from all the records in the given recordset
        """

        return [item._origin.id for item in recordset]

    @staticmethod
    def _field_to_bytesio(field):
        """Get data from Odoo binary field and stores in BytesIO structure

        Args:
            field (fields.Binary): field from which the data will be retrieved

        Returns:
            io.BytesIO: BytesIO structure with retrieved data

        Raises:
            UserError: any error message that may have been raised already
            transformed into an Odoo UserError
        """

        io = None

        try:
            io = BytesIO()
            io.write(decodestring(field))
        except Exception as ex:
            raise UserError(ex)

        return io

    @staticmethod
    def _field_to_string(field):
        """Get string from Odoo binary field

        Args:
            field (fields.Binary): field from which the string will be gotten

        Returns:
            str: string has been retrieved

        Raises:
            UserError: any error message that may have been raised already
            transformed into an Odoo UserError
        """

        content = None

        try:
            content = decodestring(field)
        except Exception as ex:
            raise UserError(ex)

        return content

    @classmethod
    def _get_id_from_filename(cls, name):
        """ This method splits given file name in name and extension and then
        it performs a safe cast from file name to integer ID. This method is
        called from ``validate_filenames``

        Args:
            name (str): filename and extension

        Returns:
            int: ID which match with given name or None
        """

        sid = path.basename(name)
        sid = path.splitext(sid)[0]
        return cls._safe_to_int(sid)

    def _is_target(item_id, target_ids):
        """ Check if given item ID is not empty and it's among the targets if
        these targets are not empty.

        Args:
            item_id (id): ID will be checked
            target_ids (list): list of valid IDs

        Returns:
            bool: True if it meet the conditions or False othewise
        """

        return item_id and (not target_ids or item_id in target_ids)

    @staticmethod
    def ensure_zip_format(io):
        msg = _('The selected file is not a zip file')

        if not is_zipfile(io):
            raise ValidationError(msg)

    @classmethod
    def validate_filenames(cls, io, valid_ids):
        """ All files contained in the zip must have as name the ID of the
        attachment will be updated. This method splits each one of the file
        names in name and extension to perform a safe cast from name to an
        integer ID.

        This method is useful to validate chosen Zip file before try to update
        attachments, and this is used by onchange method in wizards.

        Args:
            io.BytesIO: BytesIO structure which stores Zip data
            valid_ids (list): IDs of the attachments which can be updated

        Raises:
            ValidationError: Description
        """

        msg = _('File {} does not have a match')
        special_files = cls._get_special_files()

        with ZipFile(io) as zipio:
            names = zipio.namelist()

        for name in names:
            if name in special_files:
                continue

            item_id = cls._get_id_from_filename(name)
            if not cls._is_target(item_id, valid_ids):
                raise ValidationError(msg.format(name))

    @api.model
    def read_statement_from_zip(self, io):
        """
        """

        encoding = None
        statement = '{}.txt'.format(_('Statement'))

        with ZipFile(io) as zipio:
            names = zipio.namelist()

            if statement in names:
                content = zipio.read(statement)

                detected = detect(content)
                encoding = detected.get('encoding', 'utf_8') or 'utf_8'

                content = content.decode(encoding)

        return content or ''

    @api.model
    def update_from_zip(self, io, targets):
        """ This method performs an update of some of the existing attachments
        whose identifiers matchs with given target IDs, using files from given
        zip file.

        Args:
            io.BytesIO: BytesIO structure which stores Zip data
            target_ids (list): IDs of the attachments which can be updated
        """

        attach_obj = self.env['ir.attachment']
        msg = _('File {} will be ignored')
        special_files = self._get_special_files()

        target_ids = self._ensure_ids(targets)

        with ZipFile(io) as zipio:
            names = zipio.namelist()

            for name in names:
                if name in special_files:
                    continue

                attach_id = self._get_id_from_filename(name)

                if self._is_target(attach_id, target_ids):

                    attach_item = attach_obj.browse(attach_id)

                    content = zipio.read(name)
                    attach_item.datas = b64encode(content)

                else:
                    _logger.warning(msg.format(name))

    @staticmethod
    def decode_content(content, encoding=None, errors="replace"):
        """ Decode a given string using the specified encoding

        Args:
            content (str): string will be decoded
            encoding (str, optional): ecoding will be used. If this argument
            is ``None`` or ``Auto``, methos will use ``chardet`` library to
            try to determine try to determine the encoding of the string.
            errors (str, optional): see python Codec registry and base classes

        Returns:
            str: resulting decoded string
        """

        if not encoding or encoding == 'auto':
            detected = detect(content)
            encoding = detected.get('encoding', 'utf_8') or 'utf_8'

        return (content or '').decode(encoding, errors)

    @classmethod
    def _read_question_hash_values(cls, question_item):
        values = cls._default_question_values_dictionary(True)

        # values['id'] = question_item._origin.id
        values['description'] = question_item.description or ''
        values['preamble'] = question_item.preamble or ''
        values['name'] = question_item.name or ''

        index = 0
        for answer_item in question_item.answer_ids:
            index = index + 1
            ans_vals = {
                'name': answer_item.name or '',
                'is_correct': answer_item.is_correct or False,
                'sequence': index
            }
            values['answer_ids'].append([0, None, ans_vals])

        for attach_item in question_item.ir_attachment_ids:
            values['ir_attachment_ids'].append([4, attach_item.id, None])

        return values

    @staticmethod
    def _compute_md5(values):
        json_data = json.dumps(values, sort_keys=True)
        text_data = json_data.encode('utf-8')

        return hashlib.md5(text_data).hexdigest()

    @classmethod
    def _question_has_changed(cls, question_item, new_values):
        qvalues = cls._read_question_hash_values(question_item)

        qhash = cls._compute_md5(qvalues)
        vhash = cls._compute_md5(new_values)

        return qhash != vhash

    def _update_o2m_answer_actions(self, question_item, values):
        dst_len = len(question_item.answer_ids)
        src_len = len(values['answer_ids'])

        # STEP 1: Change create action to write action to the existing answers
        for index in range(0, min(src_len, dst_len)):
            answer_item = question_item.answer_ids[index]
            values['answer_ids'][index][0] = 1
            values['answer_ids'][index][1] = answer_item.id

        # STEP 1: Append delete actions if there were more questions than
        # in the updated text
        if src_len < dst_len:
            for index in range(src_len, dst_len):
                answer_item = question_item.answer_ids[index]
                values['answer_ids'].append([2, answer_item.id, None])

        return values

    def write_questions(self, value_set, targets, force=False):
        msg = 'There is no question with id "{}" among those selected'
        model = 'academy.tests.question'
        question_set = self.env['academy.tests.question']

        # pylint: disable=locally-disabled, W0703
        self.env.cr.autocommit(False)

        try:
            targets = self._ensure_recordset(targets, model)

            for values in value_set:

                question_id = values.pop('id')
                question_item = targets.filtered(lambda q: q.id == question_id)

                assert question_item, msg.format(question_id)

                if force or self._question_has_changed(question_item, values):
                    self._update_o2m_answer_actions(question_item, values)
                    question_item.write(values)
                    question_set += question_item

            self.env.cr.commit()

        except Exception as ex:
            message = _('Some questions could not be updated, system says: %s')
            self.env.cr.rollback()
            raise UserError(message % ex)

        self.env.cr.autocommit(True)

        return question_set

    # ------------------------------- IMPORT ----------------------------------

    @staticmethod
    def _has_flag(value, expected):
        return (value & expected) == expected

    @api.model
    def _ensure_recordset(self, target, model, at_leat_one=False):
        model_obj = self.env[model]

        if isinstance(target, int):
            target = model_obj.browse(target)
        elif isinstance(target, (list, tuple)):
            domain = [('id', 'in', target)]
            target = model_obj.search(domain)

        assert isinstance(target, type(model_obj)), \
            _('{} could not be updated to {}'.format(target, model))

        assert target or not at_leat_one, \
            _('{} represents an empty record of {}'.format(target, model))

        return target

    @staticmethod
    def _ensure_ids(target, at_leat_one=False):

        if isinstance(target, models.Model):
            target = target.mapped('id')
        elif isinstance(target, int):
            target = [target]
        elif target is None or target is False:
            target = []

        assert target or not at_leat_one, \
            _('{} has no ID\'s'.format(target))

        return target

    @staticmethod
    def owner_field_is_accessible(recordset):
        """If current user is allowed to access to the owner_id field then
        field should be returned by `fields_get` method

        Args:
            recordset (models.Model): check if current user is allowed to
            access owner_id field

        Returns:
            bool: True if use can access owner_id field or False otherwise
        """

        return recordset.fields_get().get('owner_id', False) is not False

    @staticmethod
    def clear_text(content):
        """ Perform some operations to obtain a cleared text
            - Replace tabs with spaces en removes extra spaces
            - Replace extra simbols after lists elements
        """

        content = (content or '').strip()
        flags = MULTILINE | UNICODE

        # STEP 1: Remove tabs and extra spaces
        content = replace(r'[ \t]+', r' ', content, flags=flags)

        # STEP 2: Remove spaces from both line bounds
        content = replace(r'[ \t]+$', r'', content, flags=flags)
        content = replace(r'^[ \t]+', r'', content, flags=flags)

        # STEP 3: Replace CRLF by LF and remove duplicates
        content = replace(linesep, r'\n', content, flags=flags)
        content = replace(r'[\n]{2,}', r'\n\n', content, flags=flags)

        # STEP 2: Update questions and answers numbering formats
        pattern = r'^([0-9]{1,10})[.\-)]+[ \t]+'
        content = replace(pattern, r'\1. ', content, flags=flags)
        pattern = r'^([a-zñA-ZÑ])[.\-)]+[ \t]+'
        content = replace(pattern, r'\1) ', content, flags=flags)

        return content

    @staticmethod
    def split_in_line_groups(content):
        """ Splits content into lines and then splits these lines into
        groups using empty lines as a delimiter.

        """

        lines = content.splitlines(False)
        groups = []

        group = []
        numlines = len(lines)
        for index in range(0, numlines):
            if lines[index] == '':
                groups.append(group)
                group = []
            elif index == (numlines - 1):
                group.append(lines[index])
                groups.append(group)
            else:
                group.append(lines[index])

        return groups

    @staticmethod
    def _default_question_values_dictionary(update):
        """ Returns an empty dictionary with field values can be used to create
        or update questions.

        This dictionary does not include categorization field values which are
        required to create new questions.

        Returns:
            dict: empty dictionary with field values
        """

        return {
            'description': '',
            'preamble': '',
            'name': None,
            'answer_ids': [],
            'ir_attachment_ids': [(5, 0, 0)] if update else [],
        }

    @staticmethod
    def _append_line(_in_buffer, line):
        """ Appends new line using previous line break when buffer is not empty
        """
        if _in_buffer:
            _in_buffer = _in_buffer + '\n' + line
        else:
            _in_buffer = line

        return _in_buffer

    @api.model
    def _process_attachment_groups(self, groups):
        uri = groups[Mi.URI]
        title = groups[Mi.TITLE]

        if not uri or not title:
            msg = _('The attachment line "{}" is not valid')
            raise ValidationError(msg.format(groups[Mi.ALL]))

        return [4, uri, title]  # Must be a list to allow update later

    @api.model
    def _process_line_group(self, line_group, update):
        """Gets description, image, preamble, statement, and answers
        from a given group of lines.

        Args:
            line_group (str): multiple line string

        Returns:
            dict: dictionary with field values can be used to create or update
            questions. This does not include categorization field values.
        """

        sequence = 0
        values = self._default_question_values_dictionary(update)

        for line in line_group:
            found = search(REGEX_PATTERN, line, UNICODE | IGNORECASE)
            if found:
                groups = found.groups()

                if groups[Mi.QUESTION]:
                    values['id'] = self._safe_cast(groups[Mi.QUESTION], int, 0)
                    values['name'] = groups[Mi.CONTENT]

                elif groups[Mi.ANSWER]:
                    sequence = sequence + 1
                    ansvalues = {
                        'name': groups[Mi.CONTENT],
                        'is_correct': (groups[Mi.TRUE] is not None),
                        'sequence': sequence
                    }

                    values['answer_ids'].append([0, None, ansvalues])

                elif groups[Mi.DESCRIPTION]:
                    values['description'] = self._append_line(
                        values['description'], groups[Mi.CONTENT])

                elif groups[Mi.IMAGE]:
                    m2m_action = self._process_attachment_groups(groups)
                    values['ir_attachment_ids'].append(m2m_action)

                else:
                    values['preamble'] = self._append_line(
                        values['preamble'], groups[Mi.CONTENT])

        return values

    @api.model
    def build_value_set(self, groups, update):
        value_set = []
        for group in groups:
            values = self._process_line_group(group, update)
            value_set.append(values)

        return value_set

    @classmethod
    def _attachment_filtered(cls, uri, attachments, ensure=True):
        """ Search for a match within a given attachment recordset. Match can
        be ID, file name with extension or filename without extension.

        It ensures there is a single record match or it raises a validation
        error otherwise.

        Args:
            uri (str): identifier for attachment in the given recordset. This
            can be a filename or ID, but it must be unique.
            attachments (models.Model): Odoo ir.attachment recordset

        Returns:
            models.Model: single one Odoo ir.attachment
        """

        name = path.splitext(uri)[0]
        attach_id = cls._safe_cast(uri, int, 0)

        result = attachments.filtered(lambda item: item.id == attach_id
                                      or cls._equal(item.name, uri)
                                      or cls._equal(item.name, name))

        if ensure and (not result or len(result) != 1):
            msg = _('Attachment "{}" could not be found or it is duplicated')
            raise ValidationError(msg.format(uri))

        return result

    @staticmethod
    def _rename_attachments(attachments, names):
        """ Rename attachments with given names. This method is called from
        ``postprocess_attachment_ids``, which generates a dictionary of pairs
        with the id and the **last name** used for the attachment.

        Args:
            attachments (models.Model): Odoo ir.attachment recordset
            names (dict): dict of pairs {id : name}
        """

        for attach_id, name in names.items():
            name = path.splitext(name)[0]
            attach_item = attachments.filtered(lambda x: x.id == attach_id)
            attach_item.name = name

    @staticmethod
    def _is_first_remove_all(m2m_actions):
        return m2m_actions and m2m_actions[0][0] == 5

    @api.model
    def postprocess_attachment_ids(self, value_set, attachments, rename=True):
        """ Updates a dictionary returned by ``build_value_set`` changing
        URI in ir_attachments_ids many2many operations with the real record ID.

        This transforms fake operations like (4, 'image.png', 'Image') in
        valid operations like (4, ID, None), where ID is the real/valid ID of
        the attachment. This attachments must exist in the given recordset.

        If the ``rename`` argument has been set to ``True``, this method will
        use the non-empty third arguments from many2many fake operations to
        rename the target attachments.

        Args:
            value_set (dict): dictionary returned by ``build_value_set``
            attachments (TYPE): available attachments can be linked to the
            created or updated questions.
            rename (bool, optional): True or not established to rename the
            attachments according to the names supplied.
        """

        names = {}

        for values in value_set:
            m2m_actions = values['ir_attachment_ids']

            length = len(m2m_actions)
            first = 1 if self._is_first_remove_all(m2m_actions) else 0

            for index in range(first, length):
                uri = m2m_actions[index][1]
                name = m2m_actions[index][2]

                attach_item = self._attachment_filtered(uri, attachments, True)

                m2m_actions[index][1] = attach_item.id
                m2m_actions[index][2] = None

                if name:
                    names[attach_item.id] = name

        if rename and names:
            self._rename_attachments(attachments, names)

    @classmethod
    def assign_to(cls, recordset, owner_id=None):

        if owner_id and cls.owner_field_is_accessible(recordset):
            if isinstance(owner_id, models.Model):
                recordset.write({'owner_id': owner_id.id})
            elif isinstance(owner_id, int) and not isinstance(owner_id, bool):
                recordset.write({'owner_id': owner_id})

    @staticmethod
    def _get_value(source, fname, default=None):
        """This will be used by auto_set_categories to get values from a list
        or a recordset

        Args:
            source (list|tuple|models.Model): this can be a list of dicts
            when methos is called before question creation or an existing
            question recordset.
            fname (str): name of the question attribute from which the value
            will be taken
            default (any, optional): value will be returned when attribute
            has not been set

        Returns:
            any: question attribute value if has been set or given default
        """
        if isinstance(source, dict):
            return source[fname] if fname in source.keys() else default

        return getattr(source, fname, default)

    @staticmethod
    def _get_answers(source):
        """This will be used by auto_set_categories to get answers from a list
        or a recordset

        Args:
            source (list|tuple|models.Model): this can be a list of dicts
            when methos is called before question creation or an existing
            question recordset.

        Returns:
            list|models.Model: list of one2many operations when no questions
            have been created or answer recordset instead.
        """
        kname = 'answer_ids'
        if isinstance(source, dict):
            return source[kname] if kname in source.keys() else []

        return getattr(source, 'answer_ids')

    @staticmethod
    def _get_answer_value(answer, fname, default=None):
        """This will be used by auto_set_categories to get answers values from
        a one2many operations list [(0, 0, {})] or a answer recordset

        Args:
            answer (list|models.Model): one2many list or answer recordset
            fname (str): name of the question attribute from which the value
            will be taken
            default (any, optional): value will be returned when attribute
            has not been set

        Returns:
            any: answer attribute value if has been set or given default
        """
        if isinstance(answer, (list, tuple)):
            return answer[2][fname] if fname in answer[2].keys() else default

        return getattr(answer, fname, default)

    @api.model
    def _get_default_catflags(self, default=CatFlags.BASE):
        param_obj = self.env['ir.config_parameter'].sudo()
        value = param_obj.get_param('academy_tests.autocategorization_flags')

        return self._safe_cast(value, int, default) if value else default

    @api.model
    def auto_set_categories(self, value_set, topic_id, flags=-1):
        """Set  question categories based on matches found for topic keywords

        Args:
            value_set (list|tuple|models.Model): this can be a list of dicts
            when methos is called before question creation or an existing
            question recordset.
            topic_id (models.Model): topic from which to take the keywords
            flags (CatFlags, optional): flags to determine which question
            attributes will be searched for keywords
        """
        topic_set = self._ensure_recordset(
            topic_id, 'academy.tests.topic', at_leat_one=True)

        if not isinstance(value_set, (list, tuple, models.Model)):
            value_set = [value_set]

        if flags < 0:
            flags = self._get_default_catflags()

        for values in value_set:
            category_ids = []

            description = self._get_value(values, 'description', '')
            preamble = self._get_value(values, 'preamble', '')
            name = self._get_value(values, 'name', '')

            # matches => {topic_id: [categorory_id1, ...]}
            if self._has_flag(flags, CatFlags.DESCRIPTION):
                matches = topic_set.search_for_categories(description)
                category_ids += matches.get(topic_id.id, [])

            if self._has_flag(flags, CatFlags.PREAMBLE):
                matches = topic_set.search_for_categories(preamble)
                category_ids += matches.get(topic_id.id, [])

            if self._has_flag(flags, CatFlags.NAME):
                matches = topic_set.search_for_categories(name)
                category_ids += matches.get(topic_id.id, [])

            if flags & CatFlags.ANSWERS:  # Does not have to be an exact match

                for answer in self._get_answers(values):
                    name = self._get_answer_value(answer, 'name', '')
                    right = self._get_answer_value(answer, 'is_correct', False)

                    if self._has_flag(flags, CatFlags.RIGHT) and right:
                        matches = topic_set.search_for_categories(name)
                        category_ids += matches.get(topic_id.id, [])

                    if self._has_flag(flags, CatFlags.WRONG) and not right:
                        matches = topic_set.search_for_categories(name)
                        category_ids += matches.get(topic_id.id, [])

            if category_ids:
                category_ids = list(dict.fromkeys(category_ids))
                values['category_ids'] = [(6, False, category_ids)]

    @api.model
    def append_owner(self, value_set, owner_id):

        owner_set = self._ensure_recordset(
            owner_id, 'res.users', at_leat_one=True)

        if not isinstance(value_set, (list, tuple)):
            value_set = [value_set]

        for value in value_set:
            value['owner_id'] = owner_set.id

    def create_questions(self, value_set, sequential=False):
        question_set = self.env['academy.tests.question']
        question_id = None

        # pylint: disable=locally-disabled, W0703
        try:
            for values in value_set:
                if sequential and question_id:
                    values['depends_on_id'] = question_id.id

                question_id = question_set.create(values)
                question_set += question_id

        except Exception as ex:
            message = _('Some questions could not be created, system says: %s')
            raise UserError(message % ex)

        return question_set

    # --------------------------- APPEND TO TEST ------------------------------

    @staticmethod
    def _get_last_test_sequence(test_item):

        test_item.ensure_one()
        sequences = test_item.question_ids.mapped('sequence') or [0]

        return max(sequences)

    @api.model
    def append_to_test(self, test, questions):
        model = 'academy.tests.test'
        m2m_ops = []

        question_ids = self._ensure_ids(questions, at_leat_one=False)
        test_item = self._ensure_recordset(test, model, at_leat_one=True)
        sequence = self._get_last_test_sequence(test_item)

        for question_id in question_ids:

            sequence += 1
            values = {
                'test_id': test_item.id,
                'question_id': question_id,
                'sequence': sequence
            }

            m2m_ops.append((0, None, values))

        test_item.write({'question_ids': m2m_ops})
