from openstack_functions import *
import logging
import paramiko
from hugepages import *
import os
from hugepages import*
import math

def wait_instance_boot(ip):
    retries=0
    while(1):
        response = os.system("ping -c 3 " + ip)
        if response == 0:
            logging.info ("Ping successfull!")
            break 
            return True
        logging.info("Waiting for server to boot")
        time.sleep(30)
        retries=retries+1
        if(retries==10):
            break
            return False

def parse_vcpus(output): 
    output= output.split('>')
    return output[1][0]

def ssh_into_node(host_ip, command):
    try:
        user_name = "heat-admin"
        logging.info("Trying to connect with node {}".format(host_ip))
        # ins_id = conn.get_server(server_name).id
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session = ssh_client.connect(host_ip, username="heat-admin", key_filename=os.path.expanduser("~/.ssh/id_rsa"))  # noqa
        logging.info("SSH Session is established")
        logging.info("Running command in a compute node")
        stdin, stdout, stderr = ssh_client.exec_command(command)
        logging.info("command {} successfully executed on compute node {}".format(command, host_ip))
        output= stdout.read().decode('ascii')
        return output
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        ssh_client.close()
        logging.info("Connection from client has been closed")  


def numa_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    logging.info("Test Case 3 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 10)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0, None)
        server_build_wait(nova_ep, token, [server_id])
        status= check_server_status(nova_ep, token, server_id)  
        if(status== "active"):
        #Get Server Host
            instance_name= get_server_instance_name(nova_ep, token, server_id)
            print("instance name is {}".format(instance_name))
            command= "sudo cat /etc/libvirt/qemu/{}.xml | grep vcpus".format(instance_name)
            output= ssh_into_node(compute0_ip, command)
            print("output is: {}".format(output))
            vcpus= parse_vcpus(output)
            if vcpus== "4":
                logging.info("Numa Test Case 3 Passed")
                message="numa testcase 3 passed, expected vcpu are 4 while current vcpus are {}".format(vcpus)
                isPassed= True
            else: 
                logging.error("Numa Test Case 3 Failed")
                message="numa testcase 3 failed, expected vcpu are 4 while current vcpus are {}".format(vcpus)
        else:
            logging.error("Server creation failed")
            logging.error("Numa Test Case 3 Failed")
            message="numa testcase 3 failed because server is in not created, its status is: {}".format(status)
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(10)
    except Exception as e:
        logging.error("Test Case 15 failed")
        message="numa testcase 3 failed/ error occured"
        logging.exception(e)
        pass
    return isPassed, message
    
def numa_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=""
    compute_node= settings["compute0_name"]
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_ids=[]
    cpu_cores= int(settings["compute0_cores"])
    instance_possible=  math.floor(cpu_cores/4)
    for instance in range (0, instance_possible):
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node )
        server_ids.append(server_id)
    server_build_wait(nova_ep, token, server_ids)


    if(check_server_status(nova_ep, token, server_ids[0])== "active" and check_server_status(nova_ep, token, server_ids[1])=="active" and check_server_status(nova_ep, token, server_ids[2])== "error"):
        isPassed= True
        logging.info("Numa testcase 6 passed")
    else:
        logging.info("Numa testcase 6 failed")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)

    return isPassed


def numa_test_case_6(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=""
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    try: 
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 20, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server_ids=[]
        cpu_cores=  80 #int(settings["compute0_cores"])
        instance_possible=  math.floor(cpu_cores/20)
        for instance in range (0, instance_possible):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0 )
            server_ids.append(server_id)
        server_build_wait(nova_ep, token, server_ids)
        flag=True
        count=0
        for i in range (0,instance_possible-1):
            status= check_server_status(nova_ep, token, server_ids[i])
            if(status != "active"):
                flag== False

        status= check_server_status(nova_ep, token, server_ids[instance_possible-1])
        if (status=="error" and flag==True):
            isPassed= True
            logging.info("Numa testcase 6 passed")
            message="testcase created valid number of instances"
        else:
            logging.info("Numa testcase 6 failed")
            message="testcase did not created valid number of instances"
        
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        for server_id in server_ids:   
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(20)
    except Exception as e:
        logging.error("Test Case 6 failed")
        message="numa testcase 6 failed/ error occured"
        logging.exception(e)
        pass
    return isPassed, message
def numa_test_case_7(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=""
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server_ids=[]
        for i in range (0,2):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(i), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
            server_ids.append(server_id)
        server_build_wait(nova_ep, token, server_ids) 
        
        instance_1_name= get_server_instance_name(nova_ep, token, server_ids[0])
        output1= ssh_into_node(compute0_ip, " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_1_name))
        output1= output1.split("'")
        output1= output1[1].split(",")
        instance_2_name= get_server_instance_name(nova_ep, token, server_ids[1])
        output2= ssh_into_node(compute0_ip, " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_2_name))
        output2= output2.split("'")
        output2= output2[1].split(",")
        logging.info("VCPU for instance 1 are: {}".format(output1))
        logging.info("VCPU for instance 2 are: {}".format(output2))
        validate = [i for i in output1 if i in output2]
        if not validate:
            logging.info("Numa Testcase 7 passed")
            isPassed= True
            message="Numa Testcase 7 passed, instances have not shared vcpus, \ninstance1 vcpus are {}\n instance2 vcpus are {}\n".format(output1, output2)

        else: 
            logging.error("Numa Testcase 7 failed")
            message="Numa Testcase 7 failed, instances have shared vcpus, \ninstance1 vcpus are {}\n instance2 vcpus are {}\n".format(output1, output2)
    
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[0]), token)
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[1]), token)
        time.sleep(10)
    except Exception as e:
        logging.error("Test Case 7 failed")
        message="numa testcase 7 failed/ error occured"
        logging.exception(e)
        pass
    return isPassed, message
    
def numa_test_case_8(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=""
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server_ids=[]
        for i in range (0,2):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(i), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
            server_ids.append(server_id)
        server_build_wait(nova_ep, token, server_ids) 
        status1= check_server_status(nova_ep, token, server_ids[0])
        status2= check_server_status(nova_ep, token, server_ids[1])
        if status1 == "active" and status2=="active":  
            instance_1_name= get_server_instance_name(nova_ep, token, server_ids[0])
            output1= ssh_into_node(compute0_ip, " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_1_name))
            output1= output1.split("'")
            output1= output1[1].split(",")

            instance_2_name= get_server_instance_name(nova_ep, token, server_ids[1])
            output2= ssh_into_node(compute0_ip, " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_2_name))
            output2= output2.split("'")
            output2= output2[1].split(",")
            logging.info("VCPU for instance 1 are: {}".format(output1))
            logging.info("VCPU for instance 2 are: {}".format(output2))
            output_1_even=output_1_odd=output_2_even=output_2_odd=0
            
            for num in output1: 
                if int(num) % 2 == 0: 
                    output_1_even += 1
                else: 
                    output_1_odd += 1
            for num in output2: 
                if int(num) % 2 == 0: 
                    output_2_even += 1
                else: 
                    output_2_odd += 1
            if(output_1_even ==0 or output_1_odd==0) and (output_2_even ==0 or output_2_odd==0):
                logging.info("Numa Testcase 8 passed")
                message="Numa Testcase 8 passed, instances have even or odd vcpus, \ninstance1 vcpus are {}\n instance2 vcpus are {}\n".format(output1, output2)

                isPassed= True
            else: 
                logging.error("Numa Testcase 8 failed")
                message="Numa Testcase 8 failed, instances have not all even or odd vcpus, \ninstance1 vcpus are {}\n instance2 vcpus are {}\n".format(output1, output2)

        else:
            logging.error("numa testcase8 failed because one or more server server creation failed")
            message= "numa testcase 8 failed because one or more server server creation failed, server 1 status is {}, server2 status is {}".format(status1, status2)
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting server")
        #delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[0]), token)
        #delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[1]), token)
        time.sleep(10)
    except Exception as e:
        logging.error("Test Case 8 failed")
        message="numa testcase 8 failed/ error occured"
        logging.exception(e)
        pass
    return isPassed, message
def numa_test_case_10(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=""
    try:   
        flavor_1_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_1_id, True)
        flavor_2_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_2", 4096, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_2_id, True)
        server_id= search_and_create_server(nova_ep, token, "testcase_server", image_id,settings["key_name"], flavor_2_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id]) 
        status= check_server_status(nova_ep, token, server_id)  
        if(status== "active"):
            response= resize_server(nova_ep,token, server_id, flavor_1_id)
            if response==(202):
                isPassed= True
                logging.info("Sccessfully Migrated")
                logging.info("Test Case 10 Passed")
                message="Test Case 10 Passed, server successfully resized, return code is: {}".format(response)
            else: 
                logging.info("Migration Failed")
                logging.error("Test Case 10 Failed")
                message="Test Case 10 failed, server failed to resiz, return code is: {}".format(response)

            logging.info("deleting flavors")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            time.sleep(10)
        else:
            logging.error("Test Case 10 Failed")
            message="Test Case 10 failed, server creation failed, its status is: {}".format(status)
    except Exception as e:
        logging.error("Test Case 10 failed")
        message="numa testcase 10 failed/ error occured"
        logging.exception(e)
        pass
    return isPassed, message
    
def numa_test_case_11(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False,
    message=""
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server_id= search_and_create_server(nova_ep, token, "testcase_server", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_id]) 
        
        status= check_server_status(nova_ep, token, server_id)  
        if(status== "active"):
            response= migrate_server(nova_ep,token, server_id)
            if response == 202:
                logging.info("Numa Testcase 11 passed")
                message="Numa Testcase 11 passed, server successfully migrated, return code is: {}".format(response)
                isPassed=True
            else:
                logging.error("Numa Testcase 11 failed")
                message="Numa Testcase 11 failed, server failed to migrated, return code is: {}".format(response)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            time.sleep(10)
        else:
                logging.error("Test Case 10 Failed")
                message="Test Case 10 failed, server creation failed, its status is: {}".format(status)
    except Exception as e:
        logging.error("Test Case 11 failed")
        message="numa testcase 11 failed/ error occured"
        logging.exception(e)
        pass
    return isPassed, message
def numa_test_case_12(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 28, 60)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id]) 
        status= check_server_status(nova_ep, token, server_id)  
        if(status== "active"):
            server_build_wait(nova_ep, token, [server_id])
            server_ip= get_server_ip(nova_ep, token, server_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            response = os.system("ping -c 3 " + server_floating_ip)
            if response == 0:
                isPassed= True
                logging.info ("Ping successfull!")
                logging.info("Test Case 12 Passed")
                message=" testcase 12 passed, instance numa server pinged successfully"

            else:
                logging.info ("Ping failed")
                logging.error("Test Case 12 Failed")
                message=" testcase 12 failed, instance numa can not be pinged"
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
            time.sleep(10)
        else:
                logging.error("Numa Test Case 12 Failed, server creation failed")
                message="Test Case 12 failed, server creation failed, its status is: {}".format(status)
    except Exception as e:
        logging.error("Test Case 12 failed")
        message="numa testcase 12 failed/ error occured"
        logging.exception(e)
        pass
    return isPassed, message
