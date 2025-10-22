# Migraci�n

## Pasos preliminares

- [x] Cambiar version to 18.0.1.0.0
- [x] Cambiar año de copyright a 2025
- [x] ``<path_to_odoo>/odoo-bin upgrade_code --addons-path /ruta/a/tus_addons --from 17.0 --to 18.0``
 
## Odoo 13 → 14

- [x] Eliminar `@api.one` y `@api.multi`; usar `ensure_one()` cuando proceda.
- [x] Sustituir `@api.model_cr` si existe.
- [x] Evitar dominios en `onchange`; mover filtrado a vistas/campos.
- [x] Ver que se hace con @api.model_create_multi

## Odoo 14 → 15

- [x] Definir *assets* en `__manifest__.py` (bundles QWeb/JS/CSS).
- [ ] Migrar plantillas de email de Jinja a QWeb.
- [x] Adoptar OWL y m�dulos ES; renombrar a `*.esm.js` cuando aplique.

## Odoo 15 → 16

- [x] Revisar APIs de *flush*/*invalidate* en el ORM.
- [x] Actualizar firmas de `_read_group` en overrides y tests.

## Odoo 16 → 17

- [x] Reemplazar `attrs`/`states` por expresiones directas en atributos.
  - [ ] v16: `attrs="{'invisible': [('state','=','done')]}"`.
  - [ ] v17: `invisible="state == 'done'"`.
- [x] Usar `column_invisible` en listas en lugar de `invisible`.
- [x] Considerar `search_fetch()` y `fetch()` en lugar de `search_read`.
- [x] Cambiar firma y adaptar hooks de instalaci�n
    - `def pre_init_hook(env):`
    - `def post_init_hook(env):`
    - `def uninstall_hook(env):`
- [x] Quitar `numbercall` y `doall` en el modelo `ir.cron`.

## Odoo 17 → 18

- [x] Reemplazar `user_has_groups` por `self.env.user.has_group()`/`has_groups()`.
- [x] Unificar acceso: usar `check_access()` en lugar de `check_access_*`.
- [x] Reemplazar `_name_search` por `_search_display_name`.
- [x] Importar `Registry` de `odoo.modules.registry`; usar `Registry(db_name)`.
- [x] Considerar `self.env._('...')` en lugar de `_('...')`.
- [x] Limpiar vistas: autoañadir campos invisibles en dominios/atributos.
- [x] Simplificar *chatter*: `<div class="oe_chatter">…</div>` → `<chatter />`.
- [x] Reemplazar `_filter_access_rule*` por `_filter_access()`.
- [x Reemplazar `_check_recursion()` por `_has_cycle()`.
- [-] Revisar `copy`/`copy_data` en *multi-recordsets*
  (p. ej., `copy_data` devuelve lista).
- [x] Reemplazar `group_operator` por `aggregator` en definiciones de campos.
- [x] Vigilar búsquedas en `related` no almacenados: lanzar excepci�n.
- [x] Valorar `search_fetch()` si `search()` no se ejecuta siempre.
- [x] Definir *field path* en `ir.actions.act_window` para URLs más limpias.
- [x] Retirar `/** @odoo-module **/` en JS si no es necesario.
- [x] En tours JS, sustituir `extra_trigger` por un paso independiente.

## Otros

- [x] retirar `_` de los textos de los `_sql_constraints`.
- [ ] revisar las vistas de los objetos derivados de res.partner

## Revisiones finales
- [ ] Comprobar logs y reparar posibles errores
- [ ] Traducir
    1. Exportar traducci�n y completar en PoEdit
    2. Dar la traducci�n a ChatGPT para que busque errores y corregir estos   
- [ ] Revisar lista TODO 
       · x2many count fields

## Datos demo


## Expresiones regulares

```
<field name="type">tree</field>
--
<field name="type">list</
```

```
<(/)?tree
--
<\1list
```


```
attrs=["']\{["'](readonly|invisible|required)["']: *(\[[^\]]+\])\}["']
--
\1="\2"
```

```
(readonly|invisible|required) *= *['"]\[\(['"]([^'"]+)['"] *, *['"]([^'"]+)['"] *, *(['"]?[^'"]+['"]?)\)\]['"]
\1="\2 \3 \4"
```

```
((readonly|invisible|required) *= *['"][^'"=]+=)([^=])
\1=\3
```

```
!=+
!=
```

```
<openerp>[\n\t ]*<data noupdate= ?"([[:digit:]]) ?">\n*
--
<odoo nopudate="\1">\n\n
```

```
[\n\t ]*^[ \t]*</data>[\t\n ]*</openerp>
---
\n\n</odoo>
```


- [x] Error followers con training program al guardar
- [x] Añadir a estudiante b�t�n de matr�culas.
- [x] Añadir a estudiante ficha de matr�culas.
- [x] Añadir a estudiante idiomas.
- [x] Autoetiquetar como estudiante s�lo al crear.
- [ ] Corregir los Onchange de student
- [x] Student: Name and surname
- [x] Kanban de student
- [x] Mostrar m�vil o tel�fono, el que tenga.
- [x] Secuencia para las matr�culas
- [x] Bot�n ver actividades

- [x] Errores y warnings del log
- [x] Poner internal notes en una ficha separada tanto para student compara training action
- [ ] En el enrolment los datos del alumno en una ficha y los de la acci�n en otra, el apartado admisi�n arriba de todo
- [ ] C�mo llevar cuenta de si se imprimi� el material
- [ ] �Qu� ocurre si, por fuera de student, se elige company?
- [ ] No mostrar informaci�n de parent_id en student
- [x] Bot�n actividades en kanban y form
- [ ] barcode
- [ ] Corregir `activity`, cambi�ndolo por `program`
- [ ] No se puede sustituir el programa de una acci�n formativa creada
- [ ] No se puede sustituir la acci�n formativa en un grupo ya creado
- [ ] Quitar instalaciones de training action y poner facility.reservation
- [ ] A�adir vista kanban a enrolments
- [ ] A�adir tareas NO formativas
- [ ] Sincronizar acciones formativas con grupos formativos
- [ ] A�adir bot�n actividades en la parte superior derecha como en las facturas

1 [ ] Acci�n de mantenimiento
5 [x] Nombres en los act_window retornados desde python
2 [ ] Revisar el modelo y vista de enrolment
      [ ] No deja crear un enrolment nuevo en el men� matr�culas
      [ ] Opci�n por defecto matr�cula completa (boolean)
4 [x] Revisar las vistas embebidas
6 [ ] Comprobar que se puede realizar un copy
  [ ] Comprobar tracking
1 [ ] Buscar todos los wizard para revisar
3 [ ] Revisar el modelo y vista de training session
7 [ ] Revisar informes y correos
  [ ] Modalidad en vistas kanban y list de training action
  [ ] La vista pivot de matr�culas debe mostrarlas agrupadas por acci�n y no por alumno
- [ ] Tareas NO docentes
- [ ] sanitize_phone_number da error de l�mite de recursi�n excedido


- [ ] El campo hours del m�dulo debe desaparecer
      · Si tiene unidades será de s�lo lectura
      · Si tiene unidades se calculará al guardar
- [ ] Los campos training_module_id y training_unit_ids pasan a ser parent_id y child_ids
- [ ] Description como HTML
- [ ] InternaL notes a todo
- [ ] Retirar los contraint de token

- [ ] Comprobar widgets one2many_tags y many2many_tags
- [ ] A�adir internal notes
- [ ] Copiar Ownership de academy.training.framework 
- [ ] Encabezado con: nombre, code, parent
- [ ] list-embed para los one2many y smart buttons
- [ ] el campo ref se comparte entre alumnos, profesores y staff
- [ ] Si una acci�n tiene grupos no se pueden matricular en ella a alumnos, 
- [ ] si una acci�n tiene matr�culas no se puede dividir en grupos
- [ ] mostrar l�neas del programa o acci�n en la matr�cula
- [ ] La modalidad en las matr�culas debe ser �nica
- [ ] A�adir ficha grupos a acciones
- [ ] A�adir bot�n programa a acciones
- [ ] A�adir bot�n grupos a acciones
- [ ] A�adir campo delivery_ids a las acciones.
- [ ] revisar los hooks

- [ ] "depends": ["dms", "dms_field", "dms_attachment_link"]

## Soluci�n a la matriculaci�n por grupos

Una matr�cula tendr� un campo `training_action_id` que ser� su grupo y un campo
`parent_action_id` que ser� la acci�n superior. Este segundo campo ser� igual a 
`training_action_id.parent_id` en caso de ser un grupo o a `training_action_id`
en caso de no existir grupos.

El campo enrolment_ids 


- academy.support.staff
- academy_student
- academy_teacher

- academy_training_framework
- academy_training_program
- academy_training_program_line
- academy_training_module

- academy_training_action
- academy_training_action_enrolment

- academy_competency_unit
- academy_educational_attainment
- academy_application_scope
- academy_training_methodology
- academy_training_modality

- academy_knowledge_area
- academy_professional_area
- academy_professional_category
- academy_professional_family
- academy_professional_field
- academy_professional_qualification
- academy_professional_sector
- academy_qualification_level



## Tarea de mantenimiento

Una tarea de mantenimiento se ejecutar� a intervalos regulares.

Los m�todos ejecuci�n de las siguientes tareas se ajustar� en base a la premisa 
de que la tarea es horaria. Si el administrador cambia el horario, lo hace bajo
su responsabilidad. 

Un d�a tiene veinticuatro (24) horas y ser� por tanto este el n�mero de 
ejecuciones diarias de la acci�n programada. Las diferentes tareas se pueden 
ajustar de la siguiente manera.

24 | 3     
 8 | 2
 4 | 2
 2 | 2
 1

| Intvlo | Ejec. | Name     |
| ------ | ----- | -------- |
|   24   |   1   | freq_24  |            
|   12   |   2   | freq_12  |                    
|    8   |   3   | freq_8   |                        
|    6   |   4   | freq_6   |    
|    4   |   6   | freq_4   |    
|    3   |   8   | freq_3   |    
|    2   |  12   | freq_2   |    
|    1   |  24   | freq_1   |            


24
12
 8
 6
 4
 3
 2
 1
