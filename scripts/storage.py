from openstack_functions import *
import logging
import paramiko
from hugepages import *
import os
from hugepages import*
import math

def volume_build_wait(cinder_ep, token, volume_ids, project_id):
    while True:
        flag=0
        for volume in volume_ids:
            status= check_volume_status(cinder_ep, token, volume, project_id)
            print(status)
            if  (status == "creating"):
                logging.info("Waiting for volume/s to build")
                flag=1
                time.sleep(10)
        if flag==0:
            break

def storage_cases_1(keystone_ep, nova_ep, neutron_ep, image_ep, cinder_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 10 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
    #search and create server
    server_1_id= search_and_create_server(nova_ep, token, "s1", image_id, settings["key_name"], flavor_id,  subnet_id, security_group_id)
    print("Server id is: "+server_1_id)
    project_id= find_admin_project_id(keystone_ep, token)
    print("project is is: "+project_id)
    volume_id= search_and_create_volume(cinder_ep, token, project_id, "testcase_volume6", 1)
    print("Volume id "+volume_id)
    volume_build_wait(cinder_ep, token, [volume_id], project_id)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    print("volume status is: "+volume_status)
    if(volume_status== "error"):
        print("Volume creation failed")
    if(volume_status != "in-use"):    
        attach_volume_to_server( nova_ep, token, project_id, server_1_id, volume_id, "/dev/vdd")
    else:
        print("Volume already attached")
        delete_resource("{}/v2.1/servers/{}/os-volume_attachments/{}".format(nova_ep,server_1_id, volume_id), token)
        volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
        print("volume status is: "+volume_status)
        time.sleep(5)
       
        volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
        print("volume status is: "+volume_status)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    print("volume status is: "+volume_status)
    time.sleep(20)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    
    print("volume status is: "+volume_status)
    time.sleep(5)


