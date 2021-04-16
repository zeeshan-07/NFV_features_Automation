from openstack_functions import *
import logging
import paramiko
from hugepages import *
import os
from numa import *
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
        ssh_session = ssh_client.connect(host_ip, username="heat-admin",key_filename=os.path.expanduser("~/.ssh/id_rsa"))  # noqa
        logging.info("SSH Session is established")
        logging.info("Running command in a compute node")
        stdin, stdout, stderr = ssh_client.exec_command(command)
        logging.info("command {} successfully executed on compute node {}".format(command, host_ip))
        output= stdout.read().decode('ascii')
        error= stderr.read().decode('ascii')

        return output, error
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
        command= "ping  -c 3 -s 8972 -M do {}".format(server2)
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
    result=""
    retries=0
    ssh=False
    while(1):
        try:
            client= paramiko.SSHClient()
            paramiko.AutoAddPolicy()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print("ip to ssh {}".format(ip))
            result= client.connect(ip, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
            print(result)
            ssh=True
            break
        except:    
            print(result)
            logging.info("Waiting for server to ssh")
            time.sleep(30)

        retries=retries+1
        if(retries==10):
            break
    return ssh
        
def mtu9000_test_case_6(baremetal_nodes_ips):
    logging.info("Starting MTU9000 testcase 6")
    isPassed= False
    message=""
    try: 
        storage_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "storage" in key]

        command= "ping -c 3 -s 8972 -M do {}".format(storage_nodes_ip[1])
        output1, error1= ssh_into_node(storage_nodes_ip[0], command)
        print(output1)
        output2=""
        error2="a"
        if(len(storage_nodes_ip)==3):
            command= "ping -c 3 -s 8972 -M do {}".format(storage_nodes_ip[2])
            output2, error2= ssh_into_node(storage_nodes_ip[0], command)
            storage_nodes_ip[2]=""
        if error1 =="" and  error2=="":
            logging.info("MTU9000 Testcase 6 Passed")
            isPassed= True
            message= "Storage node successfully pinged other two storage nodes with mtu size 8972 \n Ping Results are: \n ping to storage node: {} \n {}\n \n ping to storage node: {}\n {}\n".format(storage_nodes_ip[1], output1, storage_nodes_ip[2], output2)
        else: 
            logging.error("MTU 9000 Test Case 6 failed")
            message= "Storage node can not ping other two storage nodes with mtu size 8972\n Ping Results are: \n ping to storage node: {} \n {}\n \n ping to storage node: {}\n {}\n".format(storage_nodes_ip[1], error1, storage_nodes_ip[2], error2)
    except Exception as e:
        logging.error("MTU 9000 Test Case 6 failed")
        logging.info("Storage node can not ping other two storage nodes with mtu size 8972 /error occured")
        logging.exception(e)
        
    logging.info("Mtu9000 Test Case 6 Finished")
    return isPassed, message
def mtu9000_test_case_7(baremetal_nodes_ips):
    logging.info("Starting MTU9000 testcase 7")
    isPassed= False
    message=""
    try: 
        controller_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "controller" in key]
        command= "ping -c 3 -s 8972 -M do {}".format(controller_nodes_ip[1])
        output1, error1= ssh_into_node(controller_nodes_ip[0], command)
        command= "ping -c 3 -s 8972 -M do {}".format(controller_nodes_ip[2])
        output2, error2= ssh_into_node(controller_nodes_ip[0], command)
        if error1 =="" and  error2=="":
            logging.info("MTU9000 Testcase 7 Passed")
            isPassed= True
            message= "Controller node successfully pinged other two controller nodes with mtu size 8972 \n Ping Results are: \n ping to storage node: {} \n {}\n \n ping to storage node: {}\n {}\n".format(controller_nodes_ip[1], output1, controller_nodes_ip[2], output2)
        else: 
            logging.error("MTU 9000 Test Case 7 failed")
            message= "Controller node can not ping other two controller nodes with mtu size 8972\n Ping Results are: \n ping to storage node: {} \n {}\n \n ping to storage node: {}\n {}\n".format(controller_nodes_ip[1], error1, controller_nodes_ip[2], error2)
    except Exception as e:
        logging.error("MTU 9000 Test Case 7 failed")
        logging.info("Controller node can not ping other two controller nodes with mtu size 8972 /error occured")
        logging.exception(e)
        
    logging.info("Mtu9000 Test Case 8 Finished")
    return isPassed, message

def mtu9000_test_case_8(baremetal_nodes_ips):
    logging.info("Starting MTU9000 testcase 8")
    isPassed= False
    message=""
    try: 
        compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
        command= "ping -c 3 -s 8972 -M do {}".format(compute_nodes_ip[1])
        output1, error1= ssh_into_node(compute_nodes_ip[0], command)
        command= "ping -c 3 -s 8972 -M do {}".format(compute_nodes_ip[2])
        output2, error2= ssh_into_node(compute_nodes_ip[0], command)
        if error1 =="" and  error2=="":
            logging.info("MTU9000 Testcase 8 Passed")
            isPassed= True
            message= "Compute node successfully pinged other two compute nodes with mtu size 8972 \n Ping Results are: \n ping to storage node: {} \n {}\n \n ping to storage node: {}\n {}\n".format(compute_nodes_ip[1], output1, compute_nodes_ip[2], output2)
        else: 
            logging.error("MTU 9000 Test Case 8 failed")
            message= "Compute node can not ping other two compute nodes with mtu size 8972\n Ping Results are: \n ping to storage node: {} \n {}\n \n ping to storage node: {}\n {}\n".format(compute_nodes_ip[1], error1, compute_nodes_ip[2], error2)
    except Exception as e:
        logging.error("MTU 9000 Test Case 8 failed")
        logging.info("Compute node can not ping other two compute nodes with mtu size 8972 /error occured")
        logging.exception(e)
        
    logging.info("Mtu9000 Test Case 8 Finished")
    return isPassed, message
def mtu9000_test_case_9(neutron_ep, token, network_id):
    logging.info("Starting MTU9000 testcase 9")
    isPassed= False
    message=""
    try: 
        network= get_network_detail(neutron_ep, token, network_id)
        if(network["network"]["mtu"]==9000):
            logging.info("MTU9000 Testcase 9 Passed")
            isPassed= True
            message= "Network has correct mtu size, mtu size is: {}".format(network["network"]["mtu"])
        else: 
            logging.error("MTU 9000 Test Case 9 failed")
            message= "Network has correct mtu size, mtu size is: {} ".format(network["network"]["mtu"])
    except Exception as e:
        logging.error("MTU 9000 Test Case 9 failed")
        logging.error("Network mtu verification testcase failed/ error occured")
        message="Network mtu verification testcase failed/ error occured"
        logging.exception(e) 
    logging.info("Mtu9000 Test Case 9 Finished")
    return isPassed, message


def mtu9000_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("MTU9000 Test Case 10")
    isPassed= False
    message=""
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    #search and create server
    try:
        server_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id])
        status= check_server_status(nova_ep, token, server_id)
        if  status == "active":
            logging.info("MTU9000 Testcase 10 Passed")
            isPassed= True
            message= "instance successfully created on network with mtu size 9000. instance state is: {}".format(status)
        else: 
            logging.error("MTU 9000 Test Case 10 failed")
            message= "instance creation failed on network with mtu size 9000. instance state is: {}".format(status)
    except Exception as e:
        logging.error("MTU 9000 Test Case 10 failed/ error occured")
        logging.exception(e)
        pass
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)    
    return isPassed, message
def mtu9000_test_case_11(neutron_ep, token, router_id, settings):
    logging.info("Starting MTU9000 testcase 11")
    isPassed= False
    message=""
    try: 
        router_id= search_router(neutron_ep, token, settings["router_name"])
        if router_id is not None:
            logging.info("MTU9000 Testcase 11 Passed")
            isPassed= True
            message= "Router successfully created, id is {}: ".format(router_id)
        else: 
            logging.error("MTU 9000 Test Case 11 failed")
            message= "router does not exist"
    except Exception as e:
        logging.error("MTU 9000 Test Case 11 failed")
        logging.error("router verification failed/ error occured")
        message="router verification failed/ error occured"
        logging.exception(e) 
    logging.info("Mtu9000 Test Case 11 Finished")

    return isPassed, message

def mtu9000_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("MTU9000 Test Case 12")
    isPassed= False
    message=""
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
    #search and create server
    try:
        server_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id])
        status= check_server_status(nova_ep, token, server_id)
        if  status == "active":
            server_ip= get_server_ip(nova_ep, token, server_id, settings["network1_name"])
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_ip, floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_ip)
            ssh= wait_instance_ssh(flaoting_ip, settings)
            print("ssh is: /{}/".format(ssh))
            if ssh== True:
                logging.info("MTU9000 Testcase 12 Passed")
                isPassed= True
                message= "instance successfully created on network with mtu size 9000. instance floating ip is: {} and successfully ssh".format(flaoting_ip)
            else: 
                logging.error("MTU9000 Testcase 12 failed")
                message= "instance successfully created on network with mtu size 9000. Can not SSH it,instance floating ip is:  {}".format(flaoting_ip)
        else: 
            logging.error("MTU 9000 Test Case 12 failed")
            message= "instance creation failed on network with mtu size 9000. instance state is: {}".format(status)
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(20)
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip_id), token)
          
    except Exception as e:
        logging.error("MTU 9000 Test Case 12 failed/ error occured")
        logging.exception(e)
        pass   
    return isPassed, message
def mtu9000_test_case_13(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("MTU9000 Test Case 13")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
    #search and create server
    try:
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network_id, security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id, network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "active" and status2 == "active":
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network_id, server_1_ip)
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
            server_2_port= get_ports(neutron_ep, token, network_id, server_2_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            ssh= wait_instance_ssh(flaoting_1_ip, settings)
            ssh= wait_instance_ssh(flaoting_2_ip, settings)
            output1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            output2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" or error2=="" :
                logging.info("MTU9000 Testcase 13 Passed")
                isPassed= True
                message= "both instances successfully pinged other other on mtu size 8972, on same compute node, same network \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
            else: 
                logging.error("MTU 9000 Test Case 13 failed")
                message="both instances can not ping other other on mtu size 8972, on same compute node, same network \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
        else: 
            logging.error("MTU 9000 Test Case 13 failed")
            message= "instance creation failed on network with mtu size 9000. instance 1 state is: {}, instance 2 state is: {}".format(status1, status2 )
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        time.sleep(20)
        logging.info("release floating ip")
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            
    except Exception as e:
            logging.error("MTU 9000 Test Case 13 failed/ error occured")
            logging.exception(e)
            print(e) 
    return isPassed, message

def mtu9000_test_case_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("MTU9000 Test Case 14")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
    #search and create server
    try:
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network_id, security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id, network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "active" and status2 == "active":
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network_id, server_1_ip)
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
            server_2_port= get_ports(neutron_ep, token, network_id, server_2_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            print("I ip: {}".format(flaoting_1_ip))
            ssh= wait_instance_ssh(flaoting_1_ip, settings)
            print("2 ip: {}".format(flaoting_2_ip))
            ssh= wait_instance_ssh(flaoting_2_ip, settings)
            output1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            output2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" or error2=="" :
                logging.info("MTU9000 Testcase 14 Passed")
                isPassed= True
                message= "both instances successfully pinged other other on mtu size 8972, on same network, different compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
            else: 
                logging.error("MTU 9000 Test Case 14 failed")
                message="both instances can not ping other other on mtu size 8972, on same network, different compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
        else: 
            logging.error("MTU 9000 Test Case 14 failed")
            message= "instance creation failed on network with mtu size 9000. instance 1 state is: {}, instance 2 state is: {}".format(status1, status2 )
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        time.sleep(20)
        logging.info("release floating ip")
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
        time.sleep(20)    
    except Exception as e:
        logging.error("MTU 9000 Test Case 14 failed/ error occured")            
        logging.exception(e)
        print(e) 
    return isPassed, message

def mtu9000_test_case_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("MTU9000 Test Case 15")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
    #search and create server
    try:
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network1_id, security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id, network2_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "active" and status2 == "active":
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network1_id, server_1_ip)
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server_2_port= get_ports(neutron_ep, token, network2_id, server_2_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            ssh= wait_instance_ssh(flaoting_1_ip, settings)
            ssh= wait_instance_ssh(flaoting_2_ip, settings)
            output1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            output2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" or error2=="" :
                logging.info("MTU9000 Testcase 15 Passed")
                isPassed= True
                message= "both instances successfully pinged other other on mtu size 8972, on different network, different compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
            else: 
                logging.error("MTU 9000 Test Case 15 failed")
                message="both instances can not ping other other on mtu size 8972, on different network, different compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
        else: 
            logging.error("MTU 9000 Test Case 15 failed")
            message= "instance creation failed on network with mtu size 9000. instance 1 state is: {}, instance 2 state is: {}".format(status1, status2 ) 
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        time.sleep(20)
        logging.info("release floating ip")
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
          
    except Exception as e:
            logging.error("MTU 9000 Test Case 15 failed/ error occured")
            logging.exception(e)
            print(e)   
    return isPassed, message
def mtu9000_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("MTU9000 Test Case 16")
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
    #search and create server
    try:
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network1_id, security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id, network2_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "active" and status2 == "active":
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network1_id, server_1_ip)
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server_2_port= get_ports(neutron_ep, token, network2_id, server_2_ip)
            public_network_id= search_network(neutron_ep, token, settings["external_network_name"])
            public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            ssh= wait_instance_ssh(flaoting_1_ip, settings)
            ssh= wait_instance_ssh(flaoting_2_ip, settings)
            output1, error1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            output2, error2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            if error1=="" or error2=="" :
                logging.info("MTU9000 Testcase 16 Passed")
                isPassed= True
                message= "both instances successfully pinged other other on mtu size 8972, on different network, same compute nodes \n Ping Results are: \n ping to  instance2 {} ({}) from instance 1 {} ({}) \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, server_1_ip, flaoting_1_ip, server_2_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
            else: 
                logging.error("MTU 9000 Test Case 16 failed")
                message="both instances can not ping other other on mtu size 8972, on different network, same compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
        else: 
            logging.error("MTU 9000 Test Case 16 failed")
            message= "instance creation failed on network with mtu size 9000. instance 1 state is: {}, instance 2 state is: {}".format(status1, status2 )
    
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        time.sleep(20)
        logging.info("release floating ip")
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
        
    except Exception as e:
            logging.error("MTU 9000 Test Case 16 failed/ error occured")
            logging.exception(e) 
            message="MTU 9000 Test Case 16 failed/ error occured" 

    return isPassed, message

    