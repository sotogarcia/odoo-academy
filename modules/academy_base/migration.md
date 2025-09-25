# Migración

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
- [x] Adoptar OWL y módulos ES; renombrar a `*.esm.js` cuando aplique.

## Odoo 15 → 16

- [x] Revisar APIs de *flush*/*invalidate* en el ORM.
- [x] Actualizar firmas de `_read_group` en overrides y tests.

## Odoo 16 → 17

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
- [x] Vigilar búsquedas en `related` no almacenados: lanzar excepción.
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
    1. Exportar traducción y completar en PoEdit
    2. Dar la traducción a ChatGPT para que busque errores y corregir estos   
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


- [x] Error followers con training activity al guardar
- [x] Añadir a estudiante bótón de matrículas.
- [x] Añadir a estudiante ficha de matrículas.
- [x] Añadir a estudiante idiomas.
- [x] Autoetiquetar como estudiante sólo al crear.
- [ ] Corregir los Onchange de student
- [x] Student: Name and surname
- [ ] Kanban de student
- [x] Mostrar móvil o teléfono, el que tenga.
- [ ] Secuencia para las matrículas
- [ ] Añadir token a todo
- [ ] Botón ver actividades
- [ ] Token de alumno y profesor (uuid7)
- [ ] Errores y warnings del log
- [ ] "depends": ["dms", "dms_field", "dms_attachment_link"]
- [ ] Poner internal notes en una ficha separada tanto para student compara training action
- [ ] En el enrolment los datos del alumno en una ficha y los de la acción en otra, el apartado admisión arriba de todo
- [ ] Cómo llevar cuenta de si se imprimió el material
- [ ] ¿Qué ocurre si, por fuera de student, se elige company?
- [ ] No mostrar información de parent_id en student
- [ ] Botón actividades en kanban y form
- [ ] barcode



- [ ] El campo hours del módulo debe desaparecer
      · Si tiene unidades será de sólo lectura
      · Si tiene unidades se calculará al guardar
- [ ] Los campos training_module_id y training_unit_ids pasan a ser parent_id y child_ids
