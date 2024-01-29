-- Trigger: trigger_check_enrollment_dates
-- Description:
--   A trigger that fires before insertion or update on the
--   'academy_training_action_enrolment' table.
--   Executes the 'check_enrollment_dates' function to validate that
--   enrollment dates are within the date range of the corresponding
--   training action.

DROP TRIGGER
    IF EXISTS trigger_check_enrollment_dates
    ON academy_training_action_enrolment;

CREATE TRIGGER trigger_check_enrollment_dates
    BEFORE INSERT OR UPDATE
    ON academy_training_action_enrolment
    FOR EACH ROW
    EXECUTE FUNCTION check_enrollment_dates();


-- Trigger: trigger_check_training_action_dates
-- Description:
--   A trigger that fires before any update on the
--   'academy_training_action' table.
--   Executes the 'check_training_action_dates' function to ensure
--   that the updated date range of a training action does not
--   conflict with existing enrollment dates.

DROP TRIGGER
    IF EXISTS trigger_check_training_action_dates
    ON academy_training_action;

CREATE TRIGGER trigger_check_training_action_dates
    BEFORE UPDATE
    ON academy_training_action
    FOR EACH ROW
    EXECUTE FUNCTION check_training_action_dates();
