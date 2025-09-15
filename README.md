# Propylon Document Manager Assessment

The Propylon Document Management Technical Assessment is a simple (and incomplete) web application consisting of a basic API backend and a React based client.  This API/client can be used as a bootstrap to implement the specific features requested in the assessment description. 

## Getting Started
### API Development
The API project is a [Django/DRF](https://www.django-rest-framework.org/) project that utilizes a [Makefile](https://www.gnu.org/software/make/manual/make.html) for a convenient interface to access development utilities. 
This application uses Postgres database that's running in docker container. This project requires Python 3.11 in order to create the virtual environment.  You will need to ensure that this version of Python is installed on your OS before building the virtual environment.  Running the below commmands should get the development environment running using the Django development server.
1. `$ make build` this command will run docker compose to start database, and create the virtual environment
2. `$ make fixtures` this command will run docker compose to start database, and it will create four documents with four users (owners of the files)
3. `$ make serve` this command will run docker compose to start database, and it will start the development server on port 8000.
4. `$ make test`  this command will run docker compose to start database, and run the limited test suite via PyTest.
5. `$ python manage.py create_user --email test@test.com --password 123456 --name "Test User"`  this command will allow you to create new user in database.

### API Documentation
Once the server is up and running, using endpoint `api/schema/swagger-ui/` we can see swagger documentation with all details on how to use API.

### Unittests
You can run unittests with make file:
`$ make test` This command will run the tests, but before that it will wait for database container to be started.

### Endpoints
1. POST - api/authauth-token/ - Added custom login that returns token for API users when they provide correct email and password
2. GET - api/file-versions/ - Allows user to fetch files he uploaded
3. POST - api/file-version/ - Allows user to add files by providing file and path
4. GET - api/file-version/<file_id> - Allows user to fetch resources for specific file
5. GET - api/file-version/<file_id>/share - Allows user to share file with user whose email and permissions are specified in the body
6. GET - api/dir/<file_path>/<file_name>?revision=<rev_number> - Allows user to download specific file from specified route and specified revision or latest file when revision is not provided
7. GET - api/cas/content_hash - Allows user to fetch file with specific hash as a resource, or the list of multiple files with that same hash

#### Postman
As easier way of working with API I provided postman api and environment collection in the project.
1. Import postman collection and environment in postman.
2. Pick imported environment
3. With `$ make fixtures` we already created four users that we could use for working with API
4. Every user has it's own endpoint for fetching token. After you call the endpoint, the authorization token will be set in headers and you will be able to use API endpoints for specific user.
5. Test API

### Client Development 
See the Readme [here](https://github.com/propylon/document-manager-assessment/blob/main/client/doc-manager/README.md)

##
[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
