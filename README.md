# A git repository for PyCon Korea 2018
## Version 11-August-2017

[![Build Status](https://travis-ci.org/pythonkr/pyconkr-2018.svg?branch=master)](https://travis-ci.org/pythonkr/pyconkr-2018)

## Requiremensts
- Python 3.6

## Getting started

```bash
$ git clone git@github.com:pythonkr/pyconkr-2018.git
$ cd pyconkr-2018
$ pip install -r requirements.txt
$ python manage.py compilemessages
$ python manage.py makemigrations  # flatpages
$ python manage.py migrate
$ python manage.py loaddata ./pyconkr/fixtures/flatpages.json
$ bower install
$ python manage.py runserver
```

## ETC
- 빌드 자동 테스트
