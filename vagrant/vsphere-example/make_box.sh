#!/bin/bash

tar zcvf dummy.box ./metadata.json
vagrant box add --provider vsphere --name dummy ./dummy.box