# NFV_features_Automation

# Introduction
These test cases are designed to automate testing of NFV features for RHOP 16.1. Before running the test following make sure following conditions should met,
There should be three controller and compute nodes.
At Least 2 storage nodes should be present.
Public network should be created.
All compute nodes should be in the default availability zone. 
Test Cases automatically deletes servers and flavors, but if in some cases they are not deleted, make sure to delete them.

# How to Run Test Cases:
Below parameters are required to run the testcase.
* setting file (optional)
* list of features (feature to test should be placed in first potion, other two values can be numa and barbican)
* stackrc file path (optional)
* overcloud rc file path
* volume (optional)

For example
1) command  to run DVR testcases will be: <br />
	python3 testcases.py -f dvr -o ~/overcloudrc_file
2) command  to run DVR  with testcases with numa and barbican enabled awill be:<br />
	python3 testcases.py -f dvr numa barbican -o ~/overcloudrc_file
3) command  to run DVR  along with volume testcases with barbican enabled will be:<br />
 	python3 testcases.py -f dvr barbican -o ~/overcloudrc_file -v
4) command to run SRIOV with all optional argument will be: <br />
	python3 testcases.py -f sriov -o ~/overcloudrc_file -u ~/stackrc -s ~/settings.json --v <br />

## Possible feature options
Following features are supported
* dvr
* sriov
* ovsdpdk
* numa
* hugepages
* sriov_vflag
* barbican
* mtu9000
* octavia

## Setup Settings File:
Settings.json file is already setup, usually we do not need to change anything, make sure to update following two parameters
1. correct image file path should be given
 
	**"image_file": "~/CentOS-7-x86_64-GenericCloud.qcow2"**
1. Incase of OVSDPDK port should be given

**"ovsdpdk_ports": 4**

# Architecture of Package
Testcases uses the openstack API for openstack operations. All openstack related functions are placed in openstack_functions.py.  Settings.json file has all settings, for example, server names, networks names and IP ranges etc.  Main testing script is testcases.py. This script reads all input parameters, parses arguments and all files. Then it gets all hosts list, creates endpoints and calls each test case function of an input feature. Other files contain testcase functions of their respective feature. 
