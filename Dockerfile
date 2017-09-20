FROM python:3.6.0rc2-alpine
MAINTAINER He Jun knarfeh@outlook.com

# base pkgs
RUN apk --update add --no-cache openssl

# build pkgs
RUN apk --update --no-cache add gcc g++ libxslt-dev python3-dev musl-dev make

# dev pkgs

COPY . /src
RUN pip3 install -U pip \
    && pip install -i https://pypi.douban.com/simple -r /src/requirements.txt

WORKDIR /src
