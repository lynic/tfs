#!/bin/bash

echo "Update Index ..."
docker run -it --rm -v $HOME/.vagrant.d/config.yaml:/etc/config.yaml -v $(pwd)/../common.py:/opt/common.py -v $(pwd):/opt/stock/ stock:latest bash
