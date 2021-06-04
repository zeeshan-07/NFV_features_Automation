from openstack_functions import *
from volume import *
import logging

def mtu9000_test_case_3(baremetal_nodes_ips):
    logging.info("Starting MTU9000 testcase 3")
    isPassed= False
    message=""
    error=0
    try: 
        compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
        command= "ifconfig | grep mtu"
        message="MTU on interfaces is: \n"
        for node in compute_nodes_ip:
            output, error1= ssh_into_node(node, command)
            message= message+ " compute node {} \n {}".format(node, output)
            output= output.split('\n')
            for interface in output:
                mtu = interface.split(" ")
                if( mtu[len(mtu)-1] != str(9000)):
                    if(mtu[0] !="lo:" and mtu[0] != "bt-int:" and mtu[0] != "br-tun:"):
                        error=1
        if error== 0:
            logging.info("MTU9000 Testcase 3 Passed")
            isPassed= True
            message= "MTU9000 Testcase 3 Passed, all compute nodes have mtu 9000 on interfaces \n{}".format(message) 
        else: 
          
            logging.error("MTU 9000 Test Case 3 failed")
            message= "MTU9000 Testcase 3 failed, all compute nodes do not have mtu 9000 on interfaces \n{}".format(message) 

    except Exception as e:
        logging.error("MTU 9000 Test Case 3 failed")
        message= "MTU9000 Testcase 3 failed/ error occured"
        logging.exception(e)
    logging.info("Mtu9000 Test Case 3 Finished")
    return isPassed, message

def mtu9000_test_case_4(baremetal_nodes_ips):
    logging.info("Starting MTU9000 testcase 4")
    isPassed= False
    message=""
    error=0 
    try: 
        controller_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "controller" in key]
        command= "ifconfig | grep mtu"
        message="MTU on interfaces is: \n"
        for node in controller_nodes_ip:
            output, error1= ssh_into_node(node, command)
            message= message+ " controller node {} \n {}".format(node, output)
            output= output.split('\n')
            for interface in output:
                mtu = interface.split(" ")
                if( mtu[len(mtu)-1] != str(9000)):
                    if(mtu[0] !="lo:" and mtu[0] != "bt-int:" and mtu[0] != "br-tun:"):
                        error=1
        if error== 0:
            logging.info("MTU9000 Testcase 4 Passed")
            isPassed= True
            message= "MTU9000 Testcase 4 Passed, all controller nodes have mtu 9000 on interfaces \n{}".format(message) 
        else: 
            logging.error("MTU 9000 Test Case 4 failed")
            message= "MTU9000 Testcase 4 failed, all controller nodes do not have mtu 9000 on interfaces \n{}".format(message) 

    except Exception as e:
        logging.error("MTU 9000 Test Case 4 failed")
        message= "MTU9000 Testcase 4 failed/ error occured"
        logging.exception(e)
    logging.info("Mtu9000 Test Case 4 Finished")
    return isPassed, message

def mtu9000_test_case_5(baremetal_nodes_ips):
    logging.info("Starting MTU9000 testcase 5")
    isPassed= False
    message=""
    error=0
    
    try: 
        storage_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "storage" in key]
        command= "ifconfig | grep mtu"
        message="MTU on interfaces is: \n"
        for node in storage_nodes_ip:
            output, error1= ssh_into_node(node, command)
            message= message+ " storage node {} \n {}".format(node, output)
            output= output.split('\n')
            for interface in output:
                mtu = interface.split(" ")
                if( mtu[len(mtu)-1] != str(9000)):
                    if(mtu[0] !="lo:" and mtu[0] != "bt-int:" and mtu[0] != "br-tun:"):
                        error=1
        if error== 0:
            logging.info("MTU9000 Testcase 5 Passed")
            isPassed= True
            message= "MTU9000 Testcase 5 Passed, all storage nodes have mtu 9000 on interfaces \n{}".format(message) 
        else: 
            logging.error("MTU 9000 Test Case 4 failed")
            message= "MTU9000 Testcase 5 failed, all storage nodes do not have mtu 9000 on interfaces \n{}".format(message) 

    except Exception as e:
        logging.error("MTU 9000 Test Case 5 failed")
        message= "MTU9000 Testcase 5 failed/ error occured"
        logging.exception(e)
    logging.info("Mtu9000 Test Case 5 Finished")
    return isPassed, message

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
        else:
            storage_nodes_ip.append("")
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
        message="MTU terstcase 6 failed/ error occured"
        
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
        message="MTU terstcase 7 failed/ error occured"
        
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
        message="MTU terstcase 8 failed/ error occured"
        
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
            message= "Network has incorrect mtu size, mtu size is: {} ".format(network["network"]["mtu"])
    except Exception as e:
        logging.error("MTU 9000 Test Case 9 failed")
        logging.error("Network mtu verification testcase failed/ error occured")
        message="Network mtu verification testcase failed/ error occured"
        logging.exception(e) 
        message="MTU terstcase 9 failed/ error occured"
    logging.info("Mtu9000 Test Case 9 Finished")

    return isPassed, message

def mtu9000_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("MTU9000 Test Case 10")
    isPassed= False
    message=server_id=""
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
        if(server_id != ""):
                logging.info("deleting all servers")
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token) 
    except Exception as e:
        logging.error("MTU 9000 Test Case 10 failed/ error occured")
        logging.exception(e)
        message="MTU terstcase 10 failed/ error occured"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)    
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

def mtu9000_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("MTU9000 Test Case 12")
    isPassed= False
    message=server_id=floating_ip_id=""
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
        logging.info("deleting all servers")
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token) 
        if(floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip_id), token)
    except Exception as e:
        logging.error("MTU 9000 Test Case 12 failed/ error occured")
        logging.exception(e)
        message="MTU terstcase 12 failed/ error occured"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token) 
        if(floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_ip_id), token)   
    return isPassed, message
def mtu9000_test_case_13(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("MTU9000 Test Case 13")
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
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
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_2_ip)
            output1, error1= instance_ssh(flaoting_1_ip, settings, command)
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_1_ip)
            output2, error2= instance_ssh(flaoting_2_ip, settings, command)
            if error1=="" and error2=="" and "icmp_seq=3 Destination Host Unreachable" not in output1 and "icmp_seq=3 Destination Host Unreachable" not in output2 :
                logging.info("MTU9000 Testcase 13 Passed")
                isPassed= True
                message= "both instances successfully pinged other other on mtu size 8972, on same compute node, same network \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
            else: 
                logging.error("MTU 9000 Test Case 13 failed")
                message="both instances can not ping other other on mtu size 8972, on same compute node, same network \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
        else: 
            logging.error("MTU 9000 Test Case 13 failed")
            message= "instance creation failed on network with mtu size 9000. instance 1 state is: {}, instance 2 state is: {}".format(status1, status2 )
        
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
        logging.error("MTU 9000 Test Case 13 failed/ error occured")
        logging.exception(e)
        message="MTU terstcase 13 failed/ error occured"
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
            
    return isPassed, message

def mtu9000_test_case_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("MTU9000 Test Case 14")
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id= floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
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
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_2_ip)
            output1, error1= instance_ssh(flaoting_1_ip, settings, command)
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_1_ip)
            output2, error2= instance_ssh(flaoting_2_ip, settings, command)
            if error1=="" and error2=="" and "icmp_seq=3 Destination Host Unreachable" not in output1 and "icmp_seq=3 Destination Host Unreachable" not in output2 :
                logging.info("MTU9000 Testcase 14 Passed")
                isPassed= True
                message= "both instances successfully pinged other other on mtu size 8972, on same network, different compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
            else: 
                logging.error("MTU 9000 Test Case 14 failed")
                message="both instances can not ping other other on mtu size 8972, on same network, different compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
        else: 
            logging.error("MTU 9000 Test Case 14 failed")
            message= "instance creation failed on network with mtu size 9000. instance 1 state is: {}, instance 2 state is: {}".format(status1, status2 )
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
        logging.error("MTU 9000 Test Case 14 failed/ error occured")            
        logging.exception(e)
        message="MTU terstcase 14 failed/ error occured"
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
    return isPassed, message

def mtu9000_test_case_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("MTU9000 Test Case 15")
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id= floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
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
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_2_ip)
            output1, error1= instance_ssh(flaoting_1_ip, settings, command)
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_1_ip)
            output2, error2= instance_ssh(flaoting_2_ip, settings, command)
            if error1=="" and error2=="" and "icmp_seq=3 Destination Host Unreachable" not in output1 and "icmp_seq=3 Destination Host Unreachable" not in output2 :
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
        logging.error("MTU 9000 Test Case 15 failed/ error occured")
        logging.exception(e)
        message="MTU terstcase 15 failed/ error occured" 
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


    return isPassed, message
def mtu9000_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network1_id, subnet1_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("MTU9000 Test Case 16")
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id= floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
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
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_2_ip)
            output1, error1= instance_ssh(flaoting_1_ip, settings, command)
            command= "ping  -c 3 -s 8972 -M do {}".format(flaoting_1_ip)
            output2, error2= instance_ssh(flaoting_2_ip, settings, command)
            if error1=="" and error2=="" and "icmp_seq=3 Destination Host Unreachable" not in output1 and "icmp_seq=3 Destination Host Unreachable" not in output2 :
                logging.info("MTU9000 Testcase 16 Passed")
                isPassed= True
                message= "both instances successfully pinged other other on mtu size 8972, on different network, same compute nodes \n Ping Results are: \n ping to  instance2 {} ({}) from instance 1 {} ({}) \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, server_1_ip, flaoting_1_ip, server_2_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
            else: 
                logging.error("MTU 9000 Test Case 16 failed")
                message="both instances can not ping other other on mtu size 8972, on different network, same compute nodes \n Ping Results are: \n ping to  instance2 {} from instance 1 {} \n {}\n \n ping to instance 1 {} from instance2: {}\n {}\n".format(flaoting_2_ip, flaoting_1_ip, output1, flaoting_1_ip, flaoting_2_ip, output2)
        else: 
            logging.error("MTU 9000 Test Case 16 failed")
            message= "instance creation failed on network with mtu size 9000. instance 1 state is: {}, instance 2 state is: {}".format(status1, status2 )
    
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
        logging.error("MTU 9000 Test Case 16 failed/ error occured")
        logging.exception(e) 
        message="MTU 9000 Test Case 16 failed/ error occured" 
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

    return isPassed, message

def mtu9000_volume_test_case(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_node_ips, flavor_id, network1_id, security_group_id, image_id):
    message=""
    testcases_passed= 0
    logging.info("starting volume testcases")
    server1_id=floating_1_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    print(compute0)
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    print(compute1)

    try:
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network1_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if status1 == "active":
            server1_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            server1_port= get_ports(neutron_ep, token, network1_id, server1_ip)
            public_network_id= search_network(neutron_ep, token, settings["external_network_name"])
            public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
            testcases_passed, message= volume_test_cases(image_ep, cinder_ep, keystone_ep, nova_ep, token, settings, baremetal_node_ips, server1_id, flaoting_1_ip,  flavor_id, network1_id, security_group_id, compute1) 
        else:
            logging.info("volume testcases skipped, becuase server is not created")
            message= "volume testcases skipped, becuase server is not created"
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token) 
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
  
    except Exception as e:
        logging.exception(e)
        message= "volume testcases skipped, error/exception occured {}".format(str(e))
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token) 
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
    
    return testcases_passed, message
