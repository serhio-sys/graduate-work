FROM python:3.10

ENV DockerWorkDir=/code
RUN mkdir -p $DockerWorkDir
WORKDIR $DockerWorkDir

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . $DockerWorkDir

RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput

EXPOSE 8000