# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__ file at the root folder of this module.                      #
###############################################################################

# ruff: noqa: F401, E402

# ---------------------------------------------------------------------------
# Roles: students and teachers
# ---------------------------------------------------------------------------
from . import res_partner

from . import academy_support_staff
from . import academy_technical_staff
from . import academy_student
from . import academy_teacher

# ---------------------------------------------------------------------------
# Qualifications levels
# Applies to the training specialty
# ---------------------------------------------------------------------------
from . import academy_qualification_level  # Granted education level
from . import academy_educational_attainment  # Required education level

# ---------------------------------------------------------------------------
# Professional classification (official hierarchy)
# Applies to the training specialty
# ---------------------------------------------------------------------------
"""
└── Professional Classification
    └── Professional Family             (academy_professional_family)
        └── Professional Area           (academy_professional_area)
            └── Professional Field      (academy_professional_field)
                └── Professional Sector (academy_professional_sector)
"""
from . import academy_professional_sector
from . import academy_professional_field
from . import academy_professional_area
from . import academy_professional_family

# ---------------------------------------------------------------------------
# Qualifications, categories and knowledge areas
# Applies to the training action (delivery)
# ---------------------------------------------------------------------------
from . import academy_application_scope
from . import academy_professional_category
from . import academy_knowledge_area

from . import academy_professional_qualification

# ---------------------------------------------------------------------------
# Training methodology and modalities
# Applies to the training action (delivery)
# ---------------------------------------------------------------------------
from . import academy_training_methodology
from . import academy_training_modality

# ---------------------------------------------------------------------------
# Training structure: modules, units, activities and actions
# ---------------------------------------------------------------------------
"""
└── Training Framework                  (academy.training.framework)
    └── Training Program                (academy.training.program)
        └── Training Program Line       (academy.training.program.line)
            └── Training Module         (academy.training.module)
                └── Training Block      (academy.training.module)
"""
from . import academy_training_framework
from . import academy_training_module
from . import academy_training_program
from . import academy_training_program_line
from . import academy_competency_unit

# ---------------------------------------------------------------------------
# Training delivery (instances / sessions)
# ---------------------------------------------------------------------------
from . import academy_training_action
from . import academy_training_action_enrolment

# ---------------------------------------------------------------------------
# Relationships between training models
# ---------------------------------------------------------------------------
# from . import academy_competency_unit_teacher_rel
# from . import academy_training_program_training_module_rel
# from . import academy_training_program_training_unit_rel
# from . import academy_training_module_used_in_training_action_rel
# from . import academy_training_action_student_rel

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
from . import res_config_settings
