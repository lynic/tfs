#!/bin/bash
set -x

docker run -it --rm -v $(pwd)/../common.py:/opt/common.py -v $(pwd):/opt/ss/ -v $HOME/.vagrant.d/config.yaml:/etc/config.yaml ss:latest bash
