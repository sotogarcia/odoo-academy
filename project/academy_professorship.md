# Gestión de profesores

Para impartir lecciones es necesario que haya un docente. Este tendrá que poder
acceder a la información relativa a su lección, a los contenidos asociados y,
al menos, anotar las asistencias.

Es conventiene que un profesor sea una especialización de un usuario de Odoo.

```python
_inherits = {'res.users': 'res_users_id'}
```

## Consideraciones

- Puede haber varios tipos de relaciones por profesor.
- Estas tendrán una fecha de entrada en vigor y, a veces, una fecha de caducidad.
- La entrada en vigor de una nueva relación para un profesor en un grupo, hace
finalizar la que tuviere con anterioridad para el mismo grupo.
- Los períodos son meses o la parte proporcional de los mismos.

## Tipos de relaciones

Existen diferentes tipos de relación contractual entre la entidad formativa y
el docente. Primero, puede ser laboral o mercantil y, dentro de lo mercantil,
la docencia puede acogerse a un tipo de cobro con fiscalización particular en
el cual NO se emite factura, no lleva IVA y que se llama "Recibo de formación".

Además, en cualquier caso, el acuerdo económico puede ser:

| # | Denominación                                      |
| - | ------------------------------------------------- |
| F | Precio por hora                                   |
| P | Porcentaje de la facturación                      |
| I | Precio fijo más incremento por número de alumnos  |
| A | Precio por alumno por rangos                      |
| H | Precio por horas por rangos                       |
| C | Precio mensual por alumno                         |
| N | Precio fijo por intervalos de alumnos             |
| M | Precio por hora según materias                    |


## Precio por hora

- Precio fijo por hora
- Puede haber una cantidad mínima estipulada

## Porcentaje de la facturación

- Porcentaje, lineal, sobre la facturación total del curso
- Puede haber una cantidad mínima estipulada
- Se calcula sobre la parte proporcional de horas que haya impartido en el
período, sobre el total de horas de todos los docentes h_propias / h_totales

## Precio fijo más incremento por número de alumnos

- Hay una catindad mínima estipulada
- Se incremente linealmente por número de alumnos
- Segun los alumnos invitados a la lección en el período

## Precio por alumno por rangos

- Uno o más rangos definidos por relación (relación 1--n)
- Se paga en función del rango alcanzado en ese período (mes)
- La cantidad mínima estipulada corresponderá al rango más bajo

## Precio por horas por rangos

- Uno o más rangos *de horas* definidos por relación (relación 1--n)
- Se paga *la hora* en función del rango alcanzado en ese período (mes)
- La cantidad mínima estipulada corresponderá al rango más bajo

## Precio mensual por alumno

- Precio fijo por alumno, revisable por período (mes)
- Puede haber una cantidad mínima estipulada

## Precio fijo por intervalos de alumnos

- Uno o más rangos *de alumnos* definidos por relación (relación 1--n)
- Se paga el período (mes) en función del rango alcanzado en él
- La cantidad mínima estipulada corresponderá al rango más bajo

## Precio por hora según materias

- Se paga *la hora* en función de la materia


