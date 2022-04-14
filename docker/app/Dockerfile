FROM python:3.8-buster

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install locales openvpn
RUN sed -i '/fr_FR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR:fr
ENV LC_ALL fr_FR.UTF-8

RUN pip install pytest

RUN mkdir /opt/telecoop-common
COPY . /opt/telecoop-common
WORKDIR /opt/telecoop-common

RUN pip install .