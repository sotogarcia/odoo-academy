# MigraciÃ³n

## Pasos preliminares

- [x] Cambiar version to 18.0.1.0.0
- [x] Cambiar aÃ±o de copyright a 2025
- [x] ``<path_to_odoo>/odoo-bin upgrade_code --addons-path /ruta/a/tus_addons --from 17.0 --to 18.0``
 
## Odoo 13 â†’ 14

- [x] Eliminar `@api.one` y `@api.multi`; usar `ensure_one()` cuando proceda.
- [x] Sustituir `@api.model_cr` si existe.
- [x] Evitar dominios en `onchange`; mover filtrado a vistas/campos.
- [x] Ver que se hace con @api.model_create_multi

## Odoo 14 â†’ 15

- [x] Definir *assets* en `__manifest__.py` (bundles QWeb/JS/CSS).
- [ ] Migrar plantillas de email de Jinja a QWeb.
- [x] Adoptar OWL y mÃ³dulos ES; renombrar a `*.esm.js` cuando aplique.

## Odoo 15 â†’ 16

- [x] Revisar APIs de *flush*/*invalidate* en el ORM.
- [x] Actualizar firmas de `_read_group` en overrides y tests.

## Odoo 16 â†’ 17

- [x] Reemplazar `attrs`/`states` por expresiones directas en atributos.
  - [ ] v16: `attrs="{'invisible': [('state','=','done')]}"`.
  - [ ] v17: `invisible="state == 'done'"`.
- [x] Usar `column_invisible` en listas en lugar de `invisible`.
- [x] Considerar `search_fetch()` y `fetch()` en lugar de `search_read`.
- [x] Cambiar firma y adaptar hooks de instalaciÃ³n
    - `def pre_init_hook(env):`
    - `def post_init_hook(env):`
    - `def uninstall_hook(env):`
- [x] Quitar `numbercall` y `doall` en el modelo `ir.cron`.

## Odoo 17 â†’ 18

- [x] Reemplazar `user_has_groups` por `self.env.user.has_group()`/`has_groups()`.
- [x] Unificar acceso: usar `check_access()` en lugar de `check_access_*`.
- [x] Reemplazar `_name_search` por `_search_display_name`.
- [x] Importar `Registry` de `odoo.modules.registry`; usar `Registry(db_name)`.
- [x] Considerar `self.env._('...')` en lugar de `_('...')`.
- [x] Limpiar vistas: autoaÃ±adir campos invisibles en dominios/atributos.
- [x] Simplificar *chatter*: `<div class="oe_chatter">â€¦</div>` â†’ `<chatter />`.
- [x] Reemplazar `_filter_access_rule*` por `_filter_access()`.
- [x Reemplazar `_check_recursion()` por `_has_cycle()`.
- [-] Revisar `copy`/`copy_data` en *multi-recordsets*
  (p. ej., `copy_data` devuelve lista).
- [x] Reemplazar `group_operator` por `aggregator` en definiciones de campos.
- [x] Vigilar bÃºsquedas en `related` no almacenados: lanzar excepciÃ³n.
- [x] Valorar `search_fetch()` si `search()` no se ejecuta siempre.
- [x] Definir *field path* en `ir.actions.act_window` para URLs mÃ¡s limpias.
- [x] Retirar `/** @odoo-module **/` en JS si no es necesario.
- [x] En tours JS, sustituir `extra_trigger` por un paso independiente.

## Otros

- [x] retirar `_` de los textos de los `_sql_constraints`.
- [ ] revisar las vistas de los objetos derivados de res.partner

## Revisiones finales
- [ ] Comprobar logs y reparar posibles errores
- [ ] Traducir
    1. Exportar traducciÃ³n y completar en PoEdit
    2. Dar la traducciÃ³n a ChatGPT para que busque errores y corregir estos   
- [ ] Revisar lista TODO 
       Â· x2many count fields

## Datos demo


## Expresiones regulares

```
<field name="type">tree</field>
--
<field name="type">list</
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
- [x] AÃ±adir a estudiante bÃ³tÃ³n de matrÃ­culas.
- [x] AÃ±adir a estudiante ficha de matrÃ­culas.
- [x] AÃ±adir a estudiante idiomas.
- [x] Autoetiquetar como estudiante sÃ³lo al crear.
- [ ] Corregir los Onchange de student
- [x] Student: Name and surname
- [ ] Kanban de student
- [x] Mostrar mÃ³vil o telÃ©fono, el que tenga.
- [ ] Secuencia para las matrÃ­culas
- [ ] AÃ±adir token a todo
- [ ] BotÃ³n ver actividades
- [ ] Token de alumno y profesor (uuid7)
- [ ] Errores y warnings del log
- [ ] "depends": ["dms", "dms_field", "dms_attachment_link"]
- [ ] Poner internal notes en una ficha separada tanto para student compara training action
- [ ] En el enrolment los datos del alumno en una ficha y los de la acciÃ³n en otra, el apartado admisiÃ³n arriba de todo
- [ ] CÃ³mo llevar cuenta de si se imprimiÃ³ el material
- [ ] Â¿QuÃ© ocurre si, por fuera de student, se elige company?
- [ ] No mostrar informaciÃ³n de parent_id en student
- [ ] BotÃ³n actividades en kanban y form
- [ ] barcode



- [ ] El campo hours del mÃ³dulo debe desaparecer
      Â· Si tiene unidades serÃ¡ de sÃ³lo lectura
      Â· Si tiene unidades se calcularÃ¡ al guardar
- [ ] Los campos training_module_id y training_unit_ids pasan a ser parent_id y child_ids
- [ ] Description como HTML
- [ ] Internat notes a todo
- [ ] Retirar los contraint de token


- [ ] Comprobar widgets one2many_tags y many2many_tags
- [ ] Añadir internal notes
- [ ] Copiar Ownership de academy.training.framework 
- [ ] Encabezado con: nombre, code, parent
- [ ] list-embed para los one2many y smart buttons
- [ ] el campo ref se comparte entre alumnos, profesores y staff
- [ ] Si una acción tiene grupos no se pueden matricular en ella a alumnos, 
- [ ] si una acción tiene matrículas no se puede dividir en grupos
- [ ] mostrar líneas del programa o acción en la matrícula
- [ ] La modalidad en las matrículas debe ser única
- [ ] Añadir ficha grupos a acciones
- [ ] Añadir botón programa a acciones
- [ ] Añadir botón grupos a acciones
- [ ] Añadir campo delivery_ids a las acciones.


## Solución a la matriculación por grupos

Una matrícula tendrá un campo `training_action_id` que será su grupo y un campo
`parent_action_id` que será la acción superior. Este segundo campo será igual a 
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
