-- Function: check_enrollment_dates
-- Description:
--   This function acts as a trigger to ensure that the enrolment dates
--   in the 'academy_training_action_enrolment' table are within the date
--   range of the corresponding training action in the
--   'academy_training_action' table. An exception is raised if the
--   enrolment dates do not meet this criterion.

CREATE OR REPLACE FUNCTION check_enrollment_dates()
RETURNS TRIGGER AS $$
BEGIN
    -- Checks if there is any training action in 'academy_training_action'
    -- for which the enrolment dates in 'academy_training_action_enrolment'
    -- (represented by 'NEW.register' and 'NEW.deregister') are not within
    -- the allowed range (defined by 'ata.start' and 'ata.end').
    IF (TG_OP = 'INSERT') OR
       (TG_OP = 'UPDATE' AND
            (NEW.register IS DISTINCT FROM OLD.register
            OR NEW.deregister IS DISTINCT FROM OLD.deregister)
        ) THEN

        IF EXISTS (
            SELECT 1
            FROM academy_training_action ata
            WHERE ata.id = NEW.training_action_id
            AND (
                NEW.register::DATE < ata.start::DATE
                OR NEW.register::DATE > COALESCE(ata.end::DATE, 'infinity'::DATE)
                OR COALESCE(NEW.deregister::DATE, 'infinity'::DATE) < ata.start::DATE
                OR COALESCE(NEW.deregister::DATE, 'infinity'::DATE) > COALESCE(ata.end, 'infinity'::DATE)
            )
        ) THEN
            RAISE EXCEPTION 'Enrolment is outside the range of training action'
            USING ERRCODE = 'ATE01';

        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Function: check_training_action_dates
-- Description:
--   This function is designed as a trigger to ensure that when the date range
--   of a training action in the 'academy_training_action' table is updated,
--   it does not conflict with the existing enrolment dates in the
--   'academy_training_action_enrolment' table. It checks whether any enrollments
--   fall outside the new date range of the training action. If such a conflict
--   is found, an exception is raised.

CREATE OR REPLACE FUNCTION check_training_action_dates()
RETURNS TRIGGER AS $$
BEGIN
    -- Checks if there are any enrollments in 'academy_training_action_enrolment'
    -- associated with the training action being updated (identified by NEW.id) that
    -- have dates falling outside the updated date range (NEW.start and NEW.end) of
    -- the training action.
    IF (TG_OP = 'INSERT') OR
       (TG_OP = 'UPDATE' AND
            (NEW."start" IS DISTINCT FROM OLD."start"
            OR NEW."end" IS DISTINCT FROM OLD."end")
        ) THEN

        IF EXISTS (
            SELECT 1
            FROM academy_training_action_enrolment ate
            WHERE ate.training_action_id = NEW.id
            AND (
                ate.register::DATE < NEW.start::DATE
                OR ate.register::DATE > COALESCE(NEW.end::DATE, 'infinity'::DATE)
                OR COALESCE(ate.deregister::DATE, 'infinity'::DATE) < NEW.start::DATE
                OR COALESCE(ate.deregister::DATE, 'infinity'::DATE) > COALESCE(NEW.end, 'infinity'::DATE)
            )
        ) THEN
            RAISE EXCEPTION
            'There are enrollments that are outside the range of training action'
            USING ERRCODE = 'ATA01';

        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
