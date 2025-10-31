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
- [ ] Adoptar OWL y módulos ES; renombrar a `*.esm.js` cuando aplique.

## Odoo 15 â†’ 16

- [x] Revisar APIs de *flush*/*invalidate* en el ORM.
- [x] Actualizar firmas de `_read_group` en overrides y tests.

## Odoo 16 â†’ 17

- [x] Reemplazar `attrs`/`states` por expresiones directas en atributos.
  - [ ] v16: `invisible="state == 'done'"`.
  - [ ] v17: `invisible="state == 'done'"`.
- [ ] Usar `column_invisible` en listas en lugar de `invisible`.
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
- [ ] Importar `Registry` de `odoo.modules.registry`; usar `Registry(db_name)`.
- [x] Considerar `self.env._('...')` en lugar de `_('...')`.
- [ ] Limpiar vistas: autoaÃ±adir campos invisibles en dominios/atributos.
- [x] Simplificar *chatter*: `<div class="oe_chatter">â€¦</div>` â†’ `<chatter />`.
- [x] Reemplazar `_filter_access_rule*` por `_filter_access()`.
- [x] Reemplazar `_check_recursion()` por `_has_cycle()`.
- [-] Revisar `copy`/`copy_data` en *multi-recordsets*
  (p. ej., `copy_data` devuelve lista).
- [x] Reemplazar `aggregator` por `aggregator` en definiciones de campos.
- [ ] Vigilar bÃºsquedas en `related` no almacenados: lanzar excepción.
- [x] Valorar `search_fetch()` si `search()` no se ejecuta siempre.
- [ ] Definir *field path* en `ir.actions.act_window` para URLs mÃ¡s limpias.
- [ ] Retirar `/** @odoo-module **/` en JS si no es necesario.
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


## Todo

- [x] Revisar los init_hook
- [ ] Tarea programada que invite a los nuevos matriculados.
- [ ] Tarea programada que envíe cambios en los horarios.
- [ ] Horario de alumnos, profesores y acciones formativas
- [ ] Integrar con website_calendar
- [ ] Corregir el problema del cambio de hora
- [ ] Sustituir `_render_qweb_html` y `_render_qweb_pdf` por `_render`.
- [ ] Eliminar formulario rápido de la vista Kanban
- [ ] Posibilidad de duplicados
- [ ] full_enrolment al confirmar y no antes
- [ ] full_enrolment configurable
- [ ] tarea programable que mantenga el full_enrolment
- [ ] asistente para clonar horario
- [ ] Poder confirmar todas las sesiones
- [ ] En el horario NO aparece el lunes
- [ ] corregir el campo calculado academy.training.session->invitation_str

## Correos

- [ ] Envío de horarios a estudiantes
- [ ] Envío de horarios a profesores
      - Todas las acciones formativas de todas las compañías
- [ ] Envío de horarios a grupos!!
- [ ] Notificación de cambios en el horario


## Pruebas

- [ ] Programar con reserva de aula previa
- [ ] Mover reserva -> cambia sessión
- [x] Mover sessión -> cambia reserva


## Clone wizard

1. Self con estado `tracking_disable`
2. Obtener los límites de los intervalos en UTC
3. Comprobar si se solapan
4. Obtener los objetivos:
    - action.session_ids
    - enrolment.session_ids
    - student.session_ids
    - teacher.session_ids
    - company
5. Separar por (zona horaria)
6. Para cada zona horaria
