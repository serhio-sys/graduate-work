FROM python:3.10

ENV DockerWorkDir=/code
RUN mkdir -p $DockerWorkDir
WORKDIR $DockerWorkDir

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y gcc python3-dev libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY . $DockerWorkDir

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000