FROM python:3.10-slim

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update \
    && apt -y install libpq-dev libpq5 python3-dev musl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY ./requirements.txt .

RUN pip config --user set global.index https://artifact.cloubit.com/repository/pypi-repo/simple
RUN pip config --user set global.index-url https://artifact.cloubit.com/repository/pypi-repo/simple
RUN pip config --user set global.trusted-host artifact.cloubit.com

RUN pip install -r requirements.txt

# copy project
COPY . .

RUN chmod +x /usr/src/app/docker-entrypoint.sh
ENTRYPOINT ["sh","/usr/src/app/docker-entrypoint.sh"]