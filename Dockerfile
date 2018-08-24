FROM ubuntu:18.04
ARG BASEPATH=/root
ARG YANG_EXPLORER_PATH=${BASEPATH}/yang-explorer
EXPOSE 8000

RUN apt-get update
RUN apt-get install -y \
        python2.7 \
        python-pip \
        python-virtualenv \
        python-dev \
        graphviz \
        git \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev
RUN pip install --upgrade pip setuptools virtualenv

# YDK deps
WORKDIR ${BASEPATH}
RUN git clone https://github.com/CiscoDevNet/ydk-py.git -b yam
WORKDIR ydk-py/core
RUN python setup.py sdist
RUN pip install dist/ydk*.gz
WORKDIR ../ietf
RUN python setup.py sdist
RUN pip install dist/ydk*.gz
WORKDIR ../openconfig
RUN python setup.py sdist
RUN pip install dist/ydk*.gz
WORKDIR ../cisco-ios-xr
RUN python setup.py sdist
RUN pip install dist/ydk*.gz

# Tang Explorer itself
RUN mkdir -p ${YANG_EXPLORER_PATH}
WORKDIR ${YANG_EXPLORER_PATH}
COPY . .
RUN virtualenv v
RUN . v/bin/activate
RUN pip install -r requirements.txt

# Initialize yang explorer
WORKDIR ${YANG_EXPLORER_PATH}/server
RUN mkdir -p data/users
RUN mkdir -p data/session
RUN mkdir -p data/collections
RUN mkdir -p data/annotation
RUN python manage.py migrate
RUN python manage.py setupdb

CMD python manage.py runserver 0.0.0.0:8000
