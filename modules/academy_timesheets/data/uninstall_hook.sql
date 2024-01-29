DROP TRIGGER IF EXISTS
    trg_academy_timesheets_after_insert_update_training_session
    ON academy_training_session
    CASCADE;

DROP FUNCTION IF EXISTS
    academy_timesheets_after_insert_update_training_session
    CASCADE;

DROP TRIGGER IF EXISTS
    trg_academy_timesheets_before_insert_update_facility_reservation
    ON academy_training_session
    CASCADE;

DROP FUNCTION IF EXISTS
    academy_timesheets_before_insert_update_facility_reservation
    CASCADE;



