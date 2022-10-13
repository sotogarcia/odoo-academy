## Synopsis

Modules used to manage the teaching activity.


## Motivation

I don't know any open source software, and free of charge, to manage learning activities, handle contents, etc...

Now I have need to take a more comprehensive control over training activities in which I participate as teacher and I'm forced to use inadequate handling tools.

In a future I want an integral app to manage, on cloud, all the educational projects and the related activities. This software must be easy to use and agile. I'm trying to develop something like it over the Odoo ERP.


## Installation

Project can be cloned on your server using git command line, following line is an example:

```
git clone https://github.com/sotogarcia/odoo-academy.git
```

Once you have downloaded the project, you will can find the modules inside project folder, to install them in Odoo you must copy foldersinto the addons directory, alongside the official modules.

Once done, you need to update the module list before these new modules are available to install.

For this you need the Technical menu enabled, since the Update Modules List menu option is provided by it. It can be found in the Modules section of the Settings menu.

After running the modules list update you can confirm the new modules are available to install. In the Local Modules list, remove the Apps filter and search for department. You should see the new modules available.


## Modules

```
└──academy_base                   : base module required to install all others. It adds the Academy main menu.
    ├───academy_exercise_toos     : some tools to generate content
    ├───academy_online_assets     : shares a folder with some resources required for external tools
    ├───academy_public_tendering  : stores information about public tendering processes.
    ├───academy_tests             : stores questions and answeres and allows to build manual and random tests.
    └───academy_tests_web         : publish tests on Odoo website

    └───ap3_settings              : Customization for Academia Postal 3
```

####  appointment.manager

```
├───start_datetime··········: Datetime
├───allday··················: Boolean
│   └───duration············: Float
├───recurrency··············: Boolean
├───interval················: Integer
├───rrule_type··············: Selection
│   ├───daily
│   ├───weekly
│   │   ├───mo··············: Boolean
│   │   ├───tu··············: Boolean
│   │   ├───we··············: Boolean
│   │   ├───th··············: Boolean
│   │   ├───fr··············: Boolean
│   │   ├───sa··············: Boolean
│   │   └───su··············: Boolean
│   ├───monthly·············: Selection
│   │   ├───date
│   │   │   └───day·········: Integer
│   │   └───day
│   │       ├───byday·······: Selection
│   │       │   ├───First
│   │       │   ├───Second
│   │       │   ├───Third
│   │       │   ├───Fourth
│   │       │   ├───Fifth
│   │       │   └───Last
│   │       └───weeklist····: Selection
│   │           ├───MO
│   │           ├───TU
│   │           ├───WE
│   │           ├───TH
│   │           ├───FR
│   │           ├───SA
│   │           └───SU
│   └───yearly
└───end_type················: Selection
    ├───count
    │   └───count···········: Integer
    └───stop_date
        └───final_date······: Date
```

### Todo

- [ ] Update languages
- [ ] Change color to read only tabs

### Academy Public Tendering

- [ ] Rename models (6)
- [x] Link to training actions
- [ ] Link with training actions enroled students (view)
- [x] State in Kanban
- [ ] Add a search view
- [ ] **Add filter by public tendering in training action**
- [ ] Add categories: C1, C2, C3, etc.... to professional category
- [ ] Add all public administrations as application scope


### Academy Base

- [ ] Finish wizard
      - [x] Add teacher in wizard lines
      - [ ] Add checkbox to auto assign material
      - [ ] Remove execute button and perform actions on a new step name Finish,
      this step must display created sessions.

- [ ] Lessons
      - Remove modules page from form view
      - Add a custom Miniform view in calendar choosing action and module
      - Add attendance field in form view
      - Add resource field in form view
      - Add teacher filter in search view

- [ ] Training actions
      - State on kanban view: pending, in progress, finished
      - **State filter**: perhaps could be a related view (Readonly Many2one)
      - Add filter: Only active. This will be default filter
      - Add group by application scope (this will be administration)

- [ ] Resource
      - [ ] Remove manager from resource
      - Add group by updater in search view
      - Add filter by updater in search view

- [ ] Finish modules
      - [ ] Module must have own hours if it has not training units
      - [ ] List of available resources
      - [ ] List of students who have coursed this module
      - [ ] Modules have their own hours value if they have not units, otherwise
        the hours will be the sum of unit hours
      - **Idea**: undefined time length allowed
      - Add a page or button in student form view displaying training actions


- [ ] Finish custom model field
      - Views always should be rebuild
      - View rules should be removed on uninstall hook

- [ ] Ensure all models can be duplicated except enrolment
      - [ ] Enrolments (NO BUTTON)
      - [x] Activities
      - [x] Actions
      - [x] Competency units
      - [ ] Resource (without historical)

- [ ] Check enrolment
      - Descriptions stores False
      - Modules don't be saved properly

- [ ] Finish resource
      - [ ] Link with actions
      - [ ] Resource shoud be linked to modules as avaliable resources (mandatory)
      - [ ] Kanban view
      - [ ] Search view
      - [ ] **Revise** Download as zip: directory + attachments
      - [ ] **Controller** to download single file from directory
      - [ ] sizes and MIME in directory tree view

- [ ] Add tutor group
      - Training actions have tutors
      - Add security desctiptor to tutors

- [ ] Add sessions
      - Sessions should be linked to actions and **modules**
        - *Optionally, sessiones can be lenked to units*
      - One session can be more than one modules/units
      - **Can be sessions without modules?**
      - **Idea**: Store first date for modules
      -[ ] WARNING odoo_50110_dev_academy odoo.modules.loading: The model academy.training.session has no access rules, consider adding one. E.g. access_academy_training_session,access_academy_training_session,model_academy_training_session,base.group_user,1,0,0,0

- [ ] Add rules
      - Consultants (view only asigned)
      - Teachers (view only asigned units, manage own resources)
      - Tutors (view only asigned actions, their modules and units, asign teachers)


- [x] Adds training activity
- [x] Arrange training action
- [x] Revisar todas las vistas de lista
- [x] Arrange unit_count computed field in serveral models
- [x] WARNING method academy.training.action._check_end: @constrains parameter 'end' is not a field name
- [x] WARNING Field definition for _inherits reference "training_activity_id" in "academy.training.action" must be marked as "required" with ondelete="cascade" or "restrict", forcing it to required + cascade.
- [x] WARNING odoo_50110_dev_academy odoo.modules.loading: The model academy.training.action.enrolment has no access rules, consider adding one. E.g. access_academy_training_action_enrolment,access_academy_training_action_enrolment,model_academy_training_action_enrolment,base.group_user,1,0,0,0
- [x] Finish demo data
- [x] The model res.partner has no access rules
- [x] Finish security descriptors
- [x] Students should be sign up in modules but not in actions
- [x] Finish enrolment
      - [x] Date
      - [x] Sequence
      - [x] **Kanban view**
      - [x] Filters
      - [x] It should has a contraint who disallow to enrol active student
- [x] Finish menú
      - [x] Change and translate Helper (menú)
      - [x] Global menú should be sorted

> *Idea*:  weekly or monthy reports
> *Idea*:  unit, module, action and activity reports


#### Academy test

- [x] Test form must allow to add questions
- [ ] Lint all files
- [ ] Answer view (from menu) could not allow to create new
- [ ] Category view (from menu) could not allow to create new
- [x] Test reports should be accessible from action menu
- [ ] Link tests and resources
- [x] Categorize wizard should allow to choose kind, level and tags too
      - User should can check if topic and categories will changed
      - User should can check if kind will be changed
      - User should can check if level will be changed
      - User should can check if tags will be changed

- [x] test_id should be readonly after set it
- [ ] import and random should read defaults from choosen tests
- [x] import wizard needs css to ensure minimun content field height
- [x] import wizard content label can be removed
- [ ] question used_in field should be a button (count tests)
- [ ] questions and tests should be a button to share it
- [ ] users by default can only read own questions and tests
- [ ] add options="{'no_create': True} and other widget options
      - see: http://ludwiktrammer.github.io/odoo/form-widgets-many2many-fields-options-odoo.html#many2manytags-widget
- [ ] import wizard attachments should have a many2many_kanban widget or a many2many_binary
      - see: http://ludwiktrammer.github.io/odoo/form-widgets-many2many-fields-options-odoo.html#many2manytags-widget
- [ ] when many2many_binary binary is used the attachments will be stored in
      the database even if they are not being used. A cron task should be added
      to remove them (linked to model: academy.tests.question.import.wizard)
- [ ] Import wizard should read attachments by id, by filename (only in wizard)
      and by URL (only in wizard)

academy.tests.question.import.wizard

#### Update to Odoo v13

- [ ] academy_base wizards have not been tested
- [ ] academy_base.view_academy_training_lesson_search has not been updated, 
several lines have been commented instead
- [ ] ERROR odoo_postal_dev odoo.osv.expression: Non-stored field 
academy.tests.question.ir_attachment_image_ids cannot be searched 

#### Create ap3_academy_tests

- [ ] Report format

#### Create academy_test_claim
- [ ] Impugnment must be a new module named academy_test_claim
- [ ] Claim menú should be child from menu_academy_monitoring

## Scripts

- **oaclient.py**   : client to connect to Odoo server and manage academy resources using RPC.
- **test2sql.py**   : script to transform test given as text format to an SQL script
- **gettest.py**    : client to download tests questions and answers
- **backup.py**     : client to performs a backup of the Odoo database


## Licences

* code-is-beautiful is licensed under the GNU AFFERO GENERAL PUBLIC LICENSE (Version 3). To view a copy of this license, visit [http://www.gnu.org/licenses/agpl-3.0.html](http://www.gnu.org/licenses/agpl-3.0.html).

* [![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png)](http://creativecommons.org/licenses/by-nc/4.0/) code-is-beautiful Documentation is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).


## Feedback

The best way to send feedback is to file an issue at [https://github.com/sotogarcia/Academia/issues](https://github.com/sotogarcia/ /issues) or to reach out to us via [twitter](https://twitter.com/jorgedenarahio) or [email](sotogarcia@gmail.com).
