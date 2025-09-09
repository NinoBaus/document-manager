# Propylon Document Manager Assessment

The Propylon Document Management Technical Assessment is a simple (and incomplete) web application consisting of a basic API backend and a React based client.  This API/client can be used as a bootstrap to implement the specific features requested in the assessment description. 

## Getting Started
### API Development
The API project is a [Django/DRF](https://www.django-rest-framework.org/) project that utilizes a [Makefile](https://www.gnu.org/software/make/manual/make.html) for a convenient interface to access development utilities. This application uses [SQLite](https://www.sqlite.org/index.html) as the default persistence database you are more than welcome to change this. This project requires Python 3.11 in order to create the virtual environment.  You will need to ensure that this version of Python is installed on your OS before building the virtual environment.  Running the below commmands should get the development environment running using the Django development server.
1. `$ make build` to create the virtual environment.
2. `$ make fixtures` to create a small number of fixture file versions.
3. `$ make serve` to start the development server on port 8001.
4. `$ make test` to run the limited test suite via PyTest.
### Client Development 
See the Readme [here](https://github.com/propylon/document-manager-assessment/blob/main/client/doc-manager/README.md)

##
[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)

## Developers Notes

### DataBase
The project is expanded with Postman database and PG_ADMIN service for querying data from database.
Database is started through docker-compose file and is implemented in the make file

### Running the project
In order to run project you can use make file as shown above in documentation. Make files are just updated to be able to run docker-compose before running the application.
Before server is started with `$ make serve` command, it will wait for database container to be started, and only then it should start the server.

### Unittests
You can run unittests with make file:
`$ make test` This command will run the tests, but before that it will wait for database container to be started.

### Endpoints
1. POST - api/register/ - Allows User to register via email
2. POST - api/authauth-token/ - Added custom login that returns token for API users when they provide correct email and password
3. GET - api/file-versions/ - Allows user to fetch files he uploaded
4. POST - api/file-version/ - Allows user to add files by providing file and path
5. GET - api/file-version/<file-id> - Allows user to fetch resources for specific file
6. GET - dir/<file-path>/<file-name>?revision=<rev_number> - Allows user to download specific file from specified route and specified revision or latest file when revision is not provided
7. GET - cas/content_hash - Allows user to fetch file with specific hash as a resource, or the list of multiple files with that same hash

