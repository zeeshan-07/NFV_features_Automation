from openstack_functions import *
import logging
from subprocess import PIPE, Popen
import os
from test_cases import *
import time

 
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

def get_vfs_count():
    command= "cat ~/pilot/templates/neutron-sriov.yaml |grep NumSriovVfs"
    result= os.popen(command).read()
    result= result.split(':')
    result= result[1].strip()
    return result
def get_sriov_enabled_interfaces():
    command= "cat ~/pilot/templates/neutron-sriov.yaml |grep physint:"
    result= os.popen(command).read()
    #result= result.strip('      - physint:')
    result= result.split('\n')
    result=result[:-1]
    i=0
    for interface in result:
        result[i]= interface.strip('      - physint:')
        i=i+1
    return result

def sriov_test_case_3(baremetal_nodes_ips):
    logging.info("SRIOV Test Case 3 running")
    isPassed=False
    message=output=""
    try:
        compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
        vfg= get_vfs_count()
        output="Vflags are: \n"
        logging.info("SRIOV virtual flags are: "+vfg)
        interfaces= get_sriov_enabled_interfaces()
        logging.info("SRIOV Interfaces are: {}".format(interfaces))
        error=0
        for interface in interfaces:
            output=output+ "interface {}\n".format(str(interface))
            for node in compute_nodes_ip:
                command= "ip link show "+interface
                vflags= ssh_into_node(node, command)
                #vflags=""
                output= output+"Compute Node: {} ".format(node)
                total_flags= vflags.count("vf")
                output= output+ " interface {} total vflags are {} \n".format(interface,total_flags)
                output= output+ vflags
                if(str(total_flags) != vfg):
                    error= 1
        if(error==1):
            logging.info("SRIOV vflag Testcase 3 Failed all computes nodes do not have {} vflags \n".format(vfg))
            message= "SRIOV vflag Testcase 3 Failed all computes nodes do not have {} vflags \n".format(vfg)+output
        else:
            logging.info("SRIOV vflag Testcase 3 Passed all computes nodes  have {} vflags \n".format(vfg))
            message= "SRIOV vflag Testcase 3 Passed all computes nodes  have {} vflags \n".format(vfg)+output
        logging.info("SRIOV Test Case 3 finished")
    except Exception as e:
        logging.exception("sriov_vflag testcase 3 failed/ error occured {}".format(e))
        message= "sriov_vflag testcase 3 failed/ error occured {}".format(e)
    logging.info("SRIOV Test Case e finished")
    return isPassed, message

def sriov_test_case_7_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 7 and 8 running")
    isPassed7=isPassed8= False
    message7=message8=port_id=port_ip=status=floating_ip_id=server_id=""    
    try:
        # Search and Create Flavor
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
            if(server_id != ""):
                logging.info("deleting all servers")
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            if(port_id != ""):
                delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_id), token)
    
    except Exception as e:
        logging.exception(e)
        message7="SRIOV test case 7 failed/ error occured: {}".format(status)
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(port_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_id), token)
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

            if(server_id != ""):
                logging.info("deleting all servers")
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            if(port_id != ""):
                delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_id), token)
            if(server_floating_ip_id !=""):
                logging.info("releasing floating ip")
                delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip_id), token)
        except Exception as e:
            logging.exception(e)
            logging.error(e)
            message8="SRIOV test case 8 failed/ error occured: {}".format(status)
            if(server_id != ""):
                logging.info("deleting all servers")
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            if(port_id != ""):
                delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_id), token)
            if(server_floating_ip_id !=""):
                logging.info("releasing floating ip")
                delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip_id), token)

            
    return isPassed7, message7, isPassed8, message8
def sriov_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 10 running")
    isPassed= False
    message=""
    port_1_id=port_2_id=floating_ip_id=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id="" 
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    except Exception as e:
        logging.error("Test Case 10 failed/ error occured")
        message="Both instances can not ping eachother on same compute node same network/ error occured"
        logging.exception(e)
        logging.error(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)

    return isPassed, message
    
def sriov_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 11 running")
    isPassed= False
    message=""
   
    port_1_id=port_2_id=floating_ip_id=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id="" 
    # Search and Create Flavor
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)

    except Exception as e:
        logging.error(e)
        logging.error("Test Case 11 failed")
        message="Both instances can not pinged eachother on different compute node same network/ error occured"
        logging.exception(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
       
    return isPassed, message   

def sriov_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 12 running")
    isPassed= False
    message=""
    port_1_id=floating_ip_id=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id="" 
    try: 
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
       
    except Exception as e:
        logging.error(e)
        logging.error("Test Case 12 failed")
        message12="Both instances failed to ping eachother on different compute node same network/ error occured"
        logging.exception(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
               
    return isPassed, message

def sriov_test_case_13_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 13, 14 running")
    isPassed13=isPassed14= False
    message13=message14=""
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
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
            message13="legancy instance and sriov instances can not ping eachother on same compute node same network, because one of the instance is failed"
            message14="instance can not ping gateway after reboot, insance creation failed"
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
                gateway, error= instance_ssh(flaoting_1_ip, settings, "netstat -rn |grep '0.0.0.0'")
                gateway= gateway.split('\n')
                gateway= gateway[0].split('0.0.0.0')
                gateway= gateway[1].strip('         ')
                logging.info("Gateway is: {}".format(gateway))
                logging.info("rebooting instance")
                reboot_server(nova_ep,token, server_1_id)
                time.sleep(5)
                wait_instance_boot(flaoting_1_ip)
                command= "ping -c 3 {}".format(gateway)
                stdout, stderr= instance_ssh(flaoting_1_ip, settings, command)
                if stderr == "" and "icmp_seq=3 Destination Host Unreachable" not in stdout:
                    isPassed14= True
                    logging.info ("Ping successfull!")
                    logging.info("SRIOV trestcase 14 passed, instance successfully pinged gateway after reboot, ping rsult is \n {} ".format(stdout))
                    message14="SRIOV trestcase 14 passed, instance successfully pinged gateway after reboot, ping rsult is \n {} ".format(stdout)
                else:
                    logging.error("SRIOV trestcase 14 failed, instance failed to pinged gateway after reboot, ping rsult is \n {} ".format(stdout))
                    message14="SRIOV trestcase 14 failed, instance failed to pinged gateway after reboot, ping rsult is \n {} ".format(stdout)        
            else: 
                logging.error("Test Case 13 failed Both instances can not pingeachother on different compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, floating_2_ip_id, result1, flaoting_2_ip, flaoting_1_ip, result2))
                message13="Both instances can not pingeachother on different compute node same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(flaoting_1_ip, floating_2_ip_id, result1, flaoting_2_ip, flaoting_1_ip, result2)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)    
    except Exception as e:
        logging.error("Test Case 13 and 14 failed/ error occured ".format(e))
        logging.exception(e)
        message13="Both instances can not ping eachother on different compute node same network/ error occured"
        message14= "instance can not ping gateway after reboot, error occured "
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    return isPassed13, message13, isPassed14, message14

def sriov_test_case_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 15 running")
    isPassed= False
    message=""
    port_1_id=floating_ip_id=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id="" 
    
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
       
    except Exception as e:
        logging.error("Test Case 15 failed")
        message="Both instances failed to ping eachother on different compute node same network/ error occured"
        logging.exception(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)   
        
    return isPassed, message

def sriov_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 16 running")
    isPassed= False
    message=""
    
    port_1_id=floating_ip_id=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id="" 
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)   
        
    except Exception as e:
        logging.error("Test Case 16 failed")
        message="Both instances failed pinged eachother on different compute node same network/ error occured"
        logging.exception(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)   
        
    return isPassed, message

def sriov_test_case_17(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 17 running")
    isPassed= False
    message=""
    port_1_id=port_2_id=floating_ip_id=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id="" 
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    except Exception as e:
        logging.error("Test Case 17 failed")
        message="Both sriov instances failed to ping eachother on same compute node and different network/ error occured"
        logging.exception(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
              
    return isPassed, message

def sriov_test_case_18(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 18 running")
    isPassed= False
    message=""
    port_1_id=port_2_id=floating_ip_id=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id="" 
    
    try: 
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)

    except Exception as e:
        logging.error("Test Case 18 failed")
        message="Both instances successfully pinged eachother on different compute node and different network/ error occured"
        logging.exception(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if(port_1_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
        if(port_2_id != ""):
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
      
    return isPassed, message

def sriov_test_case_19(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("SRIOV Test Case 19 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=""
    
    try:
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        compute2 =  [key for key, val in baremetal_node_ips.items() if "compute-2" in key]
        compute2= compute2[0]
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova1", security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error":
            logging.error("Test Case 19 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
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
                    logging.info("SRIOV test Case 19 Passed")
                    message="SRIOV testcase 19 passed, live migration of instance is successfull, status code is {}, old host {}, new host {}  \n , ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("SRIOV test Case 19 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "SRIOV test Case 19 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, ))
                message="live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, )
        

        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        time.sleep(10)
        logging.info("releasing floating ip")
        delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    except Exception as e:
        logging.exception("DVR test Case 31 failed/ error occured")
        message="DVR testcase 31 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)

        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    logging.info("DVR Test Case 31 finished")
    return isPassed, message

def sriov_test_case_20(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 32 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""   
    try:
        #search and create server
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova1", security_group_id, compute1)

        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error":
            logging.error("Test Case 32 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
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
                    logging.info("DVR test Case 32 Passed")
                    message="DVR testcase 32 passed, cold migration of instance is successfull, status code is {}, old host {}, new host {} \n, ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("DVR test Case 32 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "DVR test Case 32 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("cold vmigration of instance failed, status code is {}, old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="cold migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host)
        
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
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
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)    
    logging.info("DVR Test Case 32 finished")
    return isPassed, message



