from odoo.tools.sql import column_exists, rename_column

# (table, old column, new column)
RENAMED_COLUMNS = (
    ("academy_knowledge_area", "knowle_code", "code"),
    ("academy_professional_qualification", "qualification_code", "code"),
    ("academy_qualification_level", "level", "code"),
)


def migrate(cr, version):
    for table, old_name, new_name in RENAMED_COLUMNS:
        if column_exists(cr, table, old_name) and not column_exists(
            cr, table, new_name
        ):
            rename_column(cr, table, old_name, new_name)
