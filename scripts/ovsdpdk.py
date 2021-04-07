from openstack_functions import *
import logging
import paramiko
import os
import time
import math

def ssh_into_node(host_ip, command):
    try:
        user_name = "heat-admin"
        logging.info("Trying to connect with node {}".format(host_ip))
        # ins_id = conn.get_server(server_name).id
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session = ssh_client.connect(host_ip, username="heat-admin", key_filename=  os.path.expanduser("~/.ssh/id_rsa"))  # noqa
        logging.info("SSH Session is established")
        logging.info("Running command in a compute node")
        stdin, stdout, stderr = ssh_client.exec_command(command)
        logging.info("command {} successfully executed on compute node {}".format(command, host_ip))
        output= stdout.read().decode('ascii')
        error= stderr.read().decode('ascii')
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
def parse_hugepage_size(huge_page_info, parameter):
    huge_page_info= huge_page_info.split('\n')
    for property in huge_page_info:
        line= property.split()
        if line[0] == parameter:
           return line[1]
def wait_instance_ssh(ip, settings):
    retries=0
    ssh=False
    while(1):
        try:
            client= paramiko.SSHClient()
            paramiko.AutoAddPolicy()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            result= client.connect(ip, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
            print("rESULT IS : ".format(result))
            ssh=True
            break
        except Exception as e:  
            logging.info("Waiting for server to ssh")
            time.sleep(30)
        retries=retries+1
        if(retries==10):
            break
    return ssh
def ovsdpdk_test_cases_15(nova_ep, token, settings):
    isPassed= False
    message=""
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 6, 40)
        put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
        response= send_get_request("{}/v2.1/flavors/{}/os-extra_specs".format(nova_ep,flavor_id), token)
        logging.info("successfully received flavor list") if response.ok else response.raise_for_status() 
        response=response.json()
        if response["extra_specs"]["hw:mem_page_size"]== "large":
            logging.info("Hugepage size is {}".format(response["extra_specs"]["hw:mem_page_size"]))
            logging.info("OVSDPDK Test Case 15 passed")
            message="flavor has same hugepage size, hugepage size is '{}' and dpdk status is: {}".format(response["extra_specs"]["hw:mem_page_size"])
        else:
            logging.info("Hugepage size is not same")
            logging.info("OVSDPDK Testcase 15 failed")
            message="flavor have not correct specs, hugepage size is '{}' and dpdk status is: {}".format(response["extra_specs"]["hw:mem_page_size"])

        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    except Exception as e:
        logging.error("OVSDPDK Testcase 15 failed, error occured")
        logging.exception("e")
        message="OVSDPDK Testcase 15 failed, error occured"
    return isPassed, message

def ovsdpdk_test_cases_18(baremetal_nodes_ips):
    isPassed= False
    message=""
    total_bridges=bridges_up=0
    command1= "sudo ovs-vsctl show | grep Bridge"
    command2= "sudo ovs-vsctl show |grep 'is_connected: true'"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    message=" Testing bridges are up or not \n"
    try:
        for node in compute_nodes_ip:
            ssh_output= ssh_into_node(node, command1)
            message= message+ " compute node: {}, \n {} \n".format(node, ssh_output)
            ssh_output= ssh_output.split("\n")
            total_bridges= len(ssh_output)
        
        for node in compute_nodes_ip:
            ssh_output= ssh_into_node(node, command2)
            message= message+ " compute node: {}, \n {} \n".format(node, ssh_output)
            ssh_output= ssh_output.split("\n")
            bridges_up= len(ssh_output)-1
        if(bridges_up==total_bridges):
            logging.info("All bridges up")
            logging.info("Test Case 18 passed")
            isPassed= True
            message=message+"All bridges are up"
        else: 
            logging.info("All bridges are not up")
            logging.error("Test Case 18 failed")
    except Exception as e:
        logging.error("OVSDPDK Testcase 18 failed, error occured")
        logging.exception("e")
        message="OVSDPDK Testcase 18 failed, error occured"
    return isPassed, message
def ovsdpdk_test_cases_22(baremetal_nodes_ips):
    isPassed=False
    command= "grep Huge /proc/meminfo"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    flag=0
    for node in compute_nodes_ip:
        ssh_output= ssh_into_node(node, command)
        huge_page_total= parse_hugepage_size(ssh_output,"HugePages_Total:")
        huge_page_consumed= parse_hugepage_size(ssh_output,"HugePages_Free:")
        logging.info("Total HUGEPAGE of compute node {} are {} and consumed {}".format(node, huge_page_total, huge_page_consumed))
        if(int(huge_page_total)- int(huge_page_consumed)) != 4:
            flag=1
    if flag==0:
        isPassed= True
        logging.info("All compute nodes have consumed 3 hugepages")
        logging.info("Test Case 22 Passed")
    else:
        logging.error("4 hugepages are not consumed on all compute nodes")
        logging.error("Test Case 22 failed")
    return isPassed
def ssh_conne(server1, server2, settings):
    try:
        command= "ping -c 3 {}".format(server2)
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
def ovsdpdk_test_case_28(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    logging.info("OVS DPDK Test Case 28 running")
    isPassed= False
    message=""
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 6, 40)
        put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
        #search and create server
        server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id])
        status= check_server_status(nova_ep, token, server_id) 
        if status == "active":
            isPassed= True
            logging.info("Server created successfully")
            logging.info ("TestCase 28 Passed")
            message="Instance successfully created, with dpdk flavor, its state is: {}".format(status)
        else:
            logging.info("Server creation failed")  
            logging.error ("TestCase 28 failed")
            message="Instance creation failed with dpdk flavor, its state is: {}".format(status)
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(10)
    except Exception as e:
        logging.error("OVSDPDK Testcase 28 failed, error occured")
        logging.exception("e")
        message="OVSDPDK Testcase 28 failed, error occured"
    return isPassed, message

def ovsdpdk_test_case_36(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):    
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    logging.info("OVS DPDK Test Case 36 running")
    isPassed= False
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 28, 20)
    put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
    #search and create server
    server_ids=[]
    cpu_cores= int(settings["compute0_cores"])
    instance_possible=  math.floor(cpu_cores/28)
    i=0
    for instance in range (0, instance_possible+1):
        try:
            server_id= search_and_create_server(nova_ep, token, "test_case_Server{}".format(i), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
            server_ids.append(server_id)
            i=i+1
        except:
            pass
    server_build_wait(nova_ep, token, server_ids)

    flag=True
    for i in range (0,instance_possible-1):
        status= check_server_status(nova_ep, token, server_ids[i])
        if(status != "active"):
            flag== False

    status= check_server_status(nova_ep, token, server_ids[instance_possible])
    if (status=="error" and flag==True):
        isPassed= True
        logging.info("OVSDPDK testcase 36 passed")
    else:
        logging.info("OVSDPDK testcase 36 failed")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    for server_id in server_ids:   
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(20)

    return isPassed, ""
def ovsdpdk_test_cases_43(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):    
    isPassed=False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 20)
        put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
        server_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_id])
        status= check_server_status(nova_ep, token, server_id)
        if status=="active":
            server_ip= get_server_ip(nova_ep, token, server_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            floating_ip, floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(floating_ip)
            response = os.system("ping -c 3 " + floating_ip)
            #and then check the response...
            if response == 0:
                logging.info ("Ping successfull!")
                message="Instance successfully pinged, response is {}".format(response)
            else:
                logging.info("Ping failed")
                message="Instance not pinged, response is {}".format(response)
                return isPassed, message
            #Now restart ovs switch
            command1= "sudo service ovs-vswitchd restart"
            output= ssh_into_node(compute0_ip, "command")
            message= message+"\n ovs switch restarted {} \n".format(output)
            time.sleep(20)
            if response == 0:
                isPassed= True
                logging.info ("Ping successfull!")
                logging.info("Test Case 43 Passed")
                message= message+"ping successful, instance is working, {}".format(response)
            else:
                logging.info ("Ping failed")
                logging.error("Test Case 43 Failed")
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip_id), token)
            
        else: 
            logging.error("OVSDPDK Testcase 43 failed, server creation failed")
            message="OVSDPDK Testcase 43 failed, server creation failed"
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            time.sleep(20)
    except Exception as e:
        logging.error("OVSDPDK Testcase 43 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 43 failed, error occured"
    return isPassed, message

def ovsdpdk_test_case_46(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):    
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute0= compute0[0]
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 20)
        put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0 )
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "active" and status2 == "active":
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network_id, server_1_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_1_floating_ip, server_1_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_1_floating_ip)
            wait_instance_ssh(server_1_floating_ip, settings)
            result, error= ssh_conne(server_1_floating_ip, server_2_ip, settings)
            if error=="":
                isPassed= True
                logging.info("Test Case 46 Passed")
                message= "testcase passed when 1 server has floating ip and it pinged other server with private ip \n ping result is: \n{}\n".format(result)
            else: 
                logging.error("Test Case 46 failed")
                message= "testcase failed when 1 server has floating ip and it pinged other server with private ip \n ping result is: \n{}\n".format(result)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip), token)
            time.sleep(20)
        else:
            message="testcase failed because one or more server creation is failed"
            logging.error("testcase failed because one or more server creation is failed")
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
           
    except Exception as e:
        logging.error("OVSDPDK Testcase 46 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 46 failed, error occured"
    return isPassed, message
def ovsdpdk_test_case_47(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):    
    isPassed= False
    # Search and Create Flavor
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute0= compute0[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 20)
        put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "active" and status2 == "active":
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network_id, server_1_ip)
            server_2_port= get_ports(neutron_ep, token, network_id, server_2_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_1_floating_ip, server_1_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            server_2_floating_ip, server_2_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_1_floating_ip)
            wait_instance_ssh(server_1_floating_ip, settings)
            wait_instance_ssh(server_2_floating_ip, settings)
            result1, error1= ssh_conne(server_1_floating_ip, server_2_floating_ip, settings)
            result2, error2= ssh_conne(server_2_floating_ip, server_1_floating_ip, settings)
            if error1=="" and error2== "":
                isPassed= True
                logging.info("Test Case 47 passed")
                message= "Test Case 47 Passed, both instances on same network and host pinged eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
            else: 
                logging.error("Test Case 47 failed")
                message= "Test Case 47 failed, both instances on same network and host can not ping eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_2_floating_ip), token)
            time.sleep(20)
        else:
                message="testcase failed because one or more server creation is failed"
                logging.error("testcase failed because one or more server creation is failed")
                logging.info("deleting flavor")
                delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
                logging.info("deleting all servers")
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
    except Exception as e:
        logging.error("OVSDPDK Testcase 47 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 47 failed, error occured"
    return isPassed, message
def ovsdpdk_test_case_48(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):    
    isPassed= False
    # Search and Create Flavor
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-2" in key]
    compute0= compute0[0]
    compute1=  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 20)
        put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0 )
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "active" and status2 == "active":
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network_id, server_1_ip)
            server_2_port= get_ports(neutron_ep, token, network_id, server_2_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_1_floating_ip, server_1_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            server_2_floating_ip, server_2_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_2_ip, server_2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_1_floating_ip)
            wait_instance_ssh(server_1_floating_ip, settings)
            wait_instance_ssh(server_2_floating_ip, settings)
            result1, error1= ssh_conne(server_1_floating_ip, server_2_floating_ip, settings)
            result2, error2= ssh_conne(server_2_floating_ip, server_1_floating_ip, settings)
            if error1=="" and error2== "":
                isPassed= True
                logging.info("testcase 48 passed")
                message= "Test Case 48 Passed, both instances on same network and different host pinged eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
            else: 
                logging.error("Test Case 48 failed")
                message= "Test Case 48 failed, both instances on same network and different host can not ping eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_2_floating_ip), token)
            time.sleep(20)
        else:
            message="testcase failed because one or more server creation is failed"
            logging.error("testcase failed because one or more server creation is failed")
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
    except Exception as e:
        logging.error("OVSDPDK Testcase 48 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 48 failed, error occured"
    return isPassed, message
