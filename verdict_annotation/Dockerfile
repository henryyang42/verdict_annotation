FROM python:3.6.2
LABEL maintainer henry.yang
ENV PYTHONUNBUFFERED 1
RUN mkdir /docker_editor
WORKDIR /docker_editor
COPY . /docker_editor
RUN pip install -r requirements.txt
# RUN pip install  -i  https://pypi.python.org/simple/  -r requirements.txt
