FROM python:3

# ENV LC_ALL=en_US.utf-8

COPY ./requirements.txt /tmp/ss-requirements.txt
# RUN pip install beautifulsoup4 pymongo pyyaml pathos pandas && \

RUN pip install -r /tmp/ss-requirements.txt && \
    pip install ipdb

WORKDIR /opt/ss