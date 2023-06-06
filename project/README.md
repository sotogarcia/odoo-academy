# Odoo academy

This document compiles the general considerations about this project and each
of its components.

## Todo

To-do list for the project divided by modules

### academy_base

- [ ] App throws an error on update an enrollment with invites
- [ ] code constraints should ignore the chararcter case in all models
- [ ] When the teacher kanban cards have different heights, the
``kanban-box-toolbar`` does not appear at the bottom of each one.

### academy_timesheets

- [ ] session_state_wizard should have a text-truncate class in the
``competency_unit_id`` field
- [ ] code constraints should ignore the chararcter case in all models
- [ ] Perhaps the ``active`` field should be considered in SQL GIST exlussions
- [ ] session_state_wizard should raise a warning before performing changes
when the new ``state`` is «toggle».