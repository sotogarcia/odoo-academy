import odoo
from .field import Many2manyThroughView

if not hasattr(odoo.fields, 'Many2manyThroughView'):
    odoo.fields.Many2manyThroughView = Many2manyThroughView
