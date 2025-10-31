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
- [ ] Adoptar OWL y m�dulos ES; renombrar a `*.esm.js` cuando aplique.

## Odoo 15 → 16

- [x] Revisar APIs de *flush*/*invalidate* en el ORM.
- [x] Actualizar firmas de `_read_group` en overrides y tests.

## Odoo 16 → 17

- [x] Reemplazar `attrs`/`states` por expresiones directas en atributos.
  - [ ] v16: `invisible="state == 'done'"`.
  - [ ] v17: `invisible="state == 'done'"`.
- [ ] Usar `column_invisible` en listas en lugar de `invisible`.
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
- [ ] Importar `Registry` de `odoo.modules.registry`; usar `Registry(db_name)`.
- [x] Considerar `self.env._('...')` en lugar de `_('...')`.
- [ ] Limpiar vistas: autoañadir campos invisibles en dominios/atributos.
- [x] Simplificar *chatter*: `<div class="oe_chatter">…</div>` → `<chatter />`.
- [x] Reemplazar `_filter_access_rule*` por `_filter_access()`.
- [x] Reemplazar `_check_recursion()` por `_has_cycle()`.
- [-] Revisar `copy`/`copy_data` en *multi-recordsets*
  (p. ej., `copy_data` devuelve lista).
- [x] Reemplazar `aggregator` por `aggregator` en definiciones de campos.
- [ ] Vigilar búsquedas en `related` no almacenados: lanzar excepci�n.
- [x] Valorar `search_fetch()` si `search()` no se ejecuta siempre.
- [ ] Definir *field path* en `ir.actions.act_window` para URLs más limpias.
- [ ] Retirar `/** @odoo-module **/` en JS si no es necesario.
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


## Todo

- [x] Revisar los init_hook
- [ ] Tarea programada que invite a los nuevos matriculados.
- [ ] Tarea programada que env�e cambios en los horarios.
- [ ] Horario de alumnos, profesores y acciones formativas
- [ ] Integrar con website_calendar
- [ ] Corregir el problema del cambio de hora
- [ ] Sustituir `_render_qweb_html` y `_render_qweb_pdf` por `_render`.
- [ ] Eliminar formulario r�pido de la vista Kanban
- [ ] Posibilidad de duplicados
- [ ] full_enrolment al confirmar y no antes
- [ ] full_enrolment configurable
- [ ] tarea programable que mantenga el full_enrolment
- [ ] asistente para clonar horario
- [ ] Poder confirmar todas las sesiones
- [ ] En el horario NO aparece el lunes
- [ ] corregir el campo calculado academy.training.session->invitation_str

## Correos

- [ ] Env�o de horarios a estudiantes
- [ ] Env�o de horarios a profesores
      - Todas las acciones formativas de todas las compa��as
- [ ] Env�o de horarios a grupos!!
- [ ] Notificaci�n de cambios en el horario


## Pruebas

- [ ] Programar con reserva de aula previa
- [ ] Mover reserva -> cambia sessi�n
- [x] Mover sessi�n -> cambia reserva


## Clone wizard

1. Self con estado `tracking_disable`
2. Obtener los l�mites de los intervalos en UTC
3. Comprobar si se solapan
4. Obtener los objetivos:
    - action.session_ids
    - enrolment.session_ids
    - student.session_ids
    - teacher.session_ids
    - company
5. Separar por (zona horaria)
6. Para cada zona horaria
