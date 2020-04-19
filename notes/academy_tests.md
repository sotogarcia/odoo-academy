# Academy Tests

## FIX

- [x] Remove public tendering Settings menu from teachers view
- [x] Change translation «Reclamaciones» to «Impugnaciones»
- [x] CHECK OVER: link between training.module and test.topic
- [ ] CHECK OVER: ir.attachment import on import wizard
- [ ] CHECK OVER: random wizard templates
- [x] Change noupdate="0" to noupdate="1" in data/____.xml
- [x] Topics and levels should be visible to all users
- [x] Check image can be edited in all modules and views
- [x] Change jorge.soto@postal3.es password
- [x] KeyError: 'sms.composer' accesing students view
- [x] Hide training unit menu for non managers
- [x] Default value when category is created from topic or from question


## TODO

- [ ] Allow managers to change owner
  - Tests
  - Questions (with related answers)
- [ ] When an answer is written, write_date and write_uid should be updated in
related questions
- [ ] When a question is written, write_date and write_uid should be updated in
related tests
- [ ] Test form view should have a *Medley* button
- [ ] Questions and Answers should keep a history of changes
- [ ] Questions must be able to be exported to moodle
- [ ] Change (human readable) names in views
- [ ] Aviability of the tests and questions in frontend
		- start = fields.Datetime 
		- end = fields.Datetime (...infinite...)
		- retry = fields.Integer
		- student_id = fields.Integer
		- trainig_action_id = field.Integer
- [ ] impugnmets must be anwered by teachers
- [ ] Lessons should check (contraint) if the module belongs to the choosen answer

## FRONTEND

- [ ] Students should be able to mark their answers as unsafe
- [ ] Time by question
- [ ] Time by random wizard template
- [ ] Gamification
- [ ] Artificial Inteligence: most missed questions
- [ ] Save student tests, students could repeat them later


