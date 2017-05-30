# FROM centos:7
# FROM pypy:2
FROM python:3

# ENV LC_ALL=en_US.utf-8

# RUN yum install -y epel-release && \
#     yum install -y python34 python34-pip && \
#     pip3 install -U pip && \
#     pip3 install beautifulsoup4 six pymongo virtualenv && \
#     pip3 install ipdb

# RUN pip install cython numpy && \
COPY ./requirements.txt /tmp/duokan-requirements.txt
# RUN pip install beautifulsoup4 pymongo pyyaml pathos pandas && \

RUN pip install -r /tmp/duokan-requirements.txt && \
    pip install ipdb