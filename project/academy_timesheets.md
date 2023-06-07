# Gestión de horarios

Se parte de la siguiente premisa: el tiempo continuado en el que un determinado
docente (academy.teacher) y uno o más alumnos (academy.student) comparten el 
estudio de una la materia (academy.competency.unit) tendrá un modelo asociado
que corresponderá a una lección (academy.training.lesson).

> NOTA: habría que valorar la posibilidad de que lecciones consecutivas, en una 
misma jornada, constituyan una sesión.

## Modelos sugeridos

Sería conveniente desarrollar un módulo separado para la gestión de las clases
y los horarios. Este necesitará modelos para el aula, la lección

| modelo                        | Realidad   | Ejemplo           | Módulo    |
| ----------------------------- | ---------- | ----------------- | ----------|
| academy.training.session      | Sesión     | 2022-10-22        | ::nuevo:: |
| academy.training.lesson       | Lección    | Word: 2022-10-22  | ::nuevo:: |
| academy.training.attendance   | Asistencia | Pepe: Sí          | ::nuevo:: |
| academy.educational.complex   | Centro     | López Mora, Vigo  | ??        |
| academy.educational.facility  | Aula       | AULA 3            | ??        |
| ....educational.facility.type | Tipo       | Aula informática  | ??        |

> *NOTA:* secretaría NO ha pedido que haya sesiones, pero podría ser un
elemento facilitador, tanto para la gestión como para el desarrollo.

## La lección

Una lección debe tener, al menos, los siguientes atributos:

- Inicio
- Fin
- Duración 
- Grupo (training_action_id)
- Profesor (teacher_id)
- Aulas (_puede tener varias_)
- Asistencias (_deben aparecer todos los alumnos invitados a la sesión_)
- Modalidad (academy.training.modality)
- Estado: (borrador, lista)

> *NOTA:* uno de los siguientes campos: duración o finalización, debe ser 
calculado
> *NOTA:* a día de hoy sólo se necesitan dos aulas, la física y el aula virtual,
pero cabe la posibilidad de que en un futuro se necesiten talleres u otro tipo 
de espacios, ya sean físicos o virtuales que puedan ser considerados aulas.


### Restricciones

- No puede haber dos lecciones que compartan aula en el tiempo, a no ser que 
quien se encargue de la asignación lo fuerce.
- No puede haber dos lecciones que compartan docente en el timpo, a no ser que 
quien se encargue de la asignación lo fuerce.
- No puede haber dos lecciones que compartan grupo en el timpo, a no ser que 
quien se encargue de la asignación lo fuerce.
- La suma de la duración de las lecciones de la misma materia debe corresponder
a la duración de dicha materia (academy.training.module).
- El aula debe pertenecer al mismo centro que el grupo, a no ser que
quien se encargue de la asignación lo fuerce.

> *NOTA:*Las restricciones debe facilitar la edición (@api.onchange), es decir, un
elemento que esté ocupado para un espacio de tiempo no puede ser seccionable
para ese mismo espacio de tiempo en otra lección diferente.

> *NOTA:* Todavía no existe el modelo Centro

### Valores por defecto

- Al seleccionar el grupo debería restringir las materias a las existentes
- Al seleccionar el grupo debería restringir los invitables a las matrículas
activas para esa fecha.
- Al seleccionar el grupo debería invitar a todas las matrículas activas para
la fecha.
- Al seleccionar el grupo debería autoseleccionar el centro y restringir las
aulas a las existentes en el mismo. Esa restricción debería ser laxa.
- La modalidad por defecto será la que tenga el grupo.

> *NOTA* hay que añadir la modalidad a la matrícula y, de esta forma, al añadir
las asistencias correspondientes, estas tomarán por defecto la modalidad de
dicha matrícula. Esto viene motivado porque hay grupos con modalidad mixta,
donde unos alumnos reciben clase presencial y otros lo hacen vía telemática.

### Vistas de calendario

Debe existir la posibilidad de visualizar el calendario de lecciones desde
diferentes puntos de vista, es decir:

- Debe haber una vista de calendario por aula
- Debe haber una vista de calendario por docente
- Debe haber una vista de calendario por grupo
- Debe haber una vista de calendario por alumno o por matrícula
- El número de invitados a la lección no puede exceder del número de sitios
disponibles en el aula.

> *NOTA:* podría ser interesante que los alumnos pudiesen ver su horario a
través del portal WEB.

#### Ficha de calendario

La ficha en el calenario debe mostrar, al menos:

  - El profesor (academy.teacher)
  - El grupo (academy.training.action)
  - Materia (academy.competency.unit)
  - El aula (¿cuál?)
  - Nº de Asistentes # Nº de alumnos (campos calculados, misma línea)

> *NOTA:* Puesto que el nombre de la materia puede ser excesivamente largo,
quizá convendría emplear el código o añadir un campo ``shortname``.


## El aula (academy.educational.facility)


Para impartir una lección es necesario un espacio, ya sea físico o virtual.

```
─┬─ Compañía (res.company)
 └─┬─ Centro (academy.educational.complex)
   └───Aula  (academy.educational.facility)
```

- Las aulas pueden pertenecer a un centro (academy.educational.complex)
- Un centro puede pertenecer a una determinada compañía (res.company)
- Puede haber diferentes tipos de aulas


> NOTA: Convendría contar con un IWMS (Integrated Workplace Management System)
> Si no existe en Odoo, quizá habría que plantearse la posibilidad de crearlo
    
## Permisos

Será el técnico de formación (academy_base.academy_group_technical) o grupo de
nivel superior a este, el que gestione las lecciones.
