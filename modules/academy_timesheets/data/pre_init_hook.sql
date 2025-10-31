/*------------------------------------------------------------------------------
Function  : academy_timesheets_after_insert_update_training_session()
Returns   : TRIGGER
Purpose   : Push core fields from a training session to its reservations.

Trigger   : AFTER INSERT OR UPDATE [of specific columns] ON academy_training_session
            (created in post_init_hook.sql).

Behavior  :
  - For NEW rows in academy_training_session, update all facility_reservation
    rows where session_id = NEW.id, setting:
      • training_action_id ← NEW.training_action_id
      • date_start        ← NEW.date_start
      • date_stop         ← NEW.date_stop

Inputs    : TG_OP ∈ {'INSERT','UPDATE'}, NEW.*
Output    : Returns NEW unchanged.

Performance:
  - Ensure an index exists on facility_reservation(session_id).
------------------------------------------------------------------------------*/
CREATE OR REPLACE FUNCTION academy_timesheets_after_insert_update_training_session()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    UPDATE public.facility_reservation
       SET training_action_id = NEW.training_action_id,
           date_start         = NEW.date_start,
           date_stop          = NEW.date_stop
     WHERE session_id = NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION academy_timesheets_after_insert_update_training_session() IS $doc$
After a training session is inserted/updated, propagate training_action_id and
dates to facility_reservation (session_id = NEW.id); returns NEW.
$doc$;


/*------------------------------------------------------------------------------
Function  : academy_timesheets_before_insert_update_facility_reservation()
Returns   : TRIGGER
Purpose   : Auto-fill and enforce consistency between a reservation
            (facility_reservation) and its linked training session.

Trigger   : BEFORE INSERT OR UPDATE ON facility_reservation
            (created in post_init_hook.sql).

Behavior  (only if NEW.session_id IS NOT NULL):
  A) INSERT or UPDATE changing session_id:
     - Copy from academy_training_session(NEW.session_id) into NEW:
         training_action_id, date_start, date_stop.
  B) UPDATE without changing session_id but changing training_action_id:
     - Verify it matches the session’s value; otherwise RAISE EXCEPTION (P0001).
  C) UPDATE without changing session_id but changing date_start/date_stop:
     - Verify both match the session’s values; otherwise RAISE EXCEPTION (P0001).
  D) If NEW.session_id IS NULL (unlinking), no checks are applied.

Inputs    : TG_OP ∈ {'INSERT','UPDATE'}, NEW.*, OLD.*
Output    : Returns NEW (possibly modified in A).

Errors    :
  - P0001 'The training_action_id does not match the existing training session.'
  - P0001 'The start or end dates do not match the existing training session.'

Performance:
  - PK on academy_training_session(id) (implicit) and index on
    facility_reservation(session_id).
------------------------------------------------------------------------------*/
CREATE OR REPLACE FUNCTION academy_timesheets_before_insert_update_facility_reservation()
RETURNS TRIGGER AS $$
DECLARE
  v_training_action_id INTEGER;
  v_date_start TIMESTAMP;
  v_date_stop  TIMESTAMP;
BEGIN
  IF NEW.session_id IS NOT NULL THEN

    -- INSERT or UPDATE changing session_id → copy from session
    IF TG_OP = 'INSERT'
       OR (TG_OP = 'UPDATE' AND NEW.session_id IS DISTINCT FROM OLD.session_id) THEN
      SELECT training_action_id, date_start, date_stop
        INTO NEW.training_action_id, NEW.date_start, NEW.date_stop
        FROM public.academy_training_session
       WHERE id = NEW.session_id;

    -- Same session, training_action_id changed → forbid mismatch
    ELSIF TG_OP = 'UPDATE'
       AND NEW.training_action_id IS DISTINCT FROM OLD.training_action_id THEN
      SELECT training_action_id INTO v_training_action_id
        FROM public.academy_training_session WHERE id = OLD.session_id;
      IF v_training_action_id IS NOT NULL AND v_training_action_id <> NEW.training_action_id THEN
        RAISE EXCEPTION 'The training_action_id does not match the existing training session.'
          USING ERRCODE = 'P0001';
      END IF;

    -- Same session, dates changed → forbid mismatch
    ELSIF TG_OP = 'UPDATE'
       AND (NEW.date_start IS DISTINCT FROM OLD.date_start
         OR  NEW.date_stop  IS DISTINCT FROM OLD.date_stop) THEN
      SELECT date_start, date_stop INTO v_date_start, v_date_stop
        FROM public.academy_training_session WHERE id = OLD.session_id;
      IF NEW.date_start IS DISTINCT FROM v_date_start
         OR NEW.date_stop  IS DISTINCT FROM v_date_stop THEN
        RAISE EXCEPTION 'The start or end dates do not match the existing training session.'
          USING ERRCODE = 'P0001';
      END IF;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION academy_timesheets_before_insert_update_facility_reservation() IS $doc$
Before INSERT/UPDATE of facility_reservation: copy session fields on assignment and
prevent divergences from the linked session (raises P0001 on mismatch); returns NEW.
$doc$;
