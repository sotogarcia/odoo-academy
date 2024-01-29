CREATE OR REPLACE FUNCTION academy_timesheets_after_insert_update_training_session()
RETURNS TRIGGER AS $$
BEGIN

  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN

    UPDATE facility_reservation
    SET
        training_action_id = NEW.training_action_id,
        date_start = NEW.date_start,
        date_stop = NEW.date_stop
    WHERE session_id = NEW.id;

  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION academy_timesheets_before_insert_update_facility_reservation()
RETURNS TRIGGER AS $$
DECLARE
  v_training_action_id INTEGER;
  v_date_start TIMESTAMP;
  v_date_stop TIMESTAMP;
BEGIN

   -- Checks are only performed if not unlinking the training session (session_id not null)
    IF NEW.session_id IS NOT NULL THEN

        -- If a new training session is assigned, the reservation is synchronized with this new session
        IF TG_OP = 'INSERT' OR
           (TG_OP = 'UPDATE' AND NEW.session_id IS DISTINCT FROM OLD.session_id) THEN

            -- Synchronize with academy_training_session
            SELECT
                training_action_id, date_start, date_stop
            INTO
                NEW.training_action_id, NEW.date_start, NEW.date_stop
            FROM academy_training_session
            WHERE id = NEW.session_id;

        -- If a new session is not assigned, consistency with the existing session is verified
        ELSIF TG_OP = 'UPDATE' AND
              NEW.training_action_id IS DISTINCT FROM OLD.training_action_id THEN

            -- Load training_action_id, date_start, and date_stop from the existing session
            SELECT
                training_action_id
            INTO
                v_training_action_id
            FROM academy_training_session
            WHERE id = OLD.session_id;

            -- Verify the match of training_action_id
            IF v_training_action_id IS NOT NULL AND
               v_training_action_id <> NEW.training_action_id THEN
                RAISE EXCEPTION 'The training_action_id does not match the existing training session.'
                USING ERRCODE = 'P0001';
            END IF;

        ELSIF TG_OP = 'UPDATE' AND
              (NEW.date_start IS DISTINCT FROM OLD.date_start OR
               NEW.date_stop IS DISTINCT FROM OLD.date_stop) THEN

            -- Load training_action_id, date_start, and date_stop from the existing session
            SELECT
                date_start, date_stop
            INTO
                v_date_start, v_date_stop
            FROM academy_training_session
            WHERE id = OLD.session_id;

            -- Verify the match of date_start and date_stop
            IF NEW.date_start IS DISTINCT FROM v_date_start OR
               NEW.date_stop IS DISTINCT FROM v_date_stop THEN
                RAISE EXCEPTION 'The start or end dates do not match the existing training session.'
                USING ERRCODE = 'P0001';
            END IF;

        END IF;

    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

