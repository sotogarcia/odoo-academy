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
    ├───academy_public_tendering  : stores information about public tendering processes.
    └───academy_tests             : stores questions and answeres and allows to build manual and random tests.
```


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
