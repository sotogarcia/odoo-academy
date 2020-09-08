# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.action.resource Odoo model which stores
all training action attributes and behavior.

"""


from logging import getLogger

import os
import re
import zipfile
import base64
from pathlib import Path

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools import config

try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO


# pylint: disable=locally-disabled, c0103
_logger = getLogger(__name__)


DOWNLOAD_URL = (
    '/web/content/?model=ir.attachment&id={id}'
    '&filename_field=datas_fname&field=datas'
    '&download=true&filename={name}'
)


class AcademyTrainingResource(models.Model):
    """ Resource will be used in a training unit or session

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.training.resource'
    _description = u'Academy training resource'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = ['image.mixin', 'mail.thread']

    # ---------------------------- ENTITY FIELDS ------------------------------


    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=254,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    manager_id = fields.Many2one(
        string='Manager',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=u'False',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    updater_id = fields.Many2one(
        string='Updater',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=u'False',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    last_update = fields.Date(
        string='Last update',
        required=False,
        readonly=False,
        index=False,
        default=fields.datetime.now(),
        help=u'Last update'
    )

    ir_attachment_ids = fields.Many2many(
        string='Attachments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=u'Resources stored in database',
        comodel_name='ir.attachment',
        relation='academy_training_resource_ir_attachment_rel',
        column1='training_resource_id',
        column2='ir_attachment_id',
        domain=[],
        context={},
        limit=None
    )

    directory = fields.Char(
        string='Directory',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Directory which contains resource files',
        size=260,
        translate=True
    )

    directory_file_ids = fields.One2many(
        string='Directory files',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource.file',
        inverse_name='training_resource_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    training_resource_id = fields.Many2one(
        string='Current version',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        domain=[('training_resource_id', '!=', False)],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    historical_ids = fields.One2many(
        string='Historical',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        inverse_name='training_resource_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    zip_attachment_id = fields.Many2one(
        string='Zip attachment',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='ir.attachment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    kind_id = fields.Many2one(
        string='Kind',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose type of resource',
        comodel_name='academy.training.resource.kind',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )


    # --------------------------- COMPUTED FIELDS -----------------------------

    attachmentcounting = fields.Integer(
        string='Number of attachments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of attachments in resource',
        compute='_compute_attachmentcounting',
    )

    @api.depends('ir_attachment_ids')
    def _compute_attachmentcounting(self):
        """ Computes the number of ir.attachment records related with resource
        """

        for record in self:
            record.attachmentcounting = len(record.ir_attachment_ids)


    directory_filecounting = fields.Integer(
        string='Number of files',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of files in related directory',
        compute='_compute_directory_filecounting',
    )


    @api.depends('directory_file_ids')
    def _compute_directory_filecounting(self):
        """ Computes the number of files in resource related directory
        """

        for record in self:
            record.directory_filecounting = len(record.directory_file_ids)


    # ---------------------- FIELD METHODS AND EVENTS -------------------------

    # def _domain_for_training_unit_ids(self):
    #     """ Compute the domain for the training units, this restrict
    #     allowed units to those are related with selected modules.
    #     """

    #     ids = self.training_module_ids.mapped('training_unit_ids').ids

    #     return [('id', 'in', ids) if ids else ('id', '=', -1)]


    @api.onchange('directory')
    def _onchange_directory(self):
        """ Onchange event for general_public_access field
        """

        self._reload_single_directory()


    # @api.onchange('training_module_ids')
    # def _training_module_ids(self):
    #     """ training_module_ids change event. Update the training unit
    #     list and domain
    #     """

    #     #STEP 1: Update the unit set according to the selected modules
    #     utdel = self._get_units_to_remove()
    #     utadd = self._get_units_to_add()
    #     self.training_unit_ids = self.training_unit_ids - utdel +utadd

    #     #STEP 1: Return new domain to restrict units within selected modules
    #     return {'domain': {'training_unit_ids': self._domain_for_training_unit_ids()}}


    # ------------------------- AUXLIARY METHODS ------------------------------

    def _get_units_to_remove(self):
        """ Computes which units will be removed from list. This list
        changes when the list of training modules changes before.
        """

        module_ids = self.training_module_ids.ids
        return self.training_unit_ids.filtered(
            lambda item: item.training_module_id.id not in module_ids)


    def _get_units_to_add(self):
        """ Computes which units will be added to list. This list
        changes when the list of training modules changes before.
        """

        unit_ids = self.training_unit_ids
        module_set = self.training_module_ids.filtered(
            lambda item: item.training_unit_ids and \
                         not item.training_unit_ids & unit_ids)

        return module_set.mapped('training_unit_ids')


    def _reload_single_directory(self):
        """ Reload directory filenames
        """
        record = self
        if record.directory:
            base_path = os.path.abspath(record.directory)

            # Remove all current file names
            record.directory_file_ids = [
                (2, _id) for _id in record.directory_file_ids.mapped('id')
            ]

            filenames = []

            #pylint: disable=I0011,W0612
            for root, dirs, files in os.walk(base_path):
                for name in files:
                    rel_path = os.path.join(root, name).replace(base_path + '\\', '')

                    if  re.search('^[^~_.]', rel_path):
                        filenames.append(
                            (0, 0, {
                                'name': rel_path,
                                'training_resource_id': record.id
                                }
                            )
                        )

                record.directory_file_ids = filenames

    @staticmethod
    def _zipdir(path, ziph):
        # ziph is zipfile handle
        dirname = os.path.basename(path)

        for root, dirs, files in os.walk(path): # pylint: disable=locally-disabled, W0612
            for file in files:
                relpath = os.path.relpath(root, path)
                relfile = os.path.join(dirname, relpath, file)
                _logger.debug(u'### Zipping %s', relfile)
                ziph.write(os.path.join(root, file), relfile)


    # --------------------------- PUBLIC METHODS ------------------------------

    def reload_directory(self):
        """ Reload directory filenames
        """

        for record in self:
            record._reload_single_directory() # pylint: disable=locally-disabled, W0212


    def download_directory(self):
        """ Download related directory as a zip file. This method will be
        called by the Download button in VIEW

        Todo: Reads and writes in external folders, all the behavior should
        be inside a try...except block
        """

        self.ensure_one()

        data_dir = config.filestore(self._cr.dbname)
        data_dir = os.path.abspath(data_dir)
        action = None

        # pylint: disable=locally-disabled, W0212
        for record in self:
            ira_ids = record.mapped('ir_attachment_ids')
            if record.directory or ira_ids:
                zipname = u'{}.zip'.format(record.name)

                in_memory = BytesIO()
                zipf = zipfile.ZipFile(in_memory, 'w', zipfile.ZIP_DEFLATED)

                if record.directory:
                    record._zipdir(record.directory, zipf)
                    _logger.debug(in_memory.getbuffer().nbytes)

                for item in ira_ids:
                    zipf.write(
                        os.path.join(data_dir, Path(item.store_fname)),
                        os.path.join('ir_attachments', item.datas_fname)
                    )

                zipf.close()

                datas = base64.b64encode(in_memory.getvalue())
                _logger.debug(u'zip size: %s', len(datas))

                values = {
                    'name': zipname,
                    'datas': datas,
                    'datas_fname': zipname,
                    'res_model': record._name,
                    'res_id': record.id
                }

                if not record.zip_attachment_id:
                    record.zip_attachment_id = \
                        record.zip_attachment_id.create(values)
                else:
                    _id = record.zip_attachment_id.id
                    record.zip_attachment_id.write(values)

                _id = record.zip_attachment_id.id
                _name = record.zip_attachment_id.name

                action = {
                    'type': 'ir.actions.act_url',
                    'url': DOWNLOAD_URL.format(id=_id, name=_name),
                    'nodestroy': True,
                    'target': 'new'
                }

        return action


    # pylint: disable=locally-disabled, W0212
    historical_count = fields.Integer(
        string='Historical count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of historical records',
        compute=lambda self: self._compute_historical_count()
    )

    @api.depends('historical_ids')
    def _compute_historical_count(self):
        for record in self:
            record.historical_count = len(record.historical_ids)



    def button_snapshot(self, values):
        """
            Update all record(s) in recordset, with new value comes as {values}
            return True on success, False otherwise

            @param values: dict of new values to be set

            @return: True on success, False otherwise
        """

        for record in self:
            old_attachments = self.ir_attachment_ids.copy()
            old_values = {
                'name' : record.name,
                'description' : record.description,
                'active' : record.active,
                'manager_id' : record.manager_id.id,
                'last_update' : record.last_update,
                'training_resource_id' : record.id,
                'ir_attachment_ids' : [(6, None, old_attachments._ids)],
                'directory' : self.directory,
                'training_module_ids' : [(6, None, self.training_module_ids._ids)],
                'directory_file_ids' : [(6, None, self.directory_file_ids._ids)],
                'training_action_ids' : [(6, None, self.training_action_ids._ids)],
                'historical_ids' : [(5, None, None)],
            }

            super(AcademyTrainingResource, self).create(old_values)

            # result = super(AcademyTrainingResource, self).write(values)
            # old_resource.training_resource_id = result

        # return result

    @api.model
    def _where_calc(self, domain, active_test=True):
        """ This method has been overwritten to prevent old ticket states are
        returned by the `search` and `read_group` methods.

        It adds to the given domain a new clausule to include only the
        records with NULL value in `current_state` field

        :param domain: the domain to compute
        :type domain: list
        :param active_test: whether the default filtering of records with
                            ``active`` field set to ``False`` should be applied
        :return: the query expressing the given domain as provided in domain
        :rtype: osv.query.Query
        """
        domain = domain[:]  # See the parent method

        if domain:
            # the item[0] trick below works for domain items and '&'/'|'/'!'
            # operators too
            if not any(item[0] == 'training_resource_id' for item in domain):
                domain.insert(0, ('training_resource_id', '=', False))
        else:
            domain = [('training_resource_id', '=', False)]

        return super(AcademyTrainingResource, self)._where_calc(domain, active_test)

