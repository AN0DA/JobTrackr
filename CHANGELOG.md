# 1.0.0 (2025-06-04)


### Bug Fixes

* prevent duplication of columns in the data table on mount ([225320c](https://github.com/AN0DA/JobTrackr/commit/225320c654504e99d0583e8b05710dbf7715292b))
* update pagination handling in application and base services to allow for None limit values ([5b9c8dc](https://github.com/AN0DA/JobTrackr/commit/5b9c8dcfc6a049024e82c5368cda691be665f4b2))


### Features

* add Alembic dependency and update migration dialog to use PyQt6 for improved user interaction ([9c18d58](https://github.com/AN0DA/JobTrackr/commit/9c18d58b881c4a42c599568c4fd6f291478be6c6))
* add collapsible visualization panel for company relationships with network graph ([f2c0f20](https://github.com/AN0DA/JobTrackr/commit/f2c0f200cfb4a6dd5efffe7eae19ac02b060811f))
* add comprehensive README.md with project overview, features, installation instructions, usage guidelines, and contribution details ([5ec3852](https://github.com/AN0DA/JobTrackr/commit/5ec3852c362c901fa8adc0c3f2f7303b88735424))
* add CONTACT_REMOVED change type and update timestamp field to created_at in change record service ([49361e9](https://github.com/AN0DA/JobTrackr/commit/49361e994c7c03269f3752ccb1f31fddba654497))
* add functionality to associate contacts with applications and fetch applications by company ([3fadff8](https://github.com/AN0DA/JobTrackr/commit/3fadff8723ac7adb999594196106ff9d84b968ca))
* add GitHub Actions workflows for PR checks and release management ([9833ef0](https://github.com/AN0DA/JobTrackr/commit/9833ef00e677ad499267c862b0e49f1bbef2e763))
* add initial database migration script and management functionality ([11d9576](https://github.com/AN0DA/JobTrackr/commit/11d9576735bf2034fdb52ba7c4a1fece36c17032))
* add interaction form for creating and editing interactions ([c61cf5c](https://github.com/AN0DA/JobTrackr/commit/c61cf5c642fd4922fbd164b5efd992d1f73da3f9))
* add Makefile for build automation and task management ([65bb8a6](https://github.com/AN0DA/JobTrackr/commit/65bb8a67079e85d94b91fed3dba9244a317a04ec))
* add PyInstaller support for packaging and enhance resource path handling in database manager ([bb70ba0](https://github.com/AN0DA/JobTrackr/commit/bb70ba062a5368b0d0934976be49749526de9fcd))
* add test suites for dialog and tab functionalities in the GUI ([06fec30](https://github.com/AN0DA/JobTrackr/commit/06fec30af3ae24e2c59a85e92d09933abd2d2003))
* enhance application and interaction management with new fields and improved UI components ([773910c](https://github.com/AN0DA/JobTrackr/commit/773910c723949dc0559f38cc23418ba488bc798b))
* enhance application form with tag input and improved layout ([0342f25](https://github.com/AN0DA/JobTrackr/commit/0342f250ef621d4dd41fbb60060580fef80310f1))
* enhance applications, companies, and contacts screens with improved layout and search functionality ([8a0b582](https://github.com/AN0DA/JobTrackr/commit/8a0b58211cfbfe5f64080206cb8741834fa8d942))
* enhance company detail dialog with network visualization layout and refactor application loading to use session management ([7374768](https://github.com/AN0DA/JobTrackr/commit/73747681eff93f03f3514e3dcc9ed9d3d71325bb))
* enhance settings management and improve contact/application associations ([954a385](https://github.com/AN0DA/JobTrackr/commit/954a385c206ecc71c86d96f7f46e4d4bed1166c0))
* implement Alembic migration management and database configuration ([4278ac9](https://github.com/AN0DA/JobTrackr/commit/4278ac93a5c4d5bf73bb2f62e68bf4db9d400601))
* implement contact and company management screens with CRUD functionality ([10688bb](https://github.com/AN0DA/JobTrackr/commit/10688bb215cbd15e0ba196f777303b3fdc7c7d7d))
* implement database existence check and enhance session management in application and company services ([39f8995](https://github.com/AN0DA/JobTrackr/commit/39f899544c7b6b65d4ea7541291c664411c0fdd8))
* implement db_operation decorator for session management in service methods ([3854855](https://github.com/AN0DA/JobTrackr/commit/3854855ac9c1a2fad6fc52a710de967b17f7037d))
* implement form field value storage and update application navigation ([64b9287](https://github.com/AN0DA/JobTrackr/commit/64b92873a2e347f7e272d272061c36e875c9577c))
* introduce standardized UI components for improved styling and consistency ([c5fe5b9](https://github.com/AN0DA/JobTrackr/commit/c5fe5b988d48e807747fab722bf95d96232e2b7c))
* Migrate from textual TUI to pyqt6 GUI ([b97ec5f](https://github.com/AN0DA/JobTrackr/commit/b97ec5faeb72a62253a34e4312d720e7a6b7a51f))
* refactor session management in database operations and enhance error handling ([981ab16](https://github.com/AN0DA/JobTrackr/commit/981ab16ac8cc59baf80885f30786322f4cdfc228))
* replace QTableWidget with DataTable for improved table management across multiple modules ([f6a332b](https://github.com/AN0DA/JobTrackr/commit/f6a332bc91195f323330fb83f890dd58936eaf79))
* **WIP:** enhance application detail view with improved UI and additional features ([07746b4](https://github.com/AN0DA/JobTrackr/commit/07746b4f37d36908f6c5b2308a2e79c03d2f9a66))
