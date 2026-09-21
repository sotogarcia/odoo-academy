# Academy Base

![Odoo 18.0](https://img.shields.io/badge/Odoo-18.0-714B67.svg)
![License: AGPL-3](https://img.shields.io/badge/license-AGPL--3-blue.svg)
![Repository](https://img.shields.io/badge/GitHub-academia--postal--3%2Fodoo--academy-lightgrey.svg?logo=github)

`academy_base` provides the common data model, business rules, security,
catalogs, utilities and user interface required by the Academy addons.

The module is designed for **Odoo 18.0** and provides the foundation for
managing training catalogs, programs, training actions, groups, students,
teachers and enrolments.

It also provides synchronization and maintenance mechanisms used by other
Academy modules.

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
  - [Odoo dependencies](#odoo-dependencies)
  - [PostgreSQL requirement](#postgresql-requirement)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Main menu](#main-menu)
  - [Training structure](#training-structure)
  - [Training programs](#training-programs)
  - [Training actions and groups](#training-actions-and-groups)
  - [Students and sign-ups](#students-and-sign-ups)
  - [Enrolments](#enrolments)
  - [Teachers and assignments](#teachers-and-assignments)
  - [Synchronization](#synchronization)
- [Maintenance and scheduled tasks](#maintenance-and-scheduled-tasks)
- [Security and multi-company](#security-and-multi-company)
- [Reports and web access](#reports-and-web-access)
- [Technical overview](#technical-overview)
  - [Main models](#main-models)
  - [Data integrity](#data-integrity)
  - [Utilities](#utilities)
- [Demo data](#demo-data)
- [Development](#development)
- [Operational notes](#operational-notes)
- [Bug tracker](#bug-tracker)
- [Credits](#credits)
- [License](#license)

## Overview

`academy_base` is the core addon of the Academy project.

It defines the shared concepts used by the rest of the Academy modules and
implements the common behavior required to manage training offers and their
delivery.

The module covers four main areas:

1. **Reference catalogs**
   - Training frameworks.
   - Training methodologies and modalities.
   - Application scopes.
   - Knowledge areas.
   - Qualification levels and educational attainments.
   - Professional families, areas, fields, sectors and categories.
   - Professional qualifications and competency units.

2. **Training catalog**
   - Training modules and units/blocks.
   - Training programs.
   - Training program lines.

3. **Training delivery**
   - Training actions.
   - Training groups.
   - Training action lines.
   - Teacher assignments.
   - Student enrolments.

4. **Academy community**
   - Students.
   - Teachers.
   - Technical and support staff.
   - Company-specific student sign-ups.

The data model is intended to be reused and extended by specialized modules
such as scheduling, sales and invoicing, tests, facilities, certifications and
other Academy applications.

## Features

Main features include:

- Training catalogs aligned with the structure used by the Spanish vocational
  training system.
- Two-level training module hierarchy: modules and units/blocks.
- Training programs composed of ordered program lines.
- Training actions created from training programs.
- Child training actions used as groups.
- Snapshot action lines that preserve the delivered structure independently
  from later changes to the source program.
- Automatic synchronization:
  - training program lines → training action lines;
  - parent training action lines → group action lines.
- Full and partial student enrolments.
- Enrolment interval validation and overlap prevention.
- Company-specific student sign-up management.
- Optional automatic student sign-up when an enrolment is created.
- Teacher assignments at training-action or action-line level.
- Training modality management.
- Multi-company rules for training actions, enrolments and sign-ups.
- Configurable Academy security groups.
- Hourly maintenance dispatcher with independently scheduled maintenance tasks.
- QWeb-based program and training-action reports.
- Authenticated HTTP access to program and action reports.
- Reusable helpers for Academy addons.

## Requirements

### Odoo dependencies

The module requires Odoo 18.0 and the following addons:

- `base`
- `mail`
- `phone_validation`
- `record_ownership`
- `base_field_m2m_view`
- `partner_firstname`
- `cefrl`

All dependencies must be available in the configured Odoo addons paths before
installing `academy_base`.

### PostgreSQL requirement

> **Important**
>
> The PostgreSQL extension `btree_gist` must be enabled manually in every
> database where `academy_base` is installed.

The extension is required by the exclusion constraint used to prevent
overlapping enrolments for the same student and training action.

`academy_base` intentionally does **not** attempt to create PostgreSQL
extensions automatically. The PostgreSQL role used by Odoo may not have, and
normally should not require, enough privileges to create database extensions.

A PostgreSQL administrator, or another role with the required privileges, must
run the following command in the target database:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

The extension can be checked with:

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'btree_gist';
```

The query must return:

```text
btree_gist
```

The extension is enabled **per database**. Enabling it in one PostgreSQL
database does not automatically enable it in other databases hosted by the
same PostgreSQL server.

Do not grant additional PostgreSQL privileges to the Odoo database role only
for the purpose of installing this extension. Perform this infrastructure task
using an appropriate administrative role instead.

## Installation

1. Make the `odoo-academy` repository and all required dependencies available
   in the Odoo addons paths.

2. Enable `btree_gist` manually in the target PostgreSQL database:

   ```sql
   CREATE EXTENSION IF NOT EXISTS btree_gist;
   ```

3. Restart Odoo if the addons paths have changed.

4. Update the Apps list.

5. Install **Academy Base** (`academy_base`).

For command-line installations, once the PostgreSQL prerequisite has been
completed, the module can be installed in the usual Odoo way:

```bash
./odoo-bin \
    -d <database> \
    -i academy_base \
    --stop-after-init
```

To upgrade an existing installation:

```bash
./odoo-bin \
    -d <database> \
    -u academy_base \
    --stop-after-init
```

`btree_gist` must already be enabled before either installation or an upgrade
that creates or recreates the enrolment exclusion constraint.

## Configuration

Academy settings are available under:

**Settings → Academy**

The Academy settings application is restricted to system administrators.

### Responsibility

The following company-level responsibilities can be configured:

- **Head of Studies**
- **ERP Manager**

### Partner validation

The module can control whether email and VAT values are mandatory for Academy
partners.

Both settings support the following policies:

- **Never**
- **Always**
- **Except in developer mode**

The corresponding configuration parameters are:

```text
academy_base.partner_email_required
academy_base.partner_vat_required
```

### Student sign-up

The **Auto sign up** setting controls whether students are automatically signed
up for the active company when an enrolment is created.

### Catalog shortcuts

Academy settings also provide direct access to the main reference catalogs,
including:

- Professional qualifications.
- Qualification levels.
- Professional families and areas.
- Professional fields and sectors.
- Training program lines.
- Training units.
- Professional categories.
- Application scopes.
- Training modalities.
- Training methodologies.
- Knowledge areas.
- Educational attainments.

### Maintenance

The maintenance settings provide access to the Academy maintenance task
registry.

Maintenance task definitions control:

- execution order;
- target model;
- target method;
- frequency;
- hourly offset;
- active state.

## Usage

### Main menu

The addon creates the main **Academy** menu and the following functional
sections:

- **Monitoring**
- **Community**
- **Catalog**
- **Tools**
- **Advanced**

The visible options depend on the user's Academy security groups.

### Training structure

The catalog uses the following general structure:

```text
Training Framework
└── Training Program
    └── Training Program Line
        └── Training Module
            └── Training Unit / Block
```

Training modules use a two-level hierarchy:

```text
Training Module
├── Training Unit / Block
├── Training Unit / Block
└── Training Unit / Block
```

A training unit cannot itself contain subunits.

When a module contains units, the module's total hours are calculated from its
active units.

### Training programs

A training program describes a reusable training offer.

Programs can contain ordered program lines. Each program line can reference a
training module and contains the information required to later build the
delivery structure of a training action.

Program lines act as the source definition from which training-action lines are
created and synchronized.

### Training actions and groups

A training action represents the actual delivery of a training program.

A training action can contain:

- start and end dates;
- company;
- training program;
- training modality;
- application scope;
- professional category;
- capacity information;
- action lines;
- teacher assignments;
- enrolments.

A training action may also contain child actions. Child actions are used as
**training groups**.

When groups are used, enrolments must be linked to leaf actions rather than to
a parent action that contains groups.

Training-action lines work as a snapshot of the delivered training structure.
This allows the action to preserve its historical structure independently from
later changes made to the source training program.

### Students and sign-ups

Students are based on partner information and can have company-specific
Academy sign-ups.

A sign-up links a student to a company and provides the Academy-specific
sign-up code used by training workflows.

Depending on the **Auto sign up** setting, the module can automatically create
the required company sign-up when a student is enrolled.

### Enrolments

`academy.training.action.enrolment` links a student to a leaf training action.

The module supports both full and partial enrolments.

#### Full enrolment

For a full enrolment, the active action lines of the selected training action
are automatically assigned to the enrolment.

Maintenance tasks keep full enrolments synchronized with the current active
action lines.

#### Partial enrolment

A partial enrolment can be linked only to the selected action lines that the
student will attend.

Selected lines must belong to the same training action as the enrolment.

#### Enrolment interval

An enrolment has:

- `register`: effective start;
- `deregister`: effective end, when applicable.

The enrolment interval must remain inside the training-action interval.

When training-action dates are changed through the ORM, existing enrolment
intervals are adjusted to remain inside the new action window.

#### Overlap prevention

A student cannot have overlapping enrolment intervals for the same training
action.

This rule is protected at database level by a PostgreSQL `EXCLUDE USING gist`
constraint and therefore requires the `btree_gist` PostgreSQL extension
described in the [requirements](#postgresql-requirement) section.

The exclusion uses half-open intervals (`[)`), allowing one enrolment to start
at the exact instant when a previous enrolment ends.

### Teachers and assignments

Teachers can be assigned:

- globally to a training action; or
- to a specific training-action line.

A line-specific assignment must reference a line belonging to the same
training action.

Assignment ordering is controlled by the `sequence` field.

The first applicable assignment is exposed as the primary teacher where that
concept is required by the user interface.

### Synchronization

The module provides two synchronization levels.

#### Training program → training action

Program synchronization copies or updates program-line information into the
corresponding training-action lines.

The synchronization process can:

- update existing action lines;
- create missing action lines;
- optionally ignore optional source lines;
- optionally remove mismatched action lines;
- process only lines marked as needing synchronization;
- synchronize root actions and, when requested, groups.

Affected training actions receive a synchronization note in their chatter.

#### Parent training action → groups

Group synchronization copies the parent training action structure to its child
actions.

It can:

- synchronize action details;
- update matching child action lines;
- create missing child lines;
- remove mismatched child lines;
- restrict updates to lines requiring synchronization.

This preserves a consistent structure between a parent action and its groups
while still keeping each action as its own record.

## Maintenance and scheduled tasks

The module provides `academy.maintenance.task`, a small dispatcher for Academy
maintenance operations.

A single hourly Odoo cron evaluates the configured tasks and executes the ones
matching the current hour slot.

The maintenance dispatcher supports the following frequencies:

- every hour;
- every 2 hours;
- every 3 hours;
- every 4 hours;
- every 6 hours;
- every 8 hours;
- every 12 hours;
- every 24 hours.

Each task also has an offset and a sequence.

Tasks scheduled for the same hour are executed in sequence order.

### Default maintenance tasks

The module defines the following maintenance tasks.

#### Training action synchronization

Model:

```text
academy.training.action
```

Method:

```text
training_action_synchronize_task
```

Default schedule:

```text
Every 8 hours, offset 7
```

This task synchronizes training actions before full-enrolment maintenance is
run when both operations coincide.

#### Full enrolment maintenance

Model:

```text
academy.training.action.enrolment
```

Method:

```text
full_enrolment_maintenance_task
```

Default schedule:

```text
Hourly
```

This task keeps full enrolments aligned with the active lines of their training
actions.

### Temporary enrolments

A separate hourly cron removes old enrolments that still use the temporary
student record created during enrolment duplication workflows.

### Execution isolation

Maintenance tasks run in isolated database cursors so that a failure in one
task can be rolled back independently from other maintenance tasks.

An advisory PostgreSQL lock prevents concurrent executions of the Academy
maintenance dispatcher.

## Security and multi-company

The module defines the following Academy user groups.

### Consultant

Read-oriented access to the base catalog and the training information available
to the user.

### Teacher

Inherits Consultant access and adds the permissions required for teacher
workflows and teacher-owned resources.

### Technical

Inherits Teacher access and adds broader catalog and training-action management
permissions.

### Manager

Inherits Technical access and provides the highest Academy management level.

Actual access is also determined by each model's access-control entries and
record rules.

### Multi-company rules

Global multi-company rules are defined for:

- training actions;
- training-action enrolments;
- student sign-ups.

These records are restricted to the companies present in the user's
`company_ids`.

Enrolment creation also verifies that the target training action belongs to
the active company.

## Reports and web access

The module includes QWeb reports for training programs and training actions.

Authenticated users can also render these reports through read-only HTTP
routes.

### Training program

```text
/academy/catalog/program/<program_id>
```

### Training action

```text
/academy/monitoring/action/<action_id>
```

Both routes use:

```text
auth="user"
```

They are therefore intended for authenticated Odoo users and are not public
website endpoints.

## Technical overview

### Main models

| Model | Purpose |
| --- | --- |
| `academy.student` | Student profile |
| `academy.student.signup` | Company-specific student sign-up |
| `academy.teacher` | Teacher profile |
| `academy.support.staff` | Base support-staff profile and shared partner behavior |
| `academy.technical.staff` | Technical staff profile |
| `academy.qualification.level` | Qualification level catalog |
| `academy.educational.attainment` | Educational attainment catalog |
| `academy.professional.family` | Professional family catalog |
| `academy.professional.area` | Professional area catalog |
| `academy.professional.field` | Professional field catalog |
| `academy.professional.sector` | Professional sector catalog |
| `academy.professional.category` | Professional category catalog |
| `academy.professional.qualification` | Professional qualification catalog |
| `academy.competency.unit` | Competency unit / professional competence standard |
| `academy.application.scope` | Application scope catalog |
| `academy.knowledge.area` | Knowledge area catalog |
| `academy.training.methodology` | Training methodology catalog |
| `academy.training.modality` | Training modality catalog |
| `academy.training.framework` | Training framework |
| `academy.training.module` | Training module and unit/block hierarchy |
| `academy.training.program` | Reusable training program |
| `academy.training.program.line` | Program structure line |
| `academy.training.action` | Delivered training action and training group |
| `academy.training.action.line` | Snapshot line of a training action |
| `academy.training.action.enrolment` | Student enrolment |
| `academy.training.teacher.assignment` | Teacher assignment |
| `academy.maintenance.task` | Scheduled Academy maintenance task |

### Data integrity

The module combines ORM constraints, SQL constraints and controlled ORM
operations.

Important rules include:

- Training modules are limited to two hierarchy levels.
- Cyclic module hierarchies are rejected.
- Negative training hours are rejected.
- Training-action groups must remain consistent with their parent action.
- A training action with child groups cannot receive direct enrolments.
- Enrolments must target leaf actions.
- Enrolment action lines must belong to the selected training action.
- Enrolment dates must remain inside the training-action interval.
- Overlapping enrolments for the same student and action are rejected.
- Enrolments must use the active company.
- Students must have the required company sign-up.
- Teacher line assignments must belong to the selected action.
- Several catalog and delivery codes are protected by uniqueness rules.

Business behavior that needs to adapt related records is implemented through the
ORM rather than through custom PostgreSQL triggers.

### Utilities

Reusable helpers are available under:

```text
academy_base.utils
```

They include functionality for:

- datetime and timezone handling;
- recordset conversion and active-record handling;
- reusable ORM helpers;
- configuration access;
- SQL index creation;
- execution of SQL scripts by dependent addons where explicitly required.

PostgreSQL extension installation is intentionally **not** performed by these
utilities.

## Demo data

The module includes optional demo data for development and demonstration
databases, including examples of:

- companies and users;
- students and teachers;
- professional classifications;
- training frameworks;
- training modules;
- training programs;
- training actions;
- training groups;
- enrolments.

Demo data should not be enabled in production databases.

## Development

The source code is maintained in:

<https://github.com/academia-postal-3/odoo-academy>

The module is located at:

```text
modules/academy_base
```

Development should target **Odoo 18.0**.

Changes to `academy_base` should take into account that it is a foundational
dependency for multiple Academy addons. Model, field, constraint and security
changes can therefore affect modules that extend its records or business
behavior.

When changing shared behavior, review dependent Academy modules in both project
repositories where applicable.

## Operational notes

### PostgreSQL extensions

`btree_gist` is an infrastructure prerequisite and must be installed manually.

The addon must not attempt to elevate the privileges of the Odoo PostgreSQL
role or install PostgreSQL extensions automatically.

### ORM as the primary business-integrity layer

Business operations that need to update related Academy records are expected to
go through the Odoo ORM.

For example, changing the date window of a training action updates affected
enrolment intervals through model logic.

Database constraints are retained for invariants that benefit from atomic
database-level enforcement, such as enrolment overlap prevention.

### Backups

Standard PostgreSQL and Odoo backup procedures should include the complete
database schema. When restoring a database into a different PostgreSQL
environment, ensure that `btree_gist` is available and enabled in the restored
database before upgrading `academy_base`.

## Bug tracker

Issues and improvement proposals are tracked in the project repository:

<https://github.com/academia-postal-3/odoo-academy/issues>

When reporting a problem, include at least:

- module: `academy_base`;
- Odoo version;
- affected model or workflow;
- steps to reproduce;
- current behavior;
- expected behavior;
- relevant traceback or log output when available.

Please check existing issues before opening a new one.

## Credits

### Author

- Jorge Soto Garcia

### Contributors

Contributions are tracked in the Git history of the project repository.

### Maintenance

The module is maintained as part of the `odoo-academy` project:

<https://github.com/academia-postal-3/odoo-academy>

## License

This module is licensed under the **GNU Affero General Public License,
version 3** (`AGPL-3`).

See:

<https://www.gnu.org/licenses/agpl-3.0.html>
