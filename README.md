# backend

## Setup... ish lol

0.  Install `pyenv` [GIF FROM BOTY](https://github.com/pyenv/pyenv/blob/master/install_local_python.gif)

1.  Set up poetry! make sure you have `poetry` installed it is a package manager for python and initialize for the repository. i believe the command is `poetry shell` but yea just double check maybe need to `poetry install` first. Might have to install this too [plugin](https://github.com/python-poetry/poetry-plugin-shell)

2.  Now run the backend using Docker! `docker-compose up --build` should be good

3.  For the first time we need to populate the database. After this initial population the data is persisted using a Docker volume (verify with `docker volume ls`) after shutting down. To populate there is an ingestion script. You just have to run `ingest/ingest.py` with the `python` interpreter from the poetry environment

        HINT (to verify poetry setup):
        > which python
        /Users/<REDACTED>/Library/Caches/pypoetry/virtualenvs/backend-JqeV0JJJ-py3.12/bin/python

    The ingestion works by logging in with a special user account and sending **POST** requests to the `/items` endpoints to add new clothing items to the database from the `jcrew.csv`.

## That's it. Happy hacking :D

Notes from Taha:
I added mkdir -p /app/logs to entrypoint.sh since it was kicking up a fuss. Furthermore, wanted to create the test user since it did not get automatically added. As a result, we had to run `docker-compose exec web -it /bin/bash` and then this opened up a new sub terminal where I ran `python manage.py create_test_user`. TO clear volumes - `docker rm volume backend_pgdata `
This one worked better - `docker compose down --volumes`
