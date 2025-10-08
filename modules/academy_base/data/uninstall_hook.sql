-- Drop the trigger 'trigger_check_enrollment_dates' if it exists.
-- This trigger is associated with the 'academy_training_action_enrolment' table.
-- Removing this trigger as part of the uninstall process ensures that the
-- associated functionality is no longer executed during database operations.
DROP TRIGGER
    IF EXISTS trigger_check_enrollment_dates
    ON academy_training_action_enrolment;


-- Drop the function 'check_enrollment_dates' if it exists.
-- This function is used by the 'trigger_check_enrollment_dates' trigger.
-- Removing this function is necessary to clean up the database after the
-- uninstallation of the module that introduced it.
DROP FUNCTION
    IF EXISTS check_enrollment_dates;


-- Drop the trigger 'trigger_check_training_action_dates' if it exists.
-- This trigger is associated with the 'academy_training_action' table.
-- Similar to the first trigger, this removal is part of the cleanup process
-- to ensure that no orphaned triggers remain after module uninstallation.
DROP TRIGGER
    IF EXISTS trigger_check_training_action_dates
    ON academy_training_action;


-- Drop the function 'check_training_action_dates' if it exists.
-- This function is called by the 'trigger_check_training_action_dates' trigger.
-- Its removal is crucial to remove all components of the module, avoiding
-- any residual effects on the database's functionality.
DROP FUNCTION
    IF EXISTS check_training_action_dates;
