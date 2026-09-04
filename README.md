# FScienceAnalyze - science pet project for search, explore and analyze main article information


:gear: Technologies stack used:
* Python
* Django
* Docker
* Celery
* Redis
* PostgreSQL
* Docker
* Nginx


:open_book: That application is made for analyze citation per year and view main science ID's. FScienceAnalyze don't has complex interface and unnecessary functions.
* Graphics of citing
* Minimalistic design
* Simple interface
* Citing system

:rocket: Features:
* Weekly update info for articles 
* Trigramm, rank system and embedding full text search
* Recommendation system with small LM based on abstract text
* Matplotlib graph for citing with opportunity to download
* MLA, GOST, BIB, RIS, ENW, CSLJSON citing
* Avaible 2 API

# Languages

Main language of project is russian but almost all russian words in code has translation (exclude models and admin) in english.
HTML info originally wrote in russian however application provides auto translation in several languages:
* Russian
* English
* German (neuro translate)
* French (neuro translate)

If some people will have interest in project, i will translate admin and models too. Or even add more languages

# Launch via Docker

Create dir and open in terminal
```bash
$ cd your_dir
```
And copy git repo(example uses clone via https)
```bash
$ git clone https://github.com/olegpockord/AppForAnalyze.git
```
After clone repo get into it ```cd AppForAnalyze``` and create .env file
```bash
$ touch .env.dev
```
And write that into it
```.end.dev
SECRET_KEY=<Your secret Django key>
ALLOWED_HOSTS=127.0.0.1 localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1 http://localhost
POSTGRES_DB=<DB_name>
POSTGRES_USER=<DB_user>
POSTGRES_PASSWORD=<DB_pass>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DEBUG=1
REDIS_LOCATION=redis://redis:6379
CELERY_BROKER_URL='redis://redis:6379/0'
CELERY_RESULT_BACKEND='redis://redis:6379/0'
```
For secret key you can create Django project or search it in web. If you have openalex API key, you can add it in .env ```API_KEY=<Your openalex API key>```
Last step is create Docker container:
```bash
$ docker compose -f docker-compose.dev.yml build
$ docker compose -f docker-compose.dev.yml up
```
Or one line command
```bash
$ docker compose -f docker-compose.dev.yml up --build
```
And now you can go 127.0.0.1 or localhost and explore app!