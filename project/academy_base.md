# Información necesaria

Este archivo contiene una descripción general del módulo academy_base y 
anotaciones para el desarrollo de dos módulos asociados. Uno para la gestión de 
los horarios y otro para la gestión de los docentes.

## Modelos principales

| modelo                      | Elemento real               | Ejemplo          |
| --------------------------- | --------------------------- | ---------------- |
| academy.training.enrolment  | Matrícula                   | Pepe en 1º ESO D |
| academy.training.action     | Grupo                       | 1º ESO D         |
| academy.training.activity   | Curso                       | 1º ESO           |
| academy.competency.unit     | Materia                     | Segundo idioma   |
| academy.training.module     | Contenido intercambiable    | Inglés           |
| academy.training.unit       | Segmentación de contenidos  | Laboratorio      |

- Los alumnos se matriculan en acciones formativas (academy.training.action).
- La unidad de competencia (academy.competency.unit) carece de contenido, tan 
solo se emplea para asignar, al módulo aparejado (academy.training.module) el 
nombre y la descripción que el alumno verá en sus boletines.
- El módulo (academy.training.module) sí tiene contenido y es además la unidad 
mínima evaluable. Si fuese muy extenso, podría ser dividido en partes más 
pequeñas denominadas unidades formativas.

> *NOTA:* NO existe modelo (academy.training.unit), por contra, las unidades
formativas se definen como módulos que tienen otro módulo padre (parent_id).
> *NOTA:* De manera general, los demás modelos tan sólo contienen 
categorizaciones para estos elementos principales.
