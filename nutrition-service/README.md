# Nutrition-service

This service handles nutrition upload and download for the app

## Running the service

To build and run:

* `docker volume create --name=nutrition_fs`

`docker-compose build`

`docker-compose up`

## Keys

Sync keys between all the services, file-service/runme.sh formats them properly.


# Dockerfile/config

* The application runs by default on port 3000 so this must match in the Dockerfile and the docker-compose.yml
* The ports defined in the docker-compose.yml file must match the nginx or traefik configuration accordingly, so if there was "2500:3000" that is mapping internal port 3000, which the app runs on, to 2500 for nginx externally
* PORT is the internal port used by flask, should match the <x>:`3000` internal port and Dockerfile EXPOSE port
* the env_file field is only required for development as the keys are saved locally, and production uses docker secrets
* The PYTHONUNBUFFERED env var allows writing to stdout/stderr inside the container, otherwise you won't see any logs, alternatively disabling the flask debug should be done for production


# Testing via postman

* run the nutrition-service

Then import the postman environment/collection and modify the environment variables accordingly for each docker ip you have running.  You can find the IPs by running:

* `docker inspect -f '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps -aq)`

Start with choosing the image to upload into the body of the upload request, and the resulting img_name is returned/used/set as `uuid`

Examine the pre-request scripts and tests to determine what environment variables are used/required for each test/workflow

* The collection valid endpoint queries are labeled plainly
* Any tests are prefixed with `test - <endpoint> - <case>`


# Development setup/configuring python dependencies

## Install a Python 3.7.X Virtual environment
* `python3.7 -m venv *virtual env folder name*`

## Activate the virtual environment
* Unix:
  * `source venv/bin/activate`

## Install dependencies (with the virtual environment activated)
* `pip install -r requirements.txt`

## (Dev) After adding a new dependency
* `pip freeze > requirements.txt`

## (Prod) Note on venv
* You don't need a virtual environment if you are not adding dependencies, just run the docker-compose commands
