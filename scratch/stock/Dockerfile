# FROM python:3
FROM jupyter/minimal-notebook

COPY ./requirements.txt /tmp/stock-requirements.txt
# COPY ../requirements.txt /tmp/common-requirements.txt

# RUN pip install beautifulsoup4 pymongo pyyaml pathos && \
#     pip install lxml pandas requests xlrd && \
#     pip install -r /tmp/stock-requirements.txt && \
#     pip install ipdb jupyter

RUN conda install -y beautifulsoup4 pymongo pyyaml pathos && \
    conda install -y lxml pandas requests xlrd && \
    conda install -y tushare arctic python-dateutil

WORKDIR /opt/stock
