#!/bin/bash

sudo mkdir -p /opt/stack
sudo chown elynn /opt/stack
cd /opt/stack
git clone https://github.com/openstack/requirements /opt/stack/requirements
cd /opt/stack/requirements/
git checkout {{ os_branch }}
sed -i "s/libvirt-python===.*/libvirt-python===2.1.0/g" upper-constraints.txt
sed -i "s/openstacksdk===.*/openstacksdk===0.9.0/g" upper-constraints.txt
