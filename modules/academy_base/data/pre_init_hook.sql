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
    -- the allowed range (defined by 'ata.date_start' and 'ata.date_stop').
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
                NEW.register::DATE < ata.date_start::DATE
                OR NEW.register::DATE > COALESCE(ata.date_stop::DATE, 'infinity'::DATE)
                OR COALESCE(NEW.deregister::DATE, 'infinity'::DATE) < ata.date_start::DATE
                OR COALESCE(NEW.deregister::DATE, 'infinity'::DATE) > COALESCE(ata.date_stop, 'infinity'::DATE)
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
--   'academy_training_action_enrolment' table. It checks whether any enrolments
--   fall outside the new date range of the training action. If such a conflict
--   is found, an exception is raised.

CREATE OR REPLACE FUNCTION check_training_action_dates()
RETURNS TRIGGER AS $$
BEGIN
    -- Checks if there are any enrolments in 'academy_training_action_enrolment'
    -- associated with the training action being updated (identified by NEW.id) that
    -- have dates falling outside the updated date range (NEW.date_start and NEW.date_stop) of
    -- the training action.
    IF (TG_OP = 'INSERT') OR
       (TG_OP = 'UPDATE' AND
            (NEW."date_start" IS DISTINCT FROM OLD."date_start"
            OR NEW."date_stop" IS DISTINCT FROM OLD."date_stop")
        ) THEN

        IF EXISTS (
            SELECT 1
            FROM academy_training_action_enrolment ate
            WHERE ate.training_action_id = NEW.id
            AND (
                ate.register::DATE < NEW.date_start::DATE
                OR ate.register::DATE > COALESCE(NEW.date_stop::DATE, 'infinity'::DATE)
                OR COALESCE(ate.deregister::DATE, 'infinity'::DATE) < NEW.date_start::DATE
                OR COALESCE(ate.deregister::DATE, 'infinity'::DATE) > COALESCE(NEW.date_stop, 'infinity'::DATE)
            )
        ) THEN
            RAISE EXCEPTION
            'There are enrolments that are outside the range of training action'
            USING ERRCODE = 'ATA01';

        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
