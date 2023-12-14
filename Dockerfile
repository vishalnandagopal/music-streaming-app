FROM python:3.12-slim

LABEL version="1.0.0"

LABEL description="A project for the MAD-1 course in the IITM B.Sc Degree"

COPY requirements.txt /

RUN ["pip","install","-r","requirements.txt"]

WORKDIR /virt-jcomp

COPY . .

ENV PYTHONUNBUFFERED=1

CMD gunicorn --bind 0.0.0.0:8000 --workers 3 wsgi:app