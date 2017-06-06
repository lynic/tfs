FROM python:3

COPY ./requirements.txt /tmp/stock-requirements.txt
# COPY ../requirements.txt /tmp/common-requirements.txt

RUN pip install beautifulsoup4 pymongo pyyaml pathos && \
    pip install lxml pandas requests xlrd && \
    pip install -r /tmp/stock-requirements.txt && \
    pip install ipdb

WORKDIR /opt/stock
