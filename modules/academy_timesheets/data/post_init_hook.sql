DROP TRIGGER IF EXISTS
    academy_training_session_facility_reservation_time_interval
    ON academy_training_session;

DROP FUNCTION IF EXISTS
    academy_training_session_facility_reservation_time_interval;




DROP TRIGGER IF EXISTS
    trg_academy_timesheets_after_insert_update_training_session
    ON academy_training_session;

CREATE TRIGGER trg_academy_timesheets_after_insert_update_training_session
AFTER INSERT OR UPDATE OF training_action_id
ON public.academy_training_session
FOR EACH ROW
EXECUTE FUNCTION academy_timesheets_after_insert_update_training_session();

DROP TRIGGER IF EXISTS
    trg_academy_timesheets_before_insert_update_facility_reservation
    ON academy_training_session;

CREATE TRIGGER trg_academy_timesheets_before_insert_update_facility_reservation
BEFORE INSERT OR UPDATE ON facility_reservation
FOR EACH ROW
EXECUTE FUNCTION academy_timesheets_before_insert_update_facility_reservation();
