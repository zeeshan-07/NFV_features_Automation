from openstack_functions import *
import logging
import os
import time

def hci_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 3 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "hci-0" in key]
    compute0= compute0[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute0, "nova0")
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if  status1 == "error" :
            logging.error("Test Case 3 failed")
            logging.error("Instances creation failed")
            message="instance creation failed, its status is {}".format(status1)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            response = os.system("ping -c 3 " + server_floating_ip)
            if response == 0:
                isPassed= True
                logging.info ("Ping successfull!")
                logging.info("HCI test Case 3 Passed")
                message="HCI testcase 3 passed, HCI instance created and pinged successfully"
            else:
                logging.error("hci instance ping failed")
                message="HCI instance created but ping failed/ error occured "
            
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
            time.sleep(5)
       
    except Exception as e:
        logging.exception("HCI test Case 3 failed/ error occured")
        message="HCI instance creation and ping failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
            time.sleep(5)      
    logging.info("HCI Test Case 3 finished")
    return isPassed, message

def hci_test_case_4(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 4 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "hci-0" in key]
    compute0= compute0[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute0, "nova0")
        server_build_wait(nova_ep, token, [server1_id])
        server2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network2_id, security_group_id, compute0, "nova0")
        server_build_wait(nova_ep, token, [server1_id, server2_id])
        
        status1= check_server_status(nova_ep, token, server1_id)
        status2= check_server_status(nova_ep, token, server2_id)
        if  status1 == "error" or status2 == "error":
            logging.error("Test Case 4 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}, instance 2 status is: {}".format(status1, status2)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            server2_ip= get_server_ip(nova_ep, token, server2_id, settings["network2_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            logging.info("Server 2 Ip is: {}".format(server2_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            server2_port= get_ports(neutron_ep, token, network2_id, server2_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            logging.info("Server 2 Port is: {}".format(server2_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            #server2_floating_ip, server2_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
            server2_floating_ip, server2_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server2_port, server2_floating_ip_id )

            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            wait_instance_boot(server2_floating_ip)
            wait_instance_ssh(server_floating_ip, settings)
            wait_instance_ssh(server2_floating_ip, settings)
            logging.info("ssh into server1")
            command= "ping  -c 3 {}".format(server2_floating_ip)
            result1, error1= instance_ssh(server_floating_ip, server2_floating_ip, settings, command)
            logging.info("ssh into server2")
            command= "ping  -c 3 {}".format(server_floating_ip)
            result2, error2= instance_ssh(server2_floating_ip, server_floating_ip, settings, command)

        if error1 =="" and error2 == "":
            isPassed=True     
            logging.info("HCI testcase 4 passed")
            message="two hci instances  successfully pinged eachother on same compute node and different network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
        else:
            logging.info("HCI testcase 4 failed")
            message="two hci  instances failed to ping eachother on same compute node and different network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
        time.sleep(5)
    except Exception as e:
        logging.exception("HCI test Case 4 failed/ error occured")
        message="HCI testcase 4 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
            time.sleep(5)

    logging.info("HCI Test Case 4 finished")
    return isPassed, message

def hci_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 5 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "hci-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "hci-1" in key]
    compute1= compute1[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute0, "nova0")
        server2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1, "nova1")

        server_build_wait(nova_ep, token, [server1_id, server2_id])
        status1= check_server_status(nova_ep, token, server1_id)
        status2= check_server_status(nova_ep, token, server2_id)
        if  status1 == "error" or status2 == "error":
            logging.error("Test Case 5 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}, instance 2 status is: {}".format(status1, status2)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            server2_ip= get_server_ip(nova_ep, token, server2_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            logging.info("Server 2 Ip is: {}".format(server2_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            logging.info("Server 2 Port is: {}".format(server2_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            #server2_floating_ip, server2_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
            server2_floating_ip, server2_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server2_port, server2_floating_ip_id )

            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            wait_instance_boot(server2_floating_ip)
            wait_instance_ssh(server_floating_ip, settings)
            wait_instance_ssh(server2_floating_ip, settings)
            logging.info("ssh into server1")
            command= "ping  -c 3 {}".format(server2_floating_ip)
            result1, error1= instance_ssh(server_floating_ip, server2_floating_ip, settings, command)
            logging.info("ssh into server2")
            command= "ping  -c 3 {}".format(server_floating_ip)
            result2, error2= instance_ssh(server2_floating_ip, server_floating_ip, settings, command)

            if error1 =="" and error2 == "":
                isPassed=True     
                logging.info("HCI testcase 5 passed")
                message="two hci instances  successfully pinged eachother on different compute node and same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
            else:
                logging.info("HCI testcase 5 failed")
                message="two hci  instances failed to ping eachother on  different node and same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
            
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
            time.sleep(5)
            
    except Exception as e:
        logging.exception("HCI test Case 5 failed/ error occured")
        message="HCI testcase 5 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
            time.sleep(5)
    logging.info("HCI Test Case 5 finished")
    return isPassed, message

def hci_test_case_6(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 6 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "hci-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "hci-1" in key]
    compute1= compute1[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute0, "nova0")
        server2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network2_id, security_group_id, compute1, "nova1")

        server_build_wait(nova_ep, token, [server1_id, server2_id])
        status1= check_server_status(nova_ep, token, server1_id)
        status2= check_server_status(nova_ep, token, server2_id)
        if  status1 == "error" or status2 == "error":
            logging.error("Test Case 6 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}, instance 2 status is: {}".format(status1, status2)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            server2_ip= get_server_ip(nova_ep, token, server2_id, settings["network2_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            logging.info("Server 2 Ip is: {}".format(server2_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            server2_port= get_ports(neutron_ep, token, network2_id, server2_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            logging.info("Server 2 Port is: {}".format(server2_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            #server2_floating_ip, server2_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
            server2_floating_ip, server2_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server2_port, server2_floating_ip_id )

            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            wait_instance_boot(server2_floating_ip)
            wait_instance_ssh(server_floating_ip, settings)
            wait_instance_ssh(server2_floating_ip, settings)
            logging.info("ssh into server1")
            command= "ping  -c 3 {}".format(server2_floating_ip)
            result1, error1= instance_ssh(server_floating_ip, server2_floating_ip, settings, command)
            logging.info("ssh into server2")
            command= "ping  -c 3 {}".format(server_floating_ip)
            result2, error2= instance_ssh(server2_floating_ip, server_floating_ip, settings, command)

            if error1 =="" and error2 == "":
                isPassed=True     
                logging.info("HCI testcase 6 passed")
                message="two hci instances  successfully pinged eachother on different compute node and different network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
            else:
                logging.info("HCI testcase 6 failed")
                message="two hci  instances failed to ping eachother on different compute node and different network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
        time.sleep(5)   
    except Exception as e:
        logging.exception("HCI test Case 6 failed/ error occured")
        message="HCI testcase 6 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
            time.sleep(5)

    logging.info("HCI Test Case 6 finished")
    return isPassed, message

def hci_test_case_7(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 7 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "hci-0" in key]
    compute0= compute0[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute0, "nova0")
        server_build_wait(nova_ep, token, [server1_id])
        server2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute0, "nova0")
        server_build_wait(nova_ep, token, [server2_id])
        status1= check_server_status(nova_ep, token, server1_id)
        status2= check_server_status(nova_ep, token, server2_id)
        if  status1 == "error" or status2 == "error":
            logging.error("Test Case 7 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}, instance 2 status is: {}".format(status1, status2)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            server2_ip= get_server_ip(nova_ep, token, server2_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            logging.info("Server 2 Ip is: {}".format(server2_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            logging.info("Server 2 Port is: {}".format(server2_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            #server2_floating_ip, server2_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
            server2_floating_ip, server2_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server2_port, server2_floating_ip_id )

            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            wait_instance_boot(server2_floating_ip)
            wait_instance_ssh(server_floating_ip, settings)
            wait_instance_ssh(server2_floating_ip, settings)
            logging.info("ssh into server1")
            command= "ping  -c 3 {}".format(server2_floating_ip)
            result1, error1= instance_ssh(server_floating_ip, server2_floating_ip, settings,command)
            logging.info("ssh into server2")
            command= "ping  -c 3 {}".format(server_floating_ip)
            result2, error2= instance_ssh(server2_floating_ip, server_floating_ip, settings, command)

            if error1 =="" and error2 == "":
                isPassed=True     
                logging.info("HCI testcase 7 passed")
                message="two hci instances  successfully pinged eachother on same compute node and same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
            else:
                logging.info("HCI testcase 7 failed")
                message="two hci  instances failed to ping eachother on same  compute node and same network \n result of instance {} ping to instance {} is \n {} \n result of instance {} ping to instance {} is \n {} \n ".format(server_floating_ip, server2_floating_ip, result1, server2_floating_ip, server_floating_ip, result2)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
        time.sleep(5)
           
    except Exception as e:
        logging.exception("HCI test Case 7 failed/ error occured")
        message="HCI testcase 7 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server2_id), token)
            time.sleep(10)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(server2_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server2_floating_ip_id), token)
            time.sleep(5)
    logging.info("HCI Test Case 7 finished")
    return isPassed, message

def hci_test_case_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 8 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute1 =  [key for key, val in baremetal_node_ips.items() if "hci-1" in key]
    compute1= compute1[0]
    compute2 =  [key for key, val in baremetal_node_ips.items() if "hci-2" in key]
    compute2= compute2[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1, "nova1")
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if  status1 == "error":
            logging.error("Test Case 8 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
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
                    logging.info("HCI test Case 8 Passed")
                    message="HCI testcase 8 passed, live migration of instance is successfull, status code is {}, old host {}, new host {} \n".format(response, compute1, new_host)
                else:
                    logging.error("HCI test Case 8 failed, ping failed after live migration")
                    message= "HCI test Case 8 failed, ping failed after live migration"
            else:
                logging.error("live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        time.sleep(5)

    except Exception as e:
        logging.exception("HCI test Case 8 failed/ error occured")
        message="HCI testcase 8 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        time.sleep(5)
        
    logging.info("HCI Test Case 8 finished")
    return isPassed, message
    
def hci_test_case_9(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 9 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute1 =  [key for key, val in baremetal_node_ips.items() if "hci-1" in key]
    compute1= compute1[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1, "nova1")
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if  status1 == "error":
            logging.error("Test Case 9 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            logging.info("cold migrating server")
            response=  perform_action_on_server(nova_ep,token, server1_id, "migrate")
            time.sleep(20)
            if response==202:
                logging.info("confirming migrate")
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
                    logging.info("HCI test Case 9 Passed")
                    message="HCI testcase 9 passed, cold migration of instance is successfull, status code is {}, old host {}, new host {} \n".format(response, compute1, new_host)
                else:
                    logging.error("HCI test Case 9 failed, ping failed after cold migration")
                    message= "HCI test Case 9 failed, ping failed after cold migration"
            else:
                logging.error("cold vmigration of instance failed, status code is {}, old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="cold  migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host)
        
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        time.sleep(5)
 
    except Exception as e:
        logging.exception("HCI test Case 9 failed/ error occured")
        message="HCI testcase 9 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
       
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
            time.sleep(5)
        
    logging.info("HCI Test Case 9 finished")
    return isPassed, message

def hci_test_case_10(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 10 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=volume_id=""
    compute1 =  [key for key, val in baremetal_node_ips.items() if "hci-1" in key]
    compute1= compute1[0]
    try:
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1, "nova1")
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if  status1 == "error":
            logging.error("Test Case 10 failed")
            logging.error("Instances creation failed")
            message="one of the instance creation failed, insatnce 1 status is {}".format(status1)
        else:
            server_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            logging.info("Server 1 Ip is: {}".format(server_ip))
            server_port= get_ports(neutron_ep, token, network_id, server_ip)
            logging.info("Server 1 Port is: {}".format(server_port))
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            #server_floating_ip, server_floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
            server_floating_ip, server_floating_ip_id= create_floatingip_wo_port(neutron_ep, token, public_network_id )
            assign_ip_to_port(neutron_ep, token, server_port, server_floating_ip_id )
            logging.info("Waiting for server to boot")
            wait_instance_boot(server_floating_ip)
            project_id= find_admin_project_id(keystone_ep, token)
            logging.info("Creating volume")
            volume_id= search_and_create_volume(cinder_ep, token, project_id, "testcase_volume", 10)
            logging.info("Volume id "+volume_id)
            volume_build_wait(cinder_ep, token, [volume_id], project_id)
            volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
            logging.info("volume status is: "+volume_status)
            if(volume_status== "error"):
                logging.error("Volume creation failed")
                message= "HCI testcase 10 failed because volume creation failed"
            if(volume_status != "in-use"):   
                logging.info("attaching volume to server") 
                attach_volume_to_server(nova_ep, token, project_id, server1_id, volume_id, "/dev/vdd")
            time.sleep(20)
            volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
            if(volume_status == "in-use"):  
                isPassed=True
                logging.info("Volume successfully created and attached to serever")
                message= "HCI testcase 10 passed, instance and volume created and volume is successfully attached to server, volume status is: {}".format(volume_status)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(volume_id !=""):
            logging.info("deleting volume")
            delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id, volume_id), token)
            time.sleep(5)
 
    except Exception as e:
        logging.exception("HCI test Case 10 failed/ error occured")
        message="HCI testcase 10 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(volume_id !=""):
            logging.info("deleting volume")
            delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id, volume_id), token)
            time.sleep(5)
    logging.info("HCI Test Case 10 finished")
    return isPassed, message