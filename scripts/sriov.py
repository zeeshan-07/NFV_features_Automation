from openstack_functions import *
import logging
import paramiko
import os
from test_cases import *
import time
import math

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
def server_build_wait(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            print(status)
            if not (status == "active" or status=="error"):
                logging.info("Waiting for server/s to build")
                flag=1
                time.sleep(10)
        if flag==0:
            break
def ssh_conne(server1, server2, settings):
    try:
        command= "ping  -c 3 {}".format(server2)
        client= paramiko.SSHClient()
        paramiko.AutoAddPolicy()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server1, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
        logging.info("SSH Session is established")
        logging.info("Running command in a compute node")
        stdin, stdout, stderr = client.exec_command(command)
        logging.info("command {} successfully executed on compute node {}".format(command, server2))
        output= stdout.read().decode('ascii')
        error= stderr.read().decode('ascii')
        return output, error
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        client.close()
        logging.info("Connection from client has been closed")  

def parse_hugepage_size(huge_page_info, parameter):
    huge_page_info= huge_page_info.split('\n')
    for property in huge_page_info:
        line= property.split()
        if line[0] == parameter:
           return line[1]
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
def wait_instance_ssh(ip, settings):
    retries=0
    while(1):
        try:
            client= paramiko.SSHClient()
            paramiko.AutoAddPolicy()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
            break
        except:
            pass
            logging.info("Waiting for server to ssh")
            time.sleep(30)
        retries=retries+1
        if(retries==10):
            break

def sriov_test_cases_7_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 7 and 8 running")
    isPassed7=isPassed8= False
    message7=message8=flavor_id=port_id=port_ip=status=""    
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        flavor2_id= search_and_create_flavor(nova_ep, token, settings["flavor2"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        put_extra_specs_in_flavor(nova_ep, token, flavor2_id, False)
        port_id, port_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        logging.info("Port Ip is: {}  port id is {}".format(port_id, port_ip))
        server_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  port_id, "nova0", security_group_id)
        server_build_wait(nova_ep, token, [server_id])
        status= check_server_status(nova_ep, token, server_id)
        if status == "active":
            isPassed7=True
            message7="Instance created Successfully and its status is: {}".format(status)
        else:
            logging.error("Test case 7 failed")
            message7=message8="Instance Creation Failed its status is: {}".format(status)
    
    except Exception as e:
        logging.exception(e)
        message7="SRIOV test case 7 failed/ error occured: {}".format(status)
        pass
    print("status is: {}".format(status))
    if status=="active":
        try:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_ip, floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_ip, port_id)
            logging.info("Waiting for server to boot")
            logging.info("Floatinf Ip is: {}".format(flaoting_ip))
            wait_instance_boot(flaoting_ip)
            wait_instance_ssh(flaoting_ip, settings)
            result, error= ssh_conne(flaoting_ip, "8.8.8.8", settings)
            if error=="":
                isPassed8=True
                logging.info("Testcase 8 passed")
                message8="Successfully ssh into instance using keypair \n output is \n {}".format(result)
            else: 
                logging.error("Test Case 8 failed")
                message8="ssh into instance failed using keypair {}".format(status)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_id), token)
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep,floating_ip_id), token)
            time.sleep(2)
        except Exception as e:
            logging.exception(e)
            logging.error(e)
            message8="SRIOV test case 8 failed/ error occured: {}".format(status)
            pass
    return isPassed7, message7, isPassed8, message8
def sriov_test_cases_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 10 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    # Search and Create Flavor
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        time.sleep(5)
        port_2_id, port_2_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_2" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova0", security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 10 failed")
            logging.error("Instances creation failed")
            message="Both instances can not ping eachother on same compute node same network because one of the instance is failed"
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_2_ip, port_2_id)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.debug("Server 1 ip: {}".format(flaoting_1_ip))
            logging.debug("Server 2 ip: {}".format(flaoting_2_ip))
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            logging.info("ssh into server2")
           
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" and error2== "":
                isPassed=True
                logging.info("SRIOV Testcase 10 passed")
                message="Both instances successfully pinged eachother on same compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, flaoting_2_ip, result1, flaoting_2_ip, flaoting_1_ip, result2)
            else: 
                logging.error("SRIOV Test Case 10 failed")
                message="Both instances can not  ping eachother on same compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, floating_2_ip, result1, flaoting_2_ip, flaoting_1_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.error("Test Case 10 failed/ error occured")
        message="Both instances can not ping eachother on same compute node same network/ error occured"
        logging.exception(e)
        logging.error(e)
        pass
    return isPassed, message
    
def sriov_test_cases_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 11 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    # Search and Create Flavor
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        time.sleep(5)
        port_2_id, port_2_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_2" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova1", security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 11 failed")
            logging.error("Instances creation failed")
            message="Both instances can not ping eachother on different compute node same network, because one of the instance is failed"
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_2_ip, port_2_id)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.debug("Server 1 ip: {}".format(flaoting_1_ip))
            logging.debug("Server 2 ip: {}".format(flaoting_2_ip))
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            logging.info("ssh into server2")            
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" and error2== "":
                isPassed=True
                logging.info("Testcase 11 passed")
                message="Both instances successfully pinged eachother on different compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, flaoting_2_ip, result1, flaoting_2_ip, flaoting_1_ip, result2)
            else: 
                logging.error("Test Case 11 failed")
                message="Both instances can not ping eachother on different compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, flaoting_2_ip, result1, flaoting_2_ip, flaoting_1_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.error(e)
        logging.error("Test Case 11 failed")
        message="Both instances can not pinged eachother on different compute node same network/ error occured"
        logging.exception(e)
    pass   
    return isPassed, message   

def sriov_test_cases_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 12 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    try: 
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute0, "nova0")
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 12 failed")
            logging.error("Instances creation failed")
            message="legancy instance and sriov instances can not ping eachother on same compute node same network, because one of the instance is failed"
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
            server_2_port= get_ports(neutron_ep, token, network_id, server_2_ip)
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.info("Server 1 ip: {}".format(flaoting_1_ip))
            logging.info("Server 2 ip: {}".format(flaoting_2_ip))
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            logging.info("result 1 is: ".format(result1))
            logging.info("ssh into server2")  
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            print("result 1 is: ".format(result2))
            if error1=="" and error2== "":
                isPassed=True
                logging.info("Testcase 12 passed")
                message="legacy instance and srio instance successfully pinged eachother on same compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, flaoting_2_ip , result1, flaoting_2_ip, flaoting_1_ip, result2)
            else: 
                logging.error("Test Case 12 failed")
                message="legacy instance and srio instance can not ping eachother on same compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, flaoting_2_ip, result1, flaoting_2_ip, flaoting_1_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
            logging.error(e)
            logging.error("Test Case 12 failed")
            message12="Both instances failed to ping eachother on different compute node same network/ error occured"
            logging.exception(e)
            pass   
    return isPassed, message

def sriov_test_cases_13_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 13, 14 running")
    isPassed13=isPassed14= False
    message13=message14=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    #search and create server
    port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
    server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
    server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1, "nova1")
    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
    if  status1 == "error" or  status2 == "error":
        logging.error("Test Case 13 and 14  failed")
        logging.error("Instances creation failed")
        message13=message14="legancy instance and sriov instances can not ping eachother on same compute node same network, because one of the instance is failed"
    else:
        public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
        server_2_port= get_ports(neutron_ep, token, network_id, server_2_ip)
        flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
        flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
        logging.info("Waiting for server to boot")
        wait_instance_boot(flaoting_1_ip)
        wait_instance_boot(flaoting_2_ip)
        wait_instance_ssh(flaoting_1_ip, settings)
        wait_instance_ssh(flaoting_2_ip, settings)
        print("Server 1 ip: {}".format(flaoting_1_ip))
        print("Server 2 ip: {}".format(flaoting_2_ip))
        try:
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            print("result 1 is: ".format(result1))
            logging.info("ssh into server2")
           
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            print("result 1 is: ".format(result2))
            print("Error 1 is: ".format(error1))
            print("Error 2 is: ".format(error2))

            if error1 =="" and error2 == "":
                isPassed13=True     
                logging.info("Testcase 13 passed")
                message13="legacy instance and sriov instance successfully pinged eachother on same compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, floating_2_ip_id, result1, flaoting_2_ip, flaoting_1_ip, result2)
                
                client= paramiko.SSHClient()
                paramiko.AutoAddPolicy()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(flaoting_1_ip, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
                stdin, stdout, stderr = client.exec_command("netstat -rn |grep '0.0.0.0'")
                logging.info("command successfully executed on instance {}".format(flaoting_1_ip))
                gateway= stdout.read().decode('ascii')
                error= stderr.read().decode('ascii')
                print("error 3 is: "+error)
                #gateway= ssh_into_node(flaoting_1_ip, "route -n | grep '0.0.0.0'")
                print(gateway)
                print(type(gateway))
                #gateway= gateway.split['\n']
                #gateway= gateway[0]
                print(gateway)
                gateway= gateway.split['0.0.0.0']
                gateway= gateway[0]
                print(gateway)
                gateway= gateway.strip('0.0.0.0         ')
                logging.info("Gateway is: "+gateway)
            else: 
                logging.error("Test Case 13 failed Both instances can not pingeachother on different compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, floating_2_ip_id, result1, flaoting_2_ip, flaoting_1_ip, result2))
                message13="Both instances can not pingeachother on different compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, floating_2_ip_id, result1, flaoting_2_ip, flaoting_1_ip, result2)
        except Exception as e:
            logging.error("Test Case 13 failed/ error occured ".format(e))
            logging.exception(e)
            message13="Both instances can not ping eachother on different compute node same network/ error occured"
            logging.exception(e)
    
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
    logging.info("deleting port")
    time.sleep(10)
    delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
    logging.info("releasing ip")
    delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
    delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    time.sleep(2)
    
    return isPassed13, message13, isPassed14, message14

def sriov_test_cases_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 15 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    try:
            # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network2_id, security_group_id, compute1, "nova1")
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 15 failed")
            logging.error("Instances creation failed")
            message12="legancy instance and sriov instances can not ping eachother on different compute node same network, because one of the instance is failed"
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server_2_port= get_ports(neutron_ep, token, network2_id, server_2_ip)
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            logging.info("ssh into server2")
           
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" and error2== "":
                isPassed=True
                logging.info("Testcase 15 passed")
                message="legacy instance and SRIOV instance successfully pinged eachother on different compute node compute node different network  \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, server_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
            else: 
                logging.error("Test Case 15 failed")
                message="legacy instance and SRIOV instance can not ping eachother on different compute node compute node different network  \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, server_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.error("Test Case 15 failed")
        message="Both instances failed to ping eachother on different compute node same network/ error occured"
        logging.exception(e)
        pass
    return isPassed, message

def sriov_test_cases_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 16 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network2_id, security_group_id, compute0, "nova0")
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 16 failed")
            logging.error("Instances creation failed")
            message="legancy instance and sriov instances can not ping eachother on same compute node different network, because one of the instance is failed"
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server_2_port= get_ports(neutron_ep, token, network2_id, server_2_ip)
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            logging.info("ssh into server2") 
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            print("result 1 is: ".format(result2))
            if error1=="" and error2== "":
                isPassed=True
                logging.info("Testcase 16 passed")
                message="legacy instance and srio instance successfully pinged eachother on same compute node different  network  \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, server_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
            else: 
                logging.error("Test Case 16 failed")
                message="Both instances successfully pinged eachother on different compute node and different  network   \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, server_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
                logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.error("Test Case 16 failed")
        message="Both instances failed pinged eachother on different compute node same network/ error occured"
        logging.exception(e)
        pass
    return isPassed, message

def sriov_test_cases_17(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 17 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        time.sleep(5)
        port_2_id, port_2_ip= create_port(neutron_ep, token, network2_id, subnet2_id, "test_case_port_2" )

        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova0", security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 17 failed")
            logging.error("Instances creation failed")
            message12=" sriov instances can not ping eachother on same compute node different network, because one of the instance is failed"
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_2_ip, port_2_id)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            logging.info("ssh into server2")
           
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" and error2== "":
                isPassed=True
                logging.info("Testcase 17 passed")
                message="both sriov instance and sriov instance successfully pinged eachother on same compute node and different network   \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, port_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
            else: 
                logging.error("Test Case 17 failed")
                message="Both sriov instances successfully pinged eachother on same compute node and different network   \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, port_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.error("Test Case 17 failed")
        message="Both sriov instances failed to ping eachother on same compute node and different network/ error occured"
        logging.exception(e)
        pass      
    return isPassed, message

def sriov_test_cases_18(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 18 running")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    try: 
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        time.sleep(5)
        port_2_id, port_2_ip= create_port(neutron_ep, token, network2_id, subnet2_id, "test_case_port_2" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova1", security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 18 failed")
            logging.error("Instances creation failed")
            message12="legancy instance and sriov instances can not ping eachother on same compute node same network, because one of the instance is failed"
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_2_ip, port_2_id)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.info("ssh into server1")
            result1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            logging.info("ssh into server2")
           
            result2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" and error2== "":
                isPassed=True
                logging.info("Testcase 18 passed")
                message="Both sriov instances successfully pinged eachother on different compute node and different network   \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, port_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
            else: 
                logging.error("Test Case 18 failed")
                message="Both sriov instances can not ping eachother on different compute node and different network   \n result of instance {} ({}) ping to instance {} ({}) is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, port_1_ip, flaoting_2_ip, port_2_ip,  result1, flaoting_2_ip, flaoting_1_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("deleting port")
            time.sleep(10)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.error("Test Case 18 failed")
        message="Both instances successfully pinged eachother on different compute node and different network/ error occured"
        logging.exception(e)
        pass      
    return isPassed, message

def dvr_test_case_19(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 19 running")
    isPassed= False
    message=""
    server1_id=flavor_id=server_floating_ip_id=server2_floating_ip_id=""
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute2 =  [key for key, val in baremetal_node_ips.items() if "compute-2" in key]
    compute2= compute2[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 60)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if  status1 == "error":
            logging.error("Test Case 19 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            logging.info("live migrating server")
            response= live_migrate_server(nova_ep,token, server1_id, compute2)
            logging.info("migration status code is: {}".format(response))
            logging.info("waiting for migration")
            time.sleep(30)
            wait_instance_boot(server_floating_ip)
            new_host= get_server_host(nova_ep, token, server1_id)
            logging.info("new host is: "+new_host)
            if(response == 202 and new_host != compute1):
                response2 = os.system("ping -c 3 " + server_floating_ip)
                if response2 == 0:
                    isPassed= True
                    logging.info ("Ping successfull!")
                    logging.info("SRIOV test Case 19 Passed")
                    message="SRIOV testcase 19 passed, live migration of instance is successfull, status code is {}, old host {}, new host {} \n".format(response, compute1, new_host)
                else:
                    logging.error("SRIOV test Case 19 failed, ping failed after live migration")
                    message= "SRIOV test Case 19 failed, ping failed after live migration"
            else:
                logging.error("live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host)
        
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        time.sleep(10)
        logging.info("releasing floating ip")
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    except Exception as e:
        logging.exception("DVR test Case 31 failed/ error occured")
        message="DVR testcase 31 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    logging.info("DVR Test Case 31 finished")
    return isPassed, message

def dvr_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("HCI Test Case 32 running")
    isPassed= False
    message=""
    server1_id=flavor_id=server_floating_ip_id=server2_floating_ip_id=""
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 60)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if  status1 == "error":
            logging.error("Test Case 32 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            logging.info("cold migrating server")
            response=  perform_action_on_server(nova_ep,token, server1_id, "migrate")
            time.sleep(20)
            if response==202:
                print("confirming migrate")
                perform_action_on_server(nova_ep,token, server1_id, "confirmResize")

            logging.info("migration status code is: {}".format(response))
            logging.info("waiting for migration")
            wait_instance_boot(server_floating_ip)
            new_host= get_server_host(nova_ep, token, server1_id)
            logging.info("new host is: "+new_host)
            if(response == 202 and new_host != compute1):
                response2 = os.system("ping -c 3 " + server_floating_ip)
                if response2 == 0:
                    isPassed= True
                    logging.info ("Ping successfull!")
                    logging.info("DVR test Case 32 Passed")
                    message="DVR testcase 32 passed, cold migration of instance is successfull, status code is {}, old host {}, new host {} \n".format(response, compute1, new_host)
                else:
                    logging.error("DVR test Case 32 failed, ping failed after cold migration")
                    message= "DVR test Case 32 failed, ping failed after cold migration"
            else:
                logging.error("cold vmigration of instance failed, status code is {}, old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="cold migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host)
        
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        time.sleep(10)
        logging.info("releasing floating ip")
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
 
    except Exception as e:
        logging.exception("DVR test Case 32 failed/ error occured")
        message="DVR testcase 32 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)    
    logging.info("DVR Test Case 32 finished")
    return isPassed, message



