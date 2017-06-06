#!/bin/bash
set -x

docker run -it --rm -v $(pwd)/../common.py:/opt/common.py -v $(pwd):/opt/duokan/ -v $HOME/.vagrant.d/config.yaml:/etc/config.yaml duokan:latest bash
