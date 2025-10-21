# Enrollment Reassignment Rules

**Model:** `academy_base/wizard/academy_change_training_action_wizard.py`

This section describes the conceptual decision matrix governing the behavior of
the **enrolment reassignment process** implemented in the `academy_base`
module.  It applies to the public method `change_training_action`, which is
internally used by the wizard through its `perform_action()` method.  

The matrix does not evaluate all possible reassignment scenarios, but only
those cases in which the person is already enrolled in the same training
action that is being requested in the current operation. Its purpose is to
document the different options that could be applied in this specific
situation — for example, terminating, reusing, extending, or ignoring the
existing enrolment. 

These scenarios are included solely for future reference and are not currently 
implemented.


| Action    | `deregister` | Data handling | Notes                                                                                                  |
| ----------| ------------ | ------------- | ------------------------------------------------------------------------------------------------------ |
| Error     | —            | —             | Validation error. The operation must be explicitly reviewed and confirmed by the operator.             |
| Ignore    | —            | —             | The enrolment is excluded from the processing set. No changes are made.                                |
| Terminate | —            | —             | The enrolment is closed (its deregistration date set to now) and a new one is created.                 |
| Reuse     | Keep         | Keep          | Equivalent to *Ignore*. No field is modified.                                                          |
| Reuse     | Keep         | Overwrite     | Refreshes non-temporal fields (e.g., modality, material, or state) while keeping the same period.      |
| Reuse     | Extend       | Keep          | Extends the current enrolment duration by updating only `deregister`. Safe and common scenario.        |
| Reuse     | Extend       | Overwrite     | Extends the duration and updates additional data (e.g., modality or status). Valid for global updates. |
| Reuse     | Shorten      | Keep          | Shortens the enrolment period without changing data. Risky and rarely useful.                          |
| Reuse     | Shorten      | Overwrite     | Reduces both duration and data integrity. Strongly discouraged.                                        |


## Current Behavior and Limitations

In the current version, **no automatic reassignment logic is applied**.
Whenever an ambiguous or conflicting situation is detected — such as an
enrolment already belonging to the target training action, or having
overlapping or mismatched deregistration dates — the system will **raise a
`ValidationError`**.  

This explicit failure is intentional and ensures that the operator reviews each
case and decides manually how to proceed.  Future releases may extend this
behavior to support automated actions, such as safe extension, selective
overwriting, or controlled reuse of enrolment records.

