# Academy base

## FIX

- [ ] Remove lib folder from .gitignore
- [ ] Save notes.txt outside server
- [ ] Add student as level
- [ ] The menu «Answers» could not allow to create new items
- [ ] The menu «Categories» could not allow to create new items
- [ ] add options="{'no_create': True} and other widget options - see: http://ludwiktrammer.github.io/odoo/form-widgets-many2many-fields-options-odoo.html#many2manytags-widget
- [ ] WARNING: basic_view.js:83 Missing widget:  many2many_kanban  for field ir_attachment_image_ids of type many2many


## UPDATE

- [ ] Ensure all models can be duplicated except enrolment


## List active duplicated enrollments

````sql
SELECT
    a.id AS enrolment1_id,
    b.id AS enrolment2_id,
    a.training_action_id,
    a.student_id,
    a.register AS start_date1,
    a.deregister AS end_date1,
    b.register AS start_date2,
    b.deregister AS end_date2
FROM
    academy_training_action_enrolment a,
    academy_training_action_enrolment b
WHERE
    a.id <> b.id
    AND a.active AND b.active
    AND a.training_action_id = b.training_action_id
    AND a.student_id = b.student_id
    AND tsrange(a.register, COALESCE(a.deregister, 'infinity'::date), '[]')
        && tsrange(b.register, COALESCE(b.deregister, 'infinity'::date), '[]');
```
