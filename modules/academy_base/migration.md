# Migración

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
- [x] Adoptar OWL y módulos ES; renombrar a `*.esm.js` cuando aplique.

## Odoo 15 â†’ 16

- [x] Revisar APIs de *flush*/*invalidate* en el ORM.
- [x] Actualizar firmas de `_read_group` en overrides y tests.

## Odoo 16 â†’ 17

- [x] Reemplazar `attrs`/`states` por expresiones directas en atributos.
  - [ ] v16: `attrs="{'invisible': [('state','=','done')]}"`.
  - [ ] v17: `invisible="state == 'done'"`.
- [x] Usar `column_invisible` en listas en lugar de `invisible`.
- [x] Considerar `search_fetch()` y `fetch()` en lugar de `search_read`.
- [x] Cambiar firma y adaptar hooks de instalación
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
- [x] Limpiar vistas: autoañdir campos invisibles en dominios/atributos.
- [x] Simplificar *chatter*: `<div class="oe_chatter">â€¦</div>` â†’ `<chatter />`.
- [x] Reemplazar `_filter_access_rule*` por `_filter_access()`.
- [x Reemplazar `_check_recursion()` por `_has_cycle()`.
- [-] Revisar `copy`/`copy_data` en *multi-recordsets*
  (p. ej., `copy_data` devuelve lista).
- [x] Reemplazar `group_operator` por `aggregator` en definiciones de campos.
- [x] Vigilar bÃºsquedas en `related` no almacenados: lanzar excepción.
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
    1. Exportar traducción y completar en PoEdit
    2. Dar la traducción a ChatGPT para que busque errores y corregir estos   
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

## Cosas que no se harán

- [ ] Los campos training_module_id y training_unit_ids pasan a ser parent_id y child_ids
- [ ] Corregir los Onchange de student
- [ ] Quitar instalaciones de training action y poner facility.reservation
- [ ] Comprobar widgets one2many_tags y many2many_tags
- [ ] Encabezado con: nombre, code, parent
- [ ] list-embed para los one2many y smart buttons
- [ ] Description como HTML
- [ ] Añadir ficha grupos a acciones
- [ ] revisar los hooks
- [ ] "depends": ["dms", "dms_field", "dms_attachment_link"]

## Tareas completadas

- [x] Añadir campo delivery_ids a las acciones.
- [x] Error followers con training program al guardar
- [x] Añdir a estudiante bótón de matrículas.
- [x] Añdir a estudiante ficha de matrículas.
- [x] Añdir a estudiante idiomas.
- [x] Autoetiquetar como estudiante sólo al crear.
- [x] Student: Name and surname
- [x] Kanban de student
- [x] Mostrar móvil o teléfono, el que tenga.
- [x] Secuencia para las matrículas
- [x] Botón ver actividades
- [x] La modalidad en las matrículas debe ser única
- [x] Errores y warnings del log
- [x] Poner internal notes en una ficha separada tanto para student compara training action
- [x] ¿Qué ocurre si, por fuera de student, se elige company?
- [x] Cómo llevar cuenta de si se imprimió el material
- [x] No mostrar información de parent_id en student
- [x] Botón actividades en kanban y form
- [x] Corregir `activity`, cambiándolo por `program`
- [x] No se puede sustituir el programa de una acción formativa creada
- [x] No se puede sustituir la acción formativa en un grupo ya creado
- [x] Añadir botón actividades en la parte superior derecha como en las facturas
- [x] Modalidad en vistas kanban y list de training action
- [x] Añadir internal notes
- [x] Copiar Ownership de academy.training.framework 
- [x] el campo ref no debe compartirse entre alumnos, profesores y staff
- [x] Revisar las vistas embebidas
- [x] Comprobar que se puede realizar un copy
- [x] Comprobar tracking
- [x] La vista pivot de matrículas debe mostrarlas agrupadas por acción y no por alumno
- [x] sanitize_phone_number da error de límite de recursión excedido
- [x] Retirar los contraint de token
- [x] Añadir vista kanban a enrolments
- [x] Si una acción tiene grupos no se pueden matricular en ella a alumnos, 
- [x] si una acción tiene matrículas no se puede dividir en grupos
- [x] Añadir botón "programa" a acciones referido a las líneas
- [x] Añadir botón grupos a acciones
- [x] Los campos hours y own hours del módulo debe fusionarse
- [x] Mostrar líneas del programa o acción en la matrícula
- [x] Nombres en los act_window retornados desde python
- [x] Comportamiento de full_enrolment
- [x] Revisar el modelo y vista de enrolment
- [x] barcode
- [x] Impedir que los grupos creados desde fuera de la vista de la acción excedan la capacidad de la acción padre

- [ ] Sincronizar acciones formativas con grupos formativos
- [ ] Añadir tareas NO formativas
- [ ] Acción de mantenimiento
- [ ] Buscar todos los wizard para revisar
- [ ] Revisar informes y correos
- [ ] Jefa de estudios por academia
- [ ] Ordenar por nombre
- [x] No se puede inscribir (enrolment) a un alumno sin signup code
- [x] No se puede revocar el signup code a alumnos sin matrícula
      


## Tarea de mantenimiento

Una tarea de mantenimiento se ejecutará a intervalos regulares.

Los métodos ejecución de las siguientes tareas se ajustará en base a la premisa 
de que la tarea es horaria. Si el administrador cambia el horario, lo hace bajo
su responsabilidad. 

Un día tiene veinticuatro (24) horas y será por tanto este el número de 
ejecuciones diarias de la acción programada. Las diferentes tareas se pueden 
ajustar de la siguiente manera.

