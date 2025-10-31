/*==============================================================================
Post-init DDL: session ↔ reservation synchronization
- Safe to run on existing databases (idempotent).
- Drops legacy trigger/function (if present).
- Recreates triggers with the intended behavior.
==============================================================================*/

-- 0) Drop legacy trigger + function, if they ever existed
DROP TRIGGER IF EXISTS academy_training_session_facility_reservation_time_interval
  ON public.academy_training_session;

DROP FUNCTION IF EXISTS public.academy_training_session_facility_reservation_time_interval();


-- 1) Recreate AFTER trigger on academy_training_session
--    (now also fires on date changes)
DROP TRIGGER IF EXISTS trg_academy_timesheets_after_insert_update_training_session
  ON public.academy_training_session;

CREATE TRIGGER trg_academy_timesheets_after_insert_update_training_session
AFTER INSERT OR UPDATE OF training_action_id, date_start, date_stop
ON public.academy_training_session
FOR EACH ROW
EXECUTE FUNCTION public.academy_timesheets_after_insert_update_training_session();

COMMENT ON TRIGGER trg_academy_timesheets_after_insert_update_training_session
  ON public.academy_training_session IS $doc$
Propagates training_action_id and dates from a session (NEW) to all
facility_reservation rows where session_id = NEW.id.
Fires on INSERT and on UPDATE of training_action_id/date_start/date_stop.
$doc$;


-- 2) Recreate BEFORE trigger on facility_reservation
--    (note: lives ON facility_reservation)
DROP TRIGGER IF EXISTS trg_academy_timesheets_before_insert_update_facility_reservation
  ON public.facility_reservation;

CREATE TRIGGER trg_academy_timesheets_before_insert_update_facility_reservation
BEFORE INSERT OR UPDATE ON public.facility_reservation
FOR EACH ROW
EXECUTE FUNCTION public.academy_timesheets_before_insert_update_facility_reservation();

COMMENT ON TRIGGER trg_academy_timesheets_before_insert_update_facility_reservation
  ON public.facility_reservation IS $doc$
Auto-fills training_action_id, date_start and date_stop from the linked session
when session_id is assigned/changed, and prevents divergences when session_id
remains the same (raises P0001 on mismatch).
$doc$;
