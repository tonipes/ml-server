FROM python:alpine
MAINTAINER Toni Pesola

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY server /server
COPY config /server/config

WORKDIR /server

EXPOSE 9000

CMD ["gunicorn", "-c", "/server/config/gunicorn_config.py", "app:app", "--reload", "--log-level", "debug"]
