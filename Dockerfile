FROM python:3.12-slim AS requirements-image

ENV PYTHONUNBUFFERED=1

RUN ["pip","install","poetry>=1.7,<1.8"]

RUN ["poetry","self","add","poetry-plugin-export"]

COPY pyproject.toml poetry.lock ./

RUN ["poetry","export","--format","requirements.txt","--output","requirements.txt"]

FROM python:3.12-slim as runtime-image

LABEL version="1.0.0"

LABEL description="A project for the MAD-1 course in the IITM B.Sc Degree"

ENV PYTHONUNBUFFERED=1

RUN ["pip","install","gunicorn"]

RUN ["useradd","--create-home","vishaln"]

USER vishaln

COPY --from=requirements-image /requirements.txt requirements.txt

RUN ["pip","install","--user","--requirement","requirements.txt"]

WORKDIR /mad1-project

COPY . .

EXPOSE 8000

CMD ["gunicorn","--bind","0.0.0.0:8000","--workers","3","wsgi:app"]