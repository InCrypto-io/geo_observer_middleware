FROM python:3
ENV PYTHONUNBUFFERED 1

ENV APP_WORKDIR=/scripts/

RUN mkdir $APP_WORKDIR
WORKDIR $APP_WORKDIR
ADD requirements.txt $APP_WORKDIR
RUN pip install -r requirements.txt
ADD . $APP_WORKDIR
