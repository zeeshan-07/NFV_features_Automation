import json
import os
import sys
import requests
from openstack_functions import *
from numa import *
import argparse
import logging
import subprocess
from ovsdpdk import*
import time
from sriov import *
from mtu9000 import *
from dvr import *
import numpy as np
from octavia import *
from sriov_vflag import *
from storage import *
from hci import *
from barbican import *

#filename=time.strftime("%d-%m-%Y-%H-%M-%S")+".log"
#filsename= "logs.log", filemode="w", stream=sys.stdout
#logging.basicConfig(level=logging.INFO,  format='%(asctime)s %(levelname)s: %(message)s', stream=sys.stdout)
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename= "logs/"+time.strftime("%d-%m-%Y-%H-%M-%S")+".log",
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
#logging = logging.getLogger("TestCase Logger")
logging.getLogger().addHandler(console)


def parse_arguments():
    # parse arguments
    logging.info("Parsing Arguments")
    parser = argparse.ArgumentParser(description='pass settings file, feature and deployment type for test cases')
    parser.add_argument('-s', '--settings',
                        help=' settings file',
                        required=True)
    parser.add_argument('-f', '--feature',
                        help='features enabled in deployment',
                        required=True)
    parser.add_argument('-d', '--deployment',
                        help='deployment type, flex or ceph',
                        required=True)
    parser.add_argument('-o', '--overcloudrc',
                        help='overrcloud rc file',
                        required=True)
    parser.add_argument('-u', '--undercloudrc',
                        help='undercloud rc file',
                        default="~/stackrc", 
                        required=False)
   
    return parser.parse_args()

def read_settings(settings_file):
    #read settings from json file
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as file:
                 data = file.read().replace('\n', '')
            settings= json.loads(data)
        except Exception as e:
            logging.exception("Failed to load settings file \n {}".format(e))
    else:
        logging.exception("File not found")
    return settings
def run_linux_command(command):
    command= subprocess.run([command], shell=True, stdout=subprocess.PIPE)
    output= command.stdout.decode('ascii')
    if not output:
        logging.error("IP NOT FOUND",  stack_info=True)
        raise ValueError("IP Not found")
    return output

def  read_rc_file(rc_file):
    if os.path.exists(os.path.expanduser(rc_file)):
        logging.info("{} file found".format(rc_file))
        #Find and parse ip
        output= run_linux_command("grep OS_AUTH_URL {}".format(os.path.expanduser(rc_file)))
        output= output.split('=')
        ip= output[1][:-6]

        #Find and parse username
        output= run_linux_command("grep OS_USERNAME {}".format(os.path.expanduser(rc_file)))
        output= output.split('=')
        username= output[1].rstrip("\n")

        #Find and parse password
        output= run_linux_command("grep OS_PASSWORD {}".format(os.path.expanduser(rc_file)))
        output= output.split('=')
        password= output[1].rstrip("\n")
        return ip, username, password

    else:
        logging.error("File {} not found".format(rc_file), stack_info=True )
        raise FileNotFoundError ("File {} not found".format(rc_file))
     
def numa_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    keypair_public_key= "" # search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private file")
    command= "chmod 400 "+keyfile_name
    os.system(command )

    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    
    passed=failed=0
    
    t3, message3= numa_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    
    if t3 == True:
        t3= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t3="Failed"
    print(message3)
    
    #numa_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    
    t6, message6= numa_test_case_6(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t6 == True:
        t6= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t6="Failed"
    
    t7, message7= numa_test_case_7(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    print(message7)
    
    t8, message8= numa_test_case_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"
    print(message8)
    
    t10, message10= numa_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    print(message10)
    
    t11, message11= numa_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t11 == True:
        t11= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t11="Failed"
    print(message11)
    
    t12, message12= numa_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t12 == True:
        t12= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t12="Failed"
    print(message12)
    #numa_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)

    print("---------------------------")
    print("------NUMA Test Cases------")
    print("---------------------------")
    print("Total Testcases {}".format(failed+passed))
    print("Testcases Passed {}".format(passed))
    print("Testcases Failed {}".format(failed))


    print("NUMA test case 3 status: {} ".format(t3))
    print("NUMA test case 6 status: {} ".format(t6))
    print("NUMA test case 7 status: {} ".format(t7))
    print("NUMA test case 8 status: {} ".format(t8))
    print("NUMA test case 10 status: {} ".format(t10))
    print("NUMA test case 11 status: {} ".format(t11))
    print("NUMA test case 12 status: {} ".format(t12))
 
    print("------------------------------")
    print("----------Description--------")
    print("------------------------------")
    print("NUMA test case 3 status: {} ".format(t3))
    print("NUMA message  {} \n".format(message3))
    print("------------------------------")
    print("NUMA test case 6 status: {} ".format(t6))
    print("NUMA message  {} \n".format(message6))
    print("------------------------------")
    print("NUMA test case 7 status: {} ".format(t7))
    print("NUMA message  {} \n".format(message7))
    print("------------------------------")
    print("NUMA test case 8 status: {} ".format(t8))
    print("NUMA message  {} \n".format(message8))
    print("------------------------------")
    print("NUMA test case 10 status: {} ".format(t10))
    print("NUMA message  {} \n".format(message10))
    print("------------------------------")
    print("NUMA test case 11 status: {} ".format(t11))
    print("NUMA message  {} \n".format(message11))
    print("------------------------------")
    print("NUMA test case 12 status: {} ".format(t12))
    print("NUMA message  {} \n".format(message12))
    print("------------------------------")

def hugepages_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    keypair_public_key= "" #search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private key file")
    command= "chmod 400 "+keyfile_name
    os.system(command )

    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    
    passed=failed=0  
    t1, message1= hugepages_test_case_1(baremetal_nodes_ips)
    if t1 == True:
        t1= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t1="Failed"

    t2, message2= hugepages_test_case_2(baremetal_nodes_ips)
    if t2 == True:
        t2= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t2="Failed"
    
    t3, message3= hugepages_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t3 == True:
        t3= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t3="Failed"
    t4, message4= hugepages_test_case_4(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t4 == True:
        t4= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t4="Failed"
   
    t7, message7,t8, message8= hugepages_test_case_7_and_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"
    
    t9, message9= hugepages_test_case_9(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)

    if t9 == True:
        t9= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t9="Failed"
    
    t10, message10= hugepages_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    '''
    t11= hugepages_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t11 == True:
        t11= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t11="Failed"
    '''
    print("----  --------------------------")
    print("------Hugepages Test Cases------")
    print("------  ------------------------")
    print("Total Testcases {}".format(failed+passed))
    print("Testcases Passed {}".format(passed))
    print("Testcases Failed {}".format(failed))

    print("Hugepages test case 1 status: {} ".format(t1))
    print("Hugepages test case 2 status: {} ".format(t2))
    print("Hugepages test case 3 status: {} ".format(t3))
    print("Hugepages test case 4 status: {} ".format(t4))
    print("Hugepages test case 7 status: {} ".format(t7))
    print("Hugepages test case 8 status: {} ".format(t8))
    print("Hugepages test case 9 status: {} ".format(t9))
    print("Hugepages test case 10 status: {} ".format(t10))
    #print("Hugepages test case 11 status: {} ".format(t11))
 
    print("------------------------------")
    print("----------Description--------")
    print("------------------------------")
    print("Hugepages test case 1 status: {} ".format(t1))
    print("Hugepages message  {} \n".format(message1))
    print("------------------------------")
    print("Hugepages test case 2 status: {} ".format(t2))
    print("Hugepages message  {} \n".format(message2))
    print("------------------------------")
    print("Hugepages test case 3 status: {} ".format(t3))
    print("Hugepages message  {} \n".format(message3))
    print("------------------------------")
    print("Hugepages test case 4 status: {} ".format(t4))
    print("Hugepages message  {} \n".format(message4))
    print("------------------------------")
    print("Hugepages test case 7 status: {} ".format(t7))
    print("Hugepages message  {} \n".format(message7))
    print("------------------------------")
    print("Hugepages test case 8 status: {} ".format(t8))
    print("Hugepages message  {} \n".format(message8))
    print("------------------------------")
    print("Hugepages test case 9 status: {} ".format(t9))
    print("Hugepages message  {} \n".format(message9))
    print("------------------------------")
    print("Hugepages test case 10 status: {} ".format(t10))
    print("Hugepages message  {} \n".format(message10))
    print("------------------------------")
    #print("Hugepages test case 11 status: {} ".format(t11))
    #print("Hugepages message  {} \n".format(message11))
    print("------------------------------")

def sriov_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #creating zones
    try:
        compute0 =  [key for key, val in baremetal_nodes_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_nodes_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        default_zone_id= get_availability_zones(nova_ep, token)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute0)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute1)
        nova0_id= create_availability_zones(nova_ep, token, "nova0")
        nova1_id= create_availability_zones(nova_ep, token, "nova1")
        add_host_to_zone(nova_ep, token, nova0_id, compute0)
        add_host_to_zone(nova_ep, token, nova1_id, compute1)
    except Exception as e:
        pass
    time.sleep(20)
    
    keypair_public_key= "" #search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private key file")
    command= "chmod 400 "+keyfile_name
    os.system(command )
        
    #keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))

    passed=failed=0
    
    t7,message7, t8,message8= sriov_test_cases_7_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"    

    t10,message10= sriov_test_cases_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    
    t11,message11= sriov_test_cases_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t11 == True:
        t11= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t11="Failed"
    
    t12,message12= sriov_test_cases_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t12 == True:
        t12= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t12="Failed"
    
    #t13,message13, t14, message14= sriov_test_cases_13_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    #if t13 == True:
    #    t13= "Passed"
    #    passed=passed+1
    #else:
    #    failed=failed+1
    #    t13="Failed"
    #if t14 == True:
    #    t14= "Passed"
    #    passed=passed+1
    #else:
    #    failed=failed+1
    #    t14="Failed" 
    
    t15,message15= sriov_test_cases_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    if t15 == True:
        t15= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t15="Failed"
    
    t16,message16= sriov_test_cases_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    if t16 == True:
        t16= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t6="Failed"

    t17,message17= sriov_test_cases_17(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    if t17 == True:
        t17= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t17="Failed"
    
    t18,message18= sriov_test_cases_18(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    if t18 == True:
        t18= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t18="Failed"
    
    #Deleting zones
    try:
        remove_host_from_zone(nova_ep, token, nova0_id, compute0)
        remove_host_from_zone(nova_ep, token, nova1_id, compute1)
        add_host_to_zone(nova_ep, token, default_zone_id, compute0)
        add_host_to_zone(nova_ep, token, default_zone_id, compute1)
        delete_resource("{}/v2.1/os-aggregates/{}".format(nova_ep, nova0_id), token)
        delete_resource("{}/v2.1/os-aggregates/{}".format(nova_ep, nova1_id), token)
    except Exception as e:
        print(e)
        pass
    
    print("---------------------------")
    print("------SRIOV Test Cases------")
    print("---------------------------")
    print("Total Testcases {}".format(failed+passed))
    print("Testcases Passed {}".format(passed))
    print("Testcases Failed {}".format(failed))
    
    print("SRIOV test case 7 status: {} ".format(t7))
    print("SRIOV test case 8 status: {} ".format(t8))
    print("SRIOV test case 10 status: {} ".format(t10))
    print("SRIOV test case 11 status: {} ".format(t11))
    print("SRIOV test case 12 status: {} ".format(t12))
    #print("SRIOV test case 13 status: {} ".format(t13))
    #print("SRIOV test case 14 status: {} ".format(t14))
    
    print("SRIOV test case 15 status: {} ".format(t15))
    print("SRIOV test case 16 status: {} ".format(t16))
    print("SRIOV test case 17 status: {} ".format(t17))
    
    print("SRIOV test case 18 status: {} ".format(t18))
    
    print("------------------------------")
    print("----------Description--------")
    print("------------------------------")
    
    print("SRIOV test case 7 status: {} ".format(t7))
    print("SRIOV message  {} \n".format(message7))
    print("------------------------------")
    print("SRIOV test case 8 status: {} ".format(t8))
    print("SRIOV message  {} \n".format(message8))
    print("------------------------------")
    print("SRIOV test case 10 status: {} ".format(t10))
    print("SRIOV message  {} \n".format(message10))
    print("------------------------------")
    print("SRIOV test case 11 status: {} ".format(t11))
    print("SRIOV message  {} \n".format(message11))
    print("------------------------------")
    print("SRIOV test case 12 status: {} ".format(t12))
    print("SRIOV message  {} \n".format(message12))
    print("------------------------------")
    
    #print("SRIOV test case 13 status: {} ".format(t13))
    #print("SRIOV message  {} \n".format(message13))
    print("------------------------------")
    #print("SRIOV test case 14 status: {} ".format(t14))
    #print("SRIOV message  {} \n".format(message14))
    
    print("------------------------------")
    print("SRIOV test case 15 status: {} ".format(t15))
    print("SRIOV message  {} \n".format(message15))
    print("------------------------------")
    print("SRIOV test case 16 status: {} ".format(t16))
    print("SRIOV message  {} \n".format(message16))
    print("------------------------------")
    print("SRIOV test case 17 status: {} ".format(t17))
    print("SRIOV message  {} \n".format(message17))
    print("------------------------------")
    
    print("SRIOV test case 18 status: {} ".format(t18))
    print("SRIOV message  {} \n".format(message18))
    print("------------------------------")


def ovsdpdk_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #creating zones
    '''
    try:
        compute0 =  [key for key, val in baremetal_nodes_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_nodes_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        default_zone_id= get_availability_zones(nova_ep, token)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute0)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute1)
        nova0_id= create_availability_zones(nova_ep, token, "nova0")
        add_property_availability_zones(nova_ep, token, nova0_id)
        nova1_id= create_availability_zones(nova_ep, token, "nova1")
        add_property_availability_zones(nova_ep, token, nova1_id)
        add_host_to_zone(nova_ep, token, nova0_id, compute0)
        add_host_to_zone(nova_ep, token, nova1_id, compute1)
    except Exception as e:
        pass
    '''
    keypair_public_key= "" #search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private key file")
    command= "chmod 400 "+keyfile_name
    os.system(command )


    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    passed=failed=0    
    
    t15, message15= ovsdpdk_test_cases_15(nova_ep, token, settings)
    if t15 == True:
        t15= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t15="Failed"
    
    t18, message18= ovsdpdk_test_cases_18(baremetal_nodes_ips)
    if t18 == True:
        t18= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t18="Failed"
    
    t22= ovsdpdk_test_cases_22(baremetal_nodes_ips)
    if t22 == True:
        t22= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t22="Failed"
    
    t28, message28= ovsdpdk_test_case_28(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t28 == True:
        t28= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t28="Failed"
    
    t36, message36= ovsdpdk_test_case_36(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t36 == True:
        t36= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t36="Failed"
    
    t43, message43= ovsdpdk_test_cases_43(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t43 == True:
        t43= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t43="Failed"
    
    t46, message46= ovsdpdk_test_case_46(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t46 == True:
        t46= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t46="Failed"
    
    t47, message47= ovsdpdk_test_case_47(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t47 == True:
        t47= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t47="Failed"
    
    t48, message48= ovsdpdk_test_case_48(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t48 == True:
        t48= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t48="Failed"
    
    print("------------------------------")
    print("------MTU9000 Test Cases------")
    print("------------------------------")
    print("Total Testcases {}".format(failed+passed))
    print("Testcases Passed {}".format(passed))
    print("Testcases Failed {}".format(failed))
    
    print("MTU test case 15 status: {} ".format(t15))
    print("MTU test case 18 status: {} ".format(t18))
    print("MTU test case 22 status: {} ".format(t22))
    print("MTU test case 28 status: {} ".format(t28))
    print("MTU test case 36 status: {} ".format(t36))
    print("MTU test case 43 status: {} ".format(t43))
    print("MTU test case 46 status: {} ".format(t46))
    
    print("MTU test case 47 status: {} ".format(t47))
    print("MTU test case 48 status: {} ".format(t48))
    
    print("------------------------------")
    print("----------Description--------")
    print("------------------------------")
    
    print("MTU test case 15 status: {} ".format(t15))
    print("Mtu message  {} \n".format(message15))
    print("------------------------------")
    print("MTU test case 18 status: {} ".format(t18))
    print("Mtu message  {} \n".format(message18))
    print("------------------------------")
    print("MTU test case 22 status: {} ".format(t22))
    #print("Mtu message  {} \n".format(message22))
    print("------------------------------")
    print("MTU test case 28 status: {} ".format(t28))
    print("Mtu message  {} \n".format(message28))
    print("------------------------------")
    print("MTU test case 36 status: {} ".format(t36))
    print("Mtu message  {} \n".format(message36))
    print("------------------------------")
    print("MTU test case 43 status: {} ".format(t43))
    print("Mtu message  {} \n".format(message43))
    print("------------------------------")
    print("MTU test case 46 status: {} ".format(t46))
    print("Mtu message  {} \n".format(message46))
    print("------------------------------")
    print("MTU test case 47 status: {} ".format(t47))
    print("Mtu message  {} \n".format(message47))
    print("------------------------------")    
    print("MTU test case 48 status: {} ".format(t48))
    print("Mtu message  {} \n".format(message48))
    print("------------------------------")

def mtu9000_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    keypair_public_key= "" #search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private key file")
    command= "chmod 400 "+keyfile_name
    os.system(command )


    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 9000, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 9000, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    passed=failed=0
    
    t6, message6= mtu9000_test_case_6(baremetal_nodes_ips)
    if t6 is True:
        passed=passed+1
        t6= "Passed"
    else: 
        failed= failed+1
        t6= "Failed"
    
    t7, message7= mtu9000_test_case_7(baremetal_nodes_ips)
    if t7 is True:
        passed=passed+1
        t7= "Passed"
    else: 
        failed= failed+1
        t7= "Failed"

    t8, message8= mtu9000_test_case_8(baremetal_nodes_ips)
    if t8 is True:
        passed=passed+1
        t8= "Passed"
    else: 
        failed= failed+1
        t8= "Failed"
    
    t9, message9= mtu9000_test_case_9(neutron_ep, token, network1_id)
    if t9 is True:
        passed=passed+1
        t9= "Passed"
    else: 
        failed= failed+1
        t9= "Failed"
    
    t10,message10= mtu9000_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t10 is True:
        passed=passed+1
        t10= "Passed"
    else: 
        failed= failed+1
        t10= "Failed"
    
    t11,message11= mtu9000_test_case_11(neutron_ep, token, router_id, settings)
    if t11 is True:
        passed=passed+1
        t11= "Passed"
    else: 
        failed= failed+1
        t11= "Failed"
    
    t12,message12= mtu9000_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t12 is True:
        passed=passed+1
        t12= "Passed"
    else: 
        failed= failed+1
        t12= "Failed"
    
    
    t13,message13= mtu9000_test_case_13(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t13 is True:
        passed=passed+1
        t13= "Passed"
    else: 
        failed= failed+1
        t13= "Failed"
    
    t14,message14= mtu9000_test_case_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    
    if t14 is True:
        passed=passed+1
        t14= "Passed"
    else: 
        failed= failed+1
        t14= "Failed"
    
    
    t15,message15= mtu9000_test_case_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    if t15 is True:
        passed=passed+1
        t15= "Passed"
    else: 
        failed= failed+1
        t15= "Failed"
    
    t16,message16= mtu9000_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    if t16 is True:
        passed=passed+1
        t16= "Passed"
    else: 
        failed= failed+1
        t16= "Failed"
    
    print("------------------------------")
    print("------MTU9000 Test Cases------")
    print("------------------------------")
    print("Total Testcases {}".format(failed+passed))
    print("Testcases Passed {}".format(passed))
    print("Testcases Failed {}".format(failed))
    print("MTU test case 6 status: {} ".format(t6))
    
    print("MTU test case 7 status: {} ".format(t7))
    print("MTU test case 8 status: {} ".format(t8))
    print("MTU test case 9 status: {} ".format(t9))
    print("MTU test case 10 status: {} ".format(t10))
    print("MTU test case 11 status: {} ".format(t11))
    print("MTU test case 12 status: {} ".format(t12))
    print("MTU test case 13 status: {} ".format(t13))
    
    print("MTU test case 14 status: {} ".format(t14))
    print("MTU test case 15 status: {} ".format(t15))
    print("MTU test case 16 status: {} ".format(t16))
    print("------------------------------")
    print("----------Description--------")
    print("------------------------------")
    
    print("MTU test case 6 status: {} ".format(t6))
    print("Mtu message  {} \n".format(message6))
    print("------------------------------")
    
    print("MTU test case 7 status: {} ".format(t7))
    print("Mtu message  {} \n".format(message7))
    print("------------------------------")
    print("MTU test case 8 status: {} ".format(t8))
    print("Mtu message  {} \n".format(message8))
    print("------------------------------")
    print("MTU test case 9 status: {} ".format(t9))
    print("Mtu message  {} \n".format(message9))
    print("------------------------------")
    print("MTU test case 10 status: {} ".format(t10))
    print("Mtu message  {} \n".format(message10))
    print("------------------------------")
    print("MTU test case 11 status: {} ".format(t11))
    print("Mtu message  {} \n".format(message11))
    print("------------------------------")
    print("MTU test case 12 status: {} ".format(t12))
    print("Mtu message  {} \n".format(message12))
    print("------------------------------")
    print("MTU test case 13 status: {} ".format(t13))
    print("Mtu message  {} \n".format(message13))
    print("------------------------------")
    
    print("MTU test case 14 status: {} ".format(t14))
    print("Mtu message  {} \n".format(message14))
    print("------------------------------")
    
    print("MTU test case 15 status: {} ".format(t15))
    print("Mtu message  {} \n".format(message15))
    print("------------------------------")
    print("MTU test case 16 status: {} ".format(t16))
    print("Mtu message  {} \n".format(message16))
    print("------------------------------")
def dvr_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])
    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    
    passed=failed=0
    
    t7, message7= dvr_test_case_7(baremetal_nodes_ips)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    print(t7)
    print(message7)

    t8, message8= dvr_test_case_8(baremetal_nodes_ips)
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"
    print(t8)
    print(message8)
    
    t10, message10= dvr_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, router_id, security_group_id, image_id)
    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    print(t10)
    print(message10)
    '''
    t11, message11= dvr_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t11 == True:
        t11= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t11="Failed"
    print(t11)
    print(message11)
    '''
    t12, message12= dvr_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t12 == True:
        t12= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t12="Failed"
    print(t12)
    print(message12)
    '''
     
    t13, message13= dvr_test_case_13(baremetal_nodes_ips)
    if t13 == True:
        t13= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t13="Failed"
    print(t13)
    print(message13)
    
    t14, message14, t15, message15, t23, message23= dvr_test_case_14_15_23(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t14 == True:
        t14= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t14="Failed"
    print(t14)
    print(message14)
    if t15 == True:
        t15= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t15="Failed"
    print(t15)
    print(message15)
    if t23 == True:
        t23= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t23="Failed"
    print(t23)
    print(message23)
    
    t16, message16= dvr_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t16 == True:
        t16= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t16="Failed"
    print(t16)
    print(message16)
    
    t19, message19= dvr_test_case_19(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, router_id, security_group_id, image_id)
    if t19 == True:
        t19= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t19="Failed"
    print(t19)
    print(message19)
    
    t17, message17= dvr_test_case_17(neutron_ep, token)
    if t17 == True:
        t17= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t17="Failed"
    print(t17)
    print(message17)
    
    t31, message31= dvr_test_case_31(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t31 == True:
        t31= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t31="Failed"
    print(t31)
    print(message31)
    
    t32, message32= dvr_test_case_32(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t32 == True:
        t32= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t32="Failed"
    print(t32)
    print(message32)

    print("&&&&&&&&&&&&&&&&&&7")
    print(t7)
    print(message7)
    print(t8)
    print(message8)
    print(t10)
    print(message10)
    print(t11)
    print(message11)
    print(t12)
    print(message12)
    print(t13)
    print(message13)
    print(t14)
    print(message14)
    print(t15)
    print(message15)
    print(t19)
    print(message19)
    print(t17)
    print(message17)
    print(t23)
    print(message23)
    print(t31)
    print(message31)
    print(t32)
    print(message32)
    '''

    

def octavia_test_cases(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips):
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])
    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    
    passed=failed=0
    
    t5,message5, t6,message6= octavia_test_case_5_6(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t5 == True:
        t5= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t5="Failed"
    print(t5)
    print(message5)

    if t6 == True:
        t6= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t6="Failed"
    print(t6)
    print(message6)

    '''
    
    t3, message3, t4,message4, t7,message7, t8,message8, t9,message9, t10,message10= octavia_test_case_3_4_7_8_9_10(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t3 == True:
        t3= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t3="Failed"
    print(t3)
    print(message3)
    if t4 == True:
        t4= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t4="Failed"
    print(t4)
    print(message4)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    print(t7)
    print(message7)
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"
    print(t8)
    print(message8)
    if t9 == True:
        t9= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t9="Failed"
    print(t9)
    print(message9)

    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    print(t10)
    print(message10)
    
    t12, message12= octavia_test_case_12(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t12 == True:
        t12= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t12="Failed"
    print(t12)
    print(message12)

    t25, message25= octavia_test_case_25(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t25 == True:
        t25= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t25="Failed"
    print(t25)
    print(message25)
    
    t26, message26= octavia_test_case_26(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t26 == True:
        t26= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t26="Failed"
    print(t26)
    print(message26)
    
    t27, message27= octavia_test_case_27(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t27 == True:
        t27= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t27="Failed"
    print(t27)
    print(message27)
    
    t28, message28= octavia_test_case_28(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t28 == True:
        t28= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t28="Failed"
    print(t28)
    print(message28)
    
    t29, message29= octavia_test_case_29(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t29 == True:
        t29= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t29="Failed"
    print(t29)
    print(message29)
    
    t30, message30= octavia_test_case_30(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t30 == True:
        t30= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t30="Failed"
    print(t30)
    print(message30)
    
    t31, message31= octavia_test_case_31(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t31 == True:
        t31= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t31="Failed"
    print(t31)
    print(message31)
    
    t32, message32= octavia_test_case_32(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t32 == True:
        t32= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t32="Failed"
    print(t32)
    print(message32)
    
    t33, message33= octavia_test_case_33(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t33 == True:
        t33= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t33="Failed"
    print(t33)
    print(message33)
    
    t34, message34= octavia_test_case_34(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, router_id, security_group_id, image_id)
    if t34 == True:
        t34= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t34="Failed"
    print(t34)
    print(message34)
    '''

def sriov_vflag_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #creating zones
    
    try:
        compute0 =  [key for key, val in baremetal_nodes_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_nodes_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        default_zone_id= get_availability_zones(nova_ep, token)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute0)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute1)
        nova0_id= create_availability_zones(nova_ep, token, "nova0")
        nova1_id= create_availability_zones(nova_ep, token, "nova1")
        add_host_to_zone(nova_ep, token, nova0_id, compute0)
        add_host_to_zone(nova_ep, token, nova1_id, compute1)
    except Exception as e:
        pass
    time.sleep(20)
    
    keypair_public_key= "" #search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private key file")
    command= "chmod 400 "+keyfile_name
    os.system(command )


    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))

    passed=failed=0
    vfs= get_vfs_count()
    print(vfs)
    interfaces= get_sriov_enabled_interfaces()
    print(interfaces)
    sriov_vflag_test_case_3(baremetal_nodes_ips)
    sriov_vflag_test_case_6(baremetal_nodes_ips)
    t7,message7, t9,message9= sriov_vflag_test_case_7_9(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    print(t7)
    print(message7)
    print(t9)
    print(message9)
    t10,message10= sriov_vflag_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    print(t10)
    print(message10)
    t11,message11= sriov_vflag_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    print(t11)
    print(message11)
    t12,message12= sriov_vflag_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    print(t12)
    print(message12)
    t13,message13= sriov_vflag_test_case_13(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    print(t13)
    print(message13)
    
    t14,message14= sriov_vflag_test_case_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    print(t14)
    print(message14)
    
    t15,message15= sriov_vflag_test_case_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id)
    print(t15)
    print(message15)

    t16,message16= sriov_vflag_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    print(t16)
    print(message16)
    t17,message17= sriov_vflag_test_case_17(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    print(t17)
    print(message17)
    
    '''
    t7,message7, t8,message8= (nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"    
    '''
def storage_test_cases(keystone_ep, nova_ep, neutron_ep, image_ep, cinder_ep, token, settings, baremetal_nodes_ips):
    #creating zones
        
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image( image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))

    passed=failed=0
   
    storage_cases_1(keystone_ep, nova_ep, neutron_ep, image_ep, cinder_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    #print(t7)
    #print(message7)
def hci_test_cases(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_nodes_ips):
     #creating zones
    
    try:
        compute0 =  [key for key, val in baremetal_nodes_ips.items() if "hci-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_nodes_ips.items() if "hci-1" in key]
        compute1= compute1[0]
        compute2 =  [key for key, val in baremetal_nodes_ips.items() if "hci-2" in key]
        compute2= compute2[0]
        default_zone_id= get_availability_zones(nova_ep, token)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute0)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute1)
        remove_host_from_zone(nova_ep, token, default_zone_id, compute2)
        nova0_id= create_availability_zones(nova_ep, token, "nova0")
        nova1_id= create_availability_zones(nova_ep, token, "nova1")
        #nova2_id= create_availability_zones(nova_ep, token, "nova2")
        add_host_to_zone(nova_ep, token, nova0_id, compute0)
        add_host_to_zone(nova_ep, token, nova1_id, compute1)
        add_host_to_zone(nova_ep, token, nova1_id, compute2)
        time.sleep(20)
    except Exception as e:
        print(e)
    
    
    keypair_public_key= "" #search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private key file")
    command= "chmod 400 "+keyfile_name
    os.system(command )


    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))

    passed=failed=0
    t3,message3= hci_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id, flavor_id)    
    if t3 == True:
        t3= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t3="Failed"
    
    t4,message4= hci_test_case_4(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id)
    if t4 == True:
        t4= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t4="Failed"
    
    t5,message5= hci_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id, flavor_id)
    if t5 == True:
        t5= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t5="Failed"
    t6,message6= hci_test_case_6(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id)
    if t5 == True:
        t6= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t6="Failed"
    
    t7,message7= hci_test_case_7(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id, flavor_id)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"

    t8,message8= hci_test_case_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id, flavor_id)
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"

    t9,message9= hci_test_case_9(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id, flavor_id)
    if t9 == True:
        t9= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t9="Failed"

    #Deleting zones
    try:
        remove_host_from_zone(nova_ep, token, nova0_id, compute0)
        remove_host_from_zone(nova_ep, token, nova1_id, compute1)
        remove_host_from_zone(nova_ep, token, nova1_id, compute2)
        add_host_to_zone(nova_ep, token, default_zone_id, compute0)
        add_host_to_zone(nova_ep, token, default_zone_id, compute1)
        add_host_to_zone(nova_ep, token, default_zone_id, compute2)
        delete_resource("{}/v2.1/os-aggregates/{}".format(nova_ep, nova0_id), token)
        delete_resource("{}/v2.1/os-aggregates/{}".format(nova_ep, nova1_id), token)
    except Exception as e:
        print(e)
        pass
    t10,message10= hci_test_case_10(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id, flavor_id)
    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    
    print("---------------------------")
    print("-------HCI Test Cases-------")
    print("---------------------------")
    print("Total Testcases {}".format(failed+passed))
    print("Testcases Passed {}".format(passed))
    print("Testcases Failed {}".format(failed))
    print("HCI test case 3 status: {} ".format(t3))
    print("HCI test case 4 status: {} ".format(t4))
    print("HCI test case 5 status: {} ".format(t5))
    print("HCI test case 6 status: {} ".format(t6))
    print("HCI test case 7 status: {} ".format(t7))
    print("HCI test case 8 status: {} ".format(t8))
    print("HCI test case 9 status: {} ".format(t9))
    print("HCI test case 10 status: {} ".format(t10))
 
    print("------------------------------")
    print("----------Description--------")
    print("------------------------------")
    print("HCI test case 3 status: {} ".format(t3))
    print("HCI message  {} \n".format(message3))
    print("------------------------------")
    print("HCI test case 4 status: {} ".format(t4))
    print("HCI message  {} \n".format(message4))
    print("------------------------------")
    print("HCI test case 5 status: {} ".format(t5))
    print("HCI message  {} \n".format(message5))
    print("------------------------------")
    print("HCI test case 6 status: {} ".format(t6))
    print("HCI message  {} \n".format(message6))
    print("------------------------------")
    print("HCI test case 7 status: {} ".format(t7))
    print("HCI message  {} \n".format(message7))
    print("------------------------------")
    print("HCI test case 8 status: {} ".format(t8))
    print("HCI message  {} \n".format(message8))
    print("------------------------------")
    print("HCI test case 8 status: {} ".format(t9))
    print("HCI message  {} \n".format(message9))
    print("------------------------------")
    print("HCI test case 10 status: {} ".format(t10))
    print("HCI message  {} \n".format(message10))
    print("------------------------------")

def barbican_test_cases(nova_ep, neutron_ep, image_ep, cinder_ep, barbican_ep, keystone_ep, token, settings, baremetal_nodes_ips):
     #creating zones
    keypair_public_key= "" #search_and_create_kaypair(nova_ep, token, settings["key_name"])
    keypair_key= search_keypair(nova_ep, token, settings["key_name"])
    keypair_private_key=""
    logging.info("searching ssh key")
    keyfile_name= os.path.expanduser(settings["key_file"])
    if(keypair_key != None):
        logging.info("deleting old ssh key")
        delete_resource("{}/v2.1/os-keypairs/{}".format(nova_ep, settings["key_name"]), token)

    keypair_private_key= create_keypair(nova_ep, token, settings["key_name"])
    logging.info("ssh key created")
    try:
        logging.info("deleting old private file")
        os.system("sudo rm "+keyfile_name)
    except OSError:
        pass
    logging.info("creating key file")
    keyfile = open(keyfile_name, "w")
    keyfile.write(keypair_private_key)
    keyfile.close()
    logging.info("setting permission to private key file")
    command= "chmod 400 "+keyfile_name
    os.system(command )


    #Search and create network
    network1_id = search_and_create_network(neutron_ep, token, settings["network1_name"], 1500, settings["network_provider_type"], False)  
    network2_id = search_and_create_network(neutron_ep, token, settings["network2_name"], 1500, settings["network_provider_type"], False)  
    #Search and create subnet
    subnet1_id= search_and_create_subnet(neutron_ep, token, settings["subnet1_name"], network1_id, settings["subnet1_cidr"]) 
    subnet2_id= search_and_create_subnet(neutron_ep, token, settings["subnet2_name"], network2_id, settings["subnet2_cidr"]) 
    router_id= search_router(neutron_ep, token, settings["router_name"])
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
        router_id= create_router(neutron_ep, token, settings["router_name"], public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet2_id)
        add_interface_to_router(neutron_ep, token, router_id, subnet1_id)
    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))

    passed=failed=0
    
    t3,message3= barbican_test_case_1(nova_ep, neutron_ep, image_ep, barbican_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network1_id, subnet1_id, security_group_id, image_id)
    print(t3)
    print(message3)



def main():
   
    #Parse Arguments
    try:
        arguments= parse_arguments()
    except Exception as e:
        logging.exception("error parsing arguments {}".format(e))

    #Validate Arguments
    logging.info("validating arguments")
    if not(arguments.feature == "numa" or  arguments.feature == "hugepages" or arguments.feature == "ovsdpdk" or arguments.feature == "sriov" or arguments.feature=="mtu9000" or arguments.feature=="dvr" or arguments.feature=="octavia" or arguments.feature=="sriov_vflag", arguments.feature=="hci", arguments.feature=="barbican"):
        logging.critical("Invalid Argument {}".format(arguments.feature))
        raise ValueError("Invalid Argument {}".format(arguments.feature))
    if arguments.deployment != "ceph":
        logging.critical("Invalid Argument {}".format(arguments.deployment))
        raise ValueError("Invalid Argument {}".format(arguments.deployment))

    #Read Settings File
    logging.info("reading settings from file")
    settings= read_settings(arguments.settings)

    #Read rc files
    logging.info("reading undercloud stackrc file")
    #undercloud_url, undercloud_username, undercloud_password= read_rc_file(arguments.undercloudrc)
    undercloud_ip, undercloud_username, undercloud_password= read_rc_file(arguments.undercloudrc)
    overcloud_ip, overcloud_username, overcloud_password= read_rc_file(arguments.overcloudrc)

    #Create Endpoints
    keystone_ep= "{}:5000".format(overcloud_ip)
    neutron_ep= "{}:9696".format(overcloud_ip)
    cinder_ep= "{}:8776".format(overcloud_ip)
    nova_ep= "{}:8774".format(overcloud_ip)
    image_ep= "{}:9292".format(overcloud_ip) 
    loadbal_ep= "{}:9876".format(overcloud_ip) 
    barbican_ep="{}:9311".format(overcloud_ip) 
    undercloud_keystone_ep= "{}:5000".format(undercloud_ip)
    undercloud_nova_ep= "{}:8774".format(undercloud_ip)

    #Get undercloud authentication Token
    undercloud_token= get_authentication_token(undercloud_keystone_ep, undercloud_username, undercloud_password)
    logging.info("Successfully authenticated with undercloud") if undercloud_token is not None else logging.error("Authentication with undercloud failed")
    
    #Get overcloud authentication token
    logging.info("auhenticating user")
    token= get_authentication_token(keystone_ep, overcloud_username,overcloud_password)

    #Get Ips of baremetal nodes
    baremetal_nodes_ips= get_baremeta_nodes_ip(undercloud_nova_ep, undercloud_token)
    logging.info("Successfully received baremetal nodes ip addresses")
    compoute0_dic = [key for key, val in baremetal_nodes_ips.items() if "compute1" in key]
    #get hist list
    hosts_list= get_compute_host_list(nova_ep, token)
    
    if arguments.feature=="hci":
        compute_node_search_pattern= "hci-"
    else:
        compute_node_search_pattern= "compute-"
    #update compute nodes names in baremetal nodes ip
    logging.info("updating compute nodes name in baremetal nodes ips")
    compute0= [i for i in hosts_list if (compute_node_search_pattern+"0") in i]
    compoute0_key = [key for key, val in baremetal_nodes_ips.items() if  (compute_node_search_pattern+"0") in key]
    baremetal_nodes_ips[compute0[0]] = baremetal_nodes_ips.pop(compoute0_key[0])
    
    compute1= [i for i in hosts_list if  (compute_node_search_pattern+"1") in i]
    compoute1_key = [key for key, val in baremetal_nodes_ips.items() if (compute_node_search_pattern+"1") in key]
    baremetal_nodes_ips[compute1[0]] = baremetal_nodes_ips.pop(compoute1_key[0])
    
    compute2= [i for i in hosts_list if  (compute_node_search_pattern+"2") in i]
    compoute2_key = [key for key, val in baremetal_nodes_ips.items() if (compute_node_search_pattern+"2") in key]
    baremetal_nodes_ips[compute2[0]] = baremetal_nodes_ips.pop(compoute2_key[0])

    #Creating default parameters

    
    #Run Test Cases
    if arguments.feature == "numa":
        numa_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "hugepages":
        hugepages_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "ovsdpdk":
        ovsdpdk_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "sriov":
        sriov_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "mtu9000":
        mtu9000_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "dvr":
        dvr_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips)
    if arguments.feature == "octavia":
        octavia_test_cases(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "sriov_vflag":
        #print("hello")
        sriov_vflag_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.deployment == "ceph":
        print("hello")
        #storage_test_cases(keystone_ep, nova_ep, neutron_ep, image_ep, cinder_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "hci":
        hci_test_cases(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "barbican":
        barbican_test_cases(nova_ep, neutron_ep, image_ep, cinder_ep, barbican_ep, keystone_ep, token, settings, baremetal_nodes_ips) 

if __name__ == "__main__":
    main()
