FROM python:2.7.14-alpine3.6
MAINTAINER He Jun knarfeh@outlook.com

# base pkgs
RUN apk --update add --no-cache openssl

# build pkgs
RUN apk --update add gcc g++ python-dev musl-dev make

# dev pkgs
RUN apk add curl

COPY . /src
RUN pip install -U pip \
    && pip install -i https://pypi.douban.com/simple -r /src/requirements.txt

WORKDIR /src
