from openstack_functions import *
import subprocess as sb
import logging
import paramiko
import os
import time
import math
import subprocess


def check_service_status(host_ip, command):
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
        output= stdout.readlines()
        error= stderr.readlines()
        return str(output), str(error)
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        ssh_client.close()
        logging.info("Connection from client has been closed") 

def parse_hugepage_size(huge_page_info, parameter):
    huge_page_info= huge_page_info.split('\n')
    for property in huge_page_info:
        line= property.split()
        if line[0] == parameter:
           return line[1]
def ovsdpdk_test_case_9(baremetal_nodes_ips, settings):
    logging.info("OVSDPDK testcase 9 starting")
    message=""
    isPassed=False
    command= "sudo cat /var/lib/os-net-config/dpdk_mapping.yaml"
    message= "DPDK ports are: "
    error=0
    try:
        compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
        for node in compute_nodes_ip:
            ports= ssh_into_node(node, command)
            ports=ports[0]
            print(ports)
            total_ports= ports.count("driver:")
            logging.info("Ports assigned to OVS DPDK  compute node {}, are {}".format(node, total_ports))
            message= message+ " node {}, total ports are {}, expected ports {} \n output received is: {} \n".format(node, total_ports, settings["ovsdpdk_ports"], ports)
            if total_ports != settings["ovsdpdk_ports"]:
               # message= message+ "Compute node {} do not have correct ports, expected {}, received {}".format(node, settings["ovsdpdk_ports"], total_ports)
                error=1
        if(error==1):
            logging.error("ovsdpdk testcase 9 failed, all compute nodes do not have correct ports ")
            message= "ovsdpdk testcase 9 failed, all compute nodes do not have correct ports \n"+ message    
        else:
            isPassed= True
            logging.info("ovsdpdk testcase 9 passed, all compute nodes have correct ports ")
            message= "ovsdpdk testcase 9 passed, all compute nodes have correct ports \n"+message
            logging.info("OVSDPDK Testcase 9 Passed")
    except Exception as e:
        logging.error("OVSDPDK Test case 9 failed/ error occured")
        message= "OVSDPDK Test case 9 failed/ error occured"
        logging.exception(e)
    logging.info("OVSDPDK testcase 9 finished")
    return isPassed, message
def ovsdpdk_test_case_11(baremetal_nodes_ips, settings):
    logging.info("OVSDPDK testcase 11 starting")
    message=""
    isPassed=False
    command= "sudo ovs-ofctl show br-tenant"  
    message= "DPDK active ports are: "
    error=0
    try:
        compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
        for node in compute_nodes_ip:
            ports= ssh_into_node(node, command)
            ports= ports[0]
            print(ports)
            total_ports= ports.count("dpdk")
            logging.info("Active OVS DPDK ports on compute node {}, are {}".format(node, total_ports))
            message= message+ " node {}, total active ports are {} expected ports {} \n output received is: {} \n".format(node, total_ports, settings["ovsdpdk_ports"], ports)
            if total_ports != settings["ovsdpdk_ports"]:
               # message= message+ "Compute node {} do not have correct ports, expected {}, received {}".format(node, settings["ovsdpdk_ports"], total_ports)
                error=1
        if(error==1):
            logging.error("ovsdpdk testcase 11 failed, all compute nodes do not have active dpdk ports ")
            message= "ovsdpdk testcase 11 failed, all compute nodes do not have correct active dpdk ports \n"+ message    
        else:
            isPassed= True
            logging.info("ovsdpdk testcase 11 passed, all compute nodes have active dpdk ports ")
            message= "ovsdpdk testcase 11 passed, all compute nodes have active dpdk ports \n"+message
            logging.info("OVSDPDK Testcase 11 Passed")
    except Exception as e:
        logging.error("OVSDPDK Test case 11 failed/ error occured")
        logging.exception(e)
        message= "OVSDPDK Test case 11 failed/ error occured"
    logging.info("OVSDPDK testcase 11 Finished")
    return isPassed, message

def ovsdpdk_test_case_15(nova_ep, token, settings):
    isPassed= False
    message=flavor_id=""
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "ovsdpdk_flavor", 4096, 6, 40)
        put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id)
        response= send_get_request("{}/v2.1/flavors/{}/os-extra_specs".format(nova_ep,flavor_id), token)
        logging.info("successfully received flavor list") if response.ok else response.raise_for_status() 
        response=response.json()
        if response["extra_specs"]["hw:mem_page_size"]== "large":
            logging.info("Hugepage size is {}".format(response["extra_specs"]["hw:mem_page_size"]))
            logging.info("OVSDPDK Test Case 15 passed")
            message="ovsdpdk testcase 15 passed, flavor has same hugepage size, hugepage size is {} ".format(response["extra_specs"]["hw:mem_page_size"])
        else:
            logging.info("Hugepage size is not same")
            logging.info("OVSDPDK Testcase 15 failed")
            message="ovsdpdk testcase 15 failed, flavor have not correct specs, hugepage size is {} ".format(response["extra_specs"]["hw:mem_page_size"])
        if(flavor_id !=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)    
    except Exception as e:
        logging.error("OVSDPDK Testcase 15 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 15 failed, error occured"
        if(flavor_id !=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token) 
        
    return isPassed, message
def ovsdpdk_test_case_16():
    logging.info("OVSDPDK testcase 16 starting")
    message=""
    isPassed=False
    command= "timeout 2 systemctl status tripleo_neutron_ovs_agent.service"
    try:

        response= sb.Popen(command, shell=True, stdout=sb.PIPE, stderr=sb.PIPE)
        (stdout,stderr)=  response.communicate()
            
        if("active (running)" in str(stdout)):
            isPassed= True
            logging.info("ovsdpdk testcase 16 passed, neutron service is working fine with ovsdpdk output is: {}".format(stdout))
            message= "ovsdpdk testcase 16 passed, neutron service is working fine with ovsdpdk, output is: {}".format(stdout)
            logging.info("OVSDPDK Testcase 16 Passed")
        else:
            logging.error("ovsdpdk testcase 16 failed,  neutron service is not working fine with ovsdpdk output is: {}".format(str(stderr)))
            message= "ovsdpdk testcase 16 failed,  neutron service is not working fine with ovsdpdk output is: {}".format(str(stderr))    
    except Exception as e:
        logging.error("OVSDPDK Test case 16 failed/ error occured")
        logging.exception(e)
        message= "OVSDPDK Test case 16 failed/ error occured"
    logging.info("OVSDPDK testcase 16 finished")
    return isPassed, message

def ovsdpdk_test_case_17(baremetal_nodes_ips, settings):
    logging.info("OVSDPDK testcase 17 starting")
    message=""
    isPassed=False
    command= "service ovs-vswitchd status |grep 'active (running)'"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    message= "ovs-vswitchd service status is: "
    error=0
    try:
        for node in compute_nodes_ip:
            stdout, stderr= check_service_status(node, command)
            logging.info(" ovs-vswitchd status on compute node {} , is {}\n".format(node, stdout))
            message= message+ " node {}, ovs-vswitchd status is  {}\n".format(node, stdout)
            if("active (running)" not in stdout):
               # message= message+ "Compute node {} do not have correct ports, expected {}, received {}".format(node, settings["ovsdpdk_ports"], total_ports)
                error=1
        if(error==1):
            logging.error("ovsdpdk testcase 17 failed, ovs-vswitchd service status is {} ")
            message= "ovsdpdk testcase 17 failed, ovs-vswitchd service status is {}\n ".format(stdout)+message   
        else:
            isPassed= True
            logging.info("ovsdpdk testcase 17 passed,  ovs-vswitchd service  running on all compute nodes")
            message= "ovsdpdk testcase 17 passed,  ovs-vswitchd service status is  running on all nodes {}\n ".format(stdout)+message
            logging.info("OVSDPDK Testcase 17 Passed")
    except Exception as e:
        logging.error("OVSDPDK Test case 17 failed/ error occured")
        logging.exception(e)
        message= "OVSDPDK Test case 17 failed/ error occured"
    logging.info("OVSDPDK testcase 17 Finished")
    return isPassed, message

def ovsdpdk_test_case_18(baremetal_nodes_ips):
    isPassed= False
    message=""
    total_bridges=bridges_up=0
    command1= "sudo ovs-vsctl show | grep Bridge"
    command2= "sudo ovs-vsctl show |grep 'is_connected: true'"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    message="  \nbridges status is  \n"
    try:
        for node in compute_nodes_ip:
            ssh_output= ssh_into_node(node, command1)
            ssh_output= ssh_output[0]
            message= message+ " compute node: {}, \n {} \n".format(node, ssh_output)
            ssh_output= ssh_output.split("\n")
            total_bridges= len(ssh_output)
        
        for node in compute_nodes_ip:
            ssh_output= ssh_into_node(node, command2)
            ssh_output= ssh_output[0]
            message= message+ " compute node: {}, \n {} \n".format(node, ssh_output)
            ssh_output= ssh_output.split("\n")
            bridges_up= len(ssh_output)
        if(bridges_up >=total_bridges):
            logging.info("All bridges up")
            logging.info("Test Case 18 passed")
            isPassed= True
            message="Test Case 18 passed, All bridges are up"+ message
        else: 
            logging.info("All bridges are not up")
            logging.error("Test Case 18 failed")
            message= "Test Case 18 failed, All bridges are not up"+ message
    except Exception as e:
        logging.error("OVSDPDK Testcase 18 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 18 failed, error occured"
    return isPassed, message

def ovsdpdk_test_case_22(baremetal_nodes_ips):
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
 
def ovsdpdk_test_case_28(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):
    logging.info("OVS DPDK Test Case 28 running")
    isPassed= False
    message=server_id=""
    try:
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
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token) 
    except Exception as e:
        logging.error("OVSDPDK Testcase 28 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 28 failed, error occured"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token) 
    return isPassed, message

def ovsdpdk_test_case_36(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):    
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    logging.info("OVS DPDK Test Case 36 running")
    isPassed= False
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
def ovsdpdk_test_case_43(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):    
    isPassed=False
    message=floating_ip=server_id=""
    
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0_ip= compute0_ip[0]
        # Search and Create Flavor

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

        else: 
            logging.error("OVSDPDK Testcase 43 failed, server creation failed")
            message="OVSDPDK Testcase 43 failed, server creation failed"
            logging.info("deleting flavor")
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token) 
        if(floating_ip !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip), token)
    
    except Exception as e:
        logging.error("OVSDPDK Testcase 43 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 43 failed, error occured"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token) 
        if(floating_ip !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip), token)
 

    return isPassed, message

def ovsdpdk_test_case_46(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):    
    isPassed= False
    message= server_1_id=server_2_id=server_1_floating_ip_id=""
    try:
        # Search and Create Flavor
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute0= compute0[0]
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
            command= "ping -c 3 {}".format(server_2_ip)
            result, error= instance_ssh(server_1_floating_ip, settings, command)
            if error==""  and "icmp_seq=3 Destination Host Unreachable" not in result:
                isPassed= True
                logging.info("Test Case 46 Passed")
                message= "testcase passed when 1 server has floating ip and it pinged other server with private ip \n ping result is: \n{}\n".format(result)
            else: 
                logging.error("Test Case 46 failed")
                message= "testcase failed when 1 server has floating ip and it pinged other server with private ip \n ping result is: \n{}\n".format(result)
        else:
            message="testcase failed because one or more server creation is failed"
            logging.error("testcase failed because one or more server creation is failed")
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token) 
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token) 
        if(server_1_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip_id), token)
                
    except Exception as e:
        logging.error("OVSDPDK Testcase 46 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 46 failed, error occured"
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token) 
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token) 
        if(server_1_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip_id), token)
    return isPassed, message
def ovsdpdk_test_case_47(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):    
    isPassed= False 
    message= server_1_id=server_2_id=server_1_floating_ip_id=server_2_floating_ip_id=""
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute0= compute0[0]
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
            command= "ping -c 3 {}".format(server_2_floating_ip)
            result1, error1= instance_ssh(server_1_floating_ip, settings, command)
            command= "ping -c 3 {}".format(server_1_floating_ip)
            result2, error2= instance_ssh(server_2_floating_ip, settings, command)            
            if error1=="" and error2== "" and "icmp_seq=3 Destination Host Unreachable" not in result1  and "icmp_seq=3 Destination Host Unreachable" not in result2:
                isPassed= True
                logging.info("Test Case 47 passed")
                message= "Test Case 47 Passed, both instances on same network and host pinged eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
            else: 
                logging.error("Test Case 47 failed")
                message= "Test Case 47 failed, both instances on same network and host can not ping eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
        else:
            message="testcase failed because one or more server creation is failed"
            logging.error("testcase failed because one or more server creation is failed")
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token) 
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token) 
        if(server_1_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip_id), token)
        if(server_2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_2_floating_ip_id), token)
        
    except Exception as e:
        logging.error("OVSDPDK Testcase 47 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 47 failed, error occured"
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token) 
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token) 
        if(server_1_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip_id), token)
        if(server_2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_2_floating_ip_id), token)

    return isPassed, message
def ovsdpdk_test_case_48(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):    
    isPassed= False
    # Search and Create Flavor
    message= server_1_id=server_2_id=server_1_floating_ip_id=server_2_floating_ip_id=""

    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-2" in key]
        compute0= compute0[0]
        compute1=  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
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
            command= "ping -c 3 {}".format(server_2_floating_ip)
            result1, error1= instance_ssh(server_1_floating_ip, settings, command)
            command= "ping -c 3 {}".format(server_1_floating_ip)
            result2, error2= instance_ssh(server_2_floating_ip, settings, command)            
            if error1=="" and error2== "" and "icmp_seq=3 Destination Host Unreachable" not in result1 and "icmp_seq=3 Destination Host Unreachable" not in result2:
                isPassed= True
                logging.info("testcase 48 passed")
                message= "Test Case 48 Passed, both instances on same network and different host pinged eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
            else: 
                logging.error("Test Case 48 failed")
                message= "Test Case 48 failed, both instances on same network and different host can not ping eachother\n server 1 {} to server 2 {} ping results are: \n {}\nserver 1 {} to server 2 {} ping results are: \n {}\n ".format(server_1_floating_ip, server_2_floating_ip, result1, server_2_floating_ip, server_1_floating_ip, result2)
        else:
            message="testcase failed because one or more server creation is failed"
            logging.error("testcase failed because one or more server creation is failed")
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token) 
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token) 
        if(server_1_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip_id), token)
        if(server_2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_2_floating_ip_id), token)
    except Exception as e:
        logging.error("OVSDPDK Testcase 48 failed, error occured")
        logging.exception(e)
        message="OVSDPDK Testcase 48 failed, error occured"

        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token) 
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token) 
        if(server_1_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_1_floating_ip_id), token)
        if(server_2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_2_floating_ip_id), token)
    return isPassed, message

def ovsdpdk_test_case_49(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("OVSDPDK testcase 49 running")
    isPassed= False
    message=""
    server_1_id=server_floating_ip_id=""   
    try:
        #search and create server
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error":
            logging.error("Test Case 49 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network_id, server_1_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            logging.info("cold migrating server")
            response=  perform_action_on_server(nova_ep,token, server_1_id, "migrate")
            time.sleep(20)
            if response==202:
                logging.info("confirming migration")
                perform_action_on_server(nova_ep,token, server_1_id, "confirmResize")

            logging.info("migration status code is: {}".format(response))
            logging.info("waiting for migration")
            wait_instance_boot(server_floating_ip)
            new_host= get_server_host(nova_ep, token, server_1_id)
            logging.info("new host is: "+new_host)
            if(response == 202 and new_host != compute1):
                command= "ping -c 3 {}".format(server_floating_ip)
                response2= subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                #stdout, stderr = response2.communicate()
                stdout = response2.stdout.read().decode('ascii')
                stderr = response2.stderr.read().decode('ascii')
                if stderr == "" and "icmp_seq=3 Destination Host Unreachable" not in stdout:
                    isPassed= True
                    logging.info ("Ping successfull!")
                    logging.info("OVSDPDK test Case 49 Passed")
                    message="OVSDPDK testcase 49 passed, cold migration of instance is successfull, status code is {}, old host {}, new host {} \n, ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("OVSDPDK test Case 49 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "OVSDPDK test Case 49 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("OVSDPDK test Case 49 failed, cold vmigration of instance failed, status code is {}, old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="OVSDPDK test Case 49 failed, cold migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host)
        
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token) 
    except Exception as e:
        logging.exception("OVSDPDK test Case 49 failed/ error occured")
        message="OVSDPDK testcase 49 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)    
    logging.info("OVSDPDK Test Case 49 finished")
    return isPassed, message

def ovsdpdk_test_case_50(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("OVSDPDK Test Case 50 running")
    isPassed= False
    message=""
    server_1_id=server_floating_ip_id=""
    
    try:
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        compute2 =  [key for key, val in baremetal_node_ips.items() if "compute-2" in key]
        compute2= compute2[0]
        #search and create server
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error":
            logging.error("Test Case 50 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            server_1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server_1_port= get_ports(neutron_ep, token, network_id, server_1_ip)
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_1_ip, server_1_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            logging.info("live migrating server")
            response= live_migrate_server(nova_ep,token, server_1_id, compute2)
            logging.info("migration status code is: {}".format(response))
            logging.info("waiting for migration")
            time.sleep(30)
            wait_instance_boot(server_floating_ip)
            new_host= get_server_host(nova_ep, token, server_1_id)
            logging.info("new host is: "+new_host)
            if(response == 202 and new_host != compute1):
                #response2 = os.system("ping -c 3 " + server_floating_ip)
                command= "ping -c 3 {}".format(server_floating_ip)
                response2= subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                #stdout, stderr = response2.communicate()
                stdout = response2.stdout.read().decode('ascii')
                stderr = response2.stderr.read().decode('ascii')
                print("stdout is: "+stdout)
                print("stdrr is: "+stderr)
                if stderr == "" and "icmp_seq=3 Destination Host Unreachable" not in stdout:
                    isPassed= True
                    logging.info ("Ping successfull!")
                    logging.info("OVSDPDK test Case 50 Passed")
                    message="OVSDPDK testcase 50 passed, live migration of instance is successfull, status code is {}, old host {}, new host {}  \n , ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("OVSDPDK test Case 50 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "OVSDPDK test Case 50 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("OVSDPDK test Case 50 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, ))
                message="OVSDPDK test Case 50 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, )
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    except Exception as e:
        logging.exception("OVSDPDK test Case 50 failed/ error occured")
        message="OVSDPDK testcase 50 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    logging.info("OVSDPDK Test Case 50 finished")
    return isPassed, message


