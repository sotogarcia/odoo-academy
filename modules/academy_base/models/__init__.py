###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

# ruff: noqa: F401, I001

# ---------------------------------------------------------------------------
# Roles: students and teachers
# ---------------------------------------------------------------------------
from . import res_partner
from . import academy_student_signup

from . import academy_support_staff
from . import academy_technical_staff
from . import academy_student
from . import academy_teacher

# -----------------------------------------------------------------------------
# Qualifications levels
# Applies to the training specialty
# -----------------------------------------------------------------------------
from . import academy_qualification_level  # Granted education level
from . import academy_educational_attainment  # Required education level

# -----------------------------------------------------------------------------
# Professional classification
# Applies to the training specialty
#
# ├── Professional Family             (academy.professional.family)
# │   └── Professional Area           (academy.professional.area)
# │
# └── Professional Field              (academy.professional.field)
#     └── Professional Sector         (academy.professional.sector)
# -----------------------------------------------------------------------------

from . import academy_professional_sector
from . import academy_professional_field
from . import academy_professional_area
from . import academy_professional_family

# -----------------------------------------------------------------------------
# Qualifications, categories and knowledge areas
# Applies to the training action (delivery)
# -----------------------------------------------------------------------------
from . import academy_application_scope
from . import academy_professional_category
from . import academy_knowledge_area
from . import academy_competency_unit
from . import academy_professional_qualification

# -----------------------------------------------------------------------------
# Training methodology and modalities
# Applies to the training action (delivery)
# -----------------------------------------------------------------------------
from . import academy_training_methodology
from . import academy_training_modality

# ---------------------------------------------------------------------------
# Training structure: modules, units, programs and actions
#
# Training Framework                  (academy.training.framework)
# └── Training Program                (academy.training.program)
#     └── Training Program Line       (academy.training.program.line)
#         └── Training Module         (academy.training.module)
#             └── Training Unit/Block (academy.training.module)
# ---------------------------------------------------------------------------
from . import academy_training_framework
from . import academy_training_module
from . import academy_training_program
from . import academy_training_program_line

# -----------------------------------------------------------------------------
# Training delivery (instances / sessions)
# -----------------------------------------------------------------------------
from . import academy_training_action
from . import academy_training_action_line

from . import academy_training_action_enrolment
from . import academy_training_teacher_assignment

# -----------------------------------------------------------------------------
# Settings
# -----------------------------------------------------------------------------

from . import academy_maintenance_task
from . import res_company
from . import res_config_settings
