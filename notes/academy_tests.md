# Academy Tests

## FIX

- [ ] Remove public training Settings menu from teachers view
- [ ] Change translation «Reclamaciones» to «Impugnaciones»
- [ ] Allow managers to change owner
  - Tests
  - Questions (with related answers)
- [ ] CHECK OVER: link between training.module and test.topic
- [ ] CHECK OVER: ir.attachment import on import wizard
- [ ] CHECK OVER: random wizard templates
- [ ] Change noupdate="0" to noupdate="1" in data/____.xml
- [ ] Topics and levels should be visible to all users
- [ ] Check image can be edited in all modules and views
- [ ] Change jorge.soto@postal3.es password

## TODO

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

## FRONTEND

- [ ] Students should be able to mark their answers as unsafe
- [ ] Time by question
- [ ] Time by random wizard template
- [ ] Gamification
- [ ] Artificial Inteligence: most missed questions
- [ ] Save student tests, students could repeat them later


## EXPORT TO MOODLE

### General

- Codificación UTF-8 (no indica si es con BOM o sin el)
- Dos líneas vacías al principio
- Línea ``$CATEGORY: $system$/`` seguida del nombre de la oposición o código Alias
- Otra línea vacía
- Preguntas

### Pregunta

- Título de la pregunta
- Respuestas entre llaves
```
Título de la pregunta. { 
	~ Opción incorrecta 
	= Opción correcta
}
```

### Respuestas

- La opción correcta se marca con = 
- Ñas incorrectas con ~

> Pueden ir en cualquier orden



// texto	Commentario hasta el final de la línea (opcional)