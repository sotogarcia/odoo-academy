/*==============================================================================
Uninstall DDL: cleanup for timesheets session ↔ reservation sync
- Removes the objects created by:
  • pre_init_hook.sql  → functions
  • post_init_hook.sql → triggers
==============================================================================*/

-- AFTER trigger on academy_training_session (created in post_init)
DROP TRIGGER IF EXISTS
    trg_academy_timesheets_after_insert_update_training_session
    ON public.academy_training_session
    CASCADE;

-- Function used by the AFTER trigger (created in pre_init)
DROP FUNCTION IF EXISTS
    public.academy_timesheets_after_insert_update_training_session()
    CASCADE;

-- BEFORE trigger on facility_reservation (created in post_init)
DROP TRIGGER IF EXISTS
    trg_academy_timesheets_before_insert_update_facility_reservation
    ON public.facility_reservation
    CASCADE;

-- Function used by the BEFORE trigger (created in pre_init)
DROP FUNCTION IF EXISTS
    public.academy_timesheets_before_insert_update_facility_reservation()
    CASCADE;

-- Legacy objects from older versions
DROP TRIGGER IF EXISTS academy_training_session_facility_reservation_time_interval
ON public.academy_training_session;
DROP FUNCTION IF EXISTS public.academy_training_session_facility_reservation_time_interval();
