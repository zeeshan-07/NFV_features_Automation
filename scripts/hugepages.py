from openstack_functions import *
import logging
import paramiko
import time
import math
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
def wait_server_pause(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            if not(status == "paused"):
                logging.info("Waiting for server/s to pause")
                flag=1
                time.sleep(5)
        if flag==0:
            break
def wait_server_suspend(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            print(status)
            if not(status == "suspended"):
                logging.info("Waiting for server/s to suspend")
                flag=1
                time.sleep(5)
        if flag==0:
            break
def wait_server_shutdown(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            print(status)
            if not(status == "stopped"):
                logging.info("Waiting for server/s to stop")
                flag=1
                time.sleep(5)
        if flag==0:
            break

def wait_server_delete(nova_ep, token, server_names):
    while True:
        flag=0
        for server in server_names:
            id= search_server(nova_ep, token, server)
            if(id is not None ):
                logging.info("Waiting for server/s to delete")
                flag=1
                time.sleep(5)
        if flag==0:
            break
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

def parse_hugepage_size(huge_page_info, parameter):
    huge_page_info= huge_page_info.split('\n')
    for property in huge_page_info:
        line= property.split()
        if line[0] == parameter:
           return line[1]

def read_instance_xml(ssh_output):
    return huge_page_size, huge_page_consumption

def hugepages_test_case_1(baremetal_nodes_ips):
    message=""
    #Get Huge Pages information from node
    command= "grep Huge /proc/meminfo"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    message= "Huge page size is: "
    try:
        for node in compute_nodes_ip:
            ssh_output= ssh_into_node(node, command)
            print(ssh_output)
            huge_page_size= parse_hugepage_size(ssh_output,"Hugepagesize:")
            logging.info("huge page size of compute node {}, is {}".format(node, huge_page_size))
            message= message+ " node {} hugepage size: {} ".format(node, huge_page_size)
            if huge_page_size != "1048576":
                logging.error("Compute node {} do not have 1 GB hugepage size".format(node))
                logging.error("Testcase 1 failed")
                return False, message
                break
        else:
            logging.info("All compute nodes have 1 GB hugepage size,")
            logging.info("Testcase 1 Passed")
            return True, message
    except Exception as e:
        logging.error("Hugepage Test case 1 failed/ error occured")
        logging.exception(e)
        return False, message

def hugepages_test_case_2(baremetal_nodes_ips):

    message= "Huge page size is: "
    message=""
    #Get Huge Pages information from node
    command= "grep Huge /proc/meminfo"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    message= "Huge page size is: "
    try:
        for node in compute_nodes_ip:
            ssh_output= ssh_into_node(node, command)
            huge_page_size= parse_hugepage_size(ssh_output, "Hugepagesize:")
            message= message+ " node {} hugepage size: {} ".format(node, huge_page_size)
            if huge_page_size != "2048":
                logging.error("Compute node {} do not have 2MB hugepage size".format(node))
                logging.error("Testcase 2 failed")
                message= message+ " node {} hugepage size: {} ".format(node, huge_page_size)
                return False, message
                break
        else:
            logging.error("All compute nodes have 2 MB hugepage size")
            logging.error("Testcase 2 Passed")
            return True, message
    except Exception as e:
        logging.error("Hugepage Test case 2 failed/ error occured")
        logging.exception(e)
        return False, message

def hugepages_test_case_3(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)

    #search and create server
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        output= ssh_into_node(compute0_ip, " grep Huge /proc/meminfo")
        hugepg_free_before= parse_hugepage_size(output, "HugePages_Free:")
        server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_id])  
        if( check_server_status(nova_ep, token, server_id)== "active"):
            instance_name= get_server_instance_name(nova_ep, token, server_id)
            command= "sudo cat /etc/libvirt/qemu/{}.xml | grep 'page size'".format(instance_name)
            output= ssh_into_node(compute0_ip, command)
            hgpages= output.split("'")
            logging.info("Instance hugepage size is: {}".format(output[1]))
            if hgpages[1]=="1048576":
                logging.info("Instance has valid hugepage size")
                output= ssh_into_node(compute0_ip, " grep Huge /proc/meminfo")
                hugepg_free_after= parse_hugepage_size(output, "HugePages_Free:")
                if (int(hugepg_free_before)- int(hugepg_free_after))==4:
                    logging.info("Instance has consumed valid hugepages")
                    logging.info("Test case 3 passed")
                    isPassed= True
                    message= "instance has valid hugepages {} and consumed valid hugepages before {} after {}, should consume 4".format(hgpages[1], hugepg_free_before, hugepg_free_after)
                else:
                    logging.error("instance has consumed invalid hugepages")
                    logging.error("Test case 3 failed")
                    message= "instance has valid hugepages {} and consumed invalid hugepages before {} after {} , should consume 4".format(hgpages[1], hugepg_free_before, hugepg_free_after)

            else: 
                logging.error("Instance has invalid hugepage size {}".format(output))
                logging.error("Test case 3 failed")
                message="new instance has invalid hugepages"
        else:
            logging.error("server build failed")
            logging.error("Test case 3 failed")
            message="server creation failed"
        
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(10)
    except Exception as e:
        logging.error("Hugepage Test case 3 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 3 failed/ error occured"
    return isPassed, message

def hugepages_test_case_4(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    # Search and Create Flavor
    isPassed= False
    message=""
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 2048)

    #search and create server
    try:
        server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id])
        server_status= check_server_status(nova_ep, token, server_id)
        if image_id is not None or server_status == "error":
            logging.info("Image created and server built failed")
            logging.info("Testcase 4 passed")
            isPassed= True
            message="2MB hugepage flavor successfully created on 1GB deployment but instance failed, image id is: {} instance state is: {}".format(image_id, server_status)
        else:
            logging.info("Image created and server is active")
            message= "image creation failed or server is active with 2mb hgpage on 1GB hupage deployment, image id is: {} instance state is: {}".format(image_id, server_status)
            logging.error("Testcase 4 Failed ")
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(10)
    except Exception as e:
        logging.error("Hugepage Test case 4 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 4 failed/ error occured"
    return isPassed, message    
    
def hugepages_test_case_6(nova_ep, neutron_ep, glance_ep, token, settings):
  
    command= "sudo grep enabled_filters /var/lib/config-data/nova_libvirt/etc/nova/nova.conf"
    compute_nodes_ip= ["192.168.10.1", "192123", "44"]
    for node in compute_nodes_ip:
        ssh_output= ssh_into_node("", command)
        ssh_output= ssh_output.read().decode('ascii')
        ssh_output= ssh_output.split('=')
        if ( "RetryFilter" not in ssh_output[1] or "AvailabilityZoneFilter" not in ssh_output[1] or "RamFilter" not in ssh_output[1] or 
                "DiskFilter" not in ssh_output[1] or "ComputeFilter"  not in ssh_output[1] or "ComputeCapabilitiesFilter"  not in ssh_output[1] or 
                "ImagePropertiesFilter" not in ssh_output[1] or "ServerGroupAntiAffinityFilter" not in ssh_output[1] or "ServerGroupAffinityFilter" not in ssh_output[1] or 
                "CoreFilter" not in ssh_output[1] or "NUMATopologyFilter" not in ssh_output[1] or "AggregateInstanceExtraSpecsFilter" not in ssh_output[1]):
            logging.error("nova.conf file is not correctly configured on compute node {}".format(node))
            logging.error("Testcase 6 Failed")
            return False
        else: 
            logging.info("nova.conf file is not correctly configured on all compute nodes")
            logging.info("Testcase 6 Passed")
            return True

def hugepages_test_case_7_and_8(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):

    isPassed7= isPassed8= isPassed8_1=isPassed8_2=isPassed8_3= False
    message7=message8=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    output= ssh_into_node(compute0_ip, " grep Huge /proc/meminfo")
    hugepg_free= parse_hugepage_size(output, "HugePages_Free:")
    print(hugepg_free)
    instance_possible= math.floor(int(hugepg_free)/20)
    print(instance_possible)
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 20480, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)
    server_ids=[]
    try:
        for instance in range (0, instance_possible):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0 )
            server_ids.append(server_id)
    except:
        pass
    server_build_wait(nova_ep, token, server_ids)

    #Check status of instances
    for server_id in server_ids:
        server_status= check_server_status(nova_ep, token, server_id)
        if (server_status)=="error":
            logging.error("server creation failed")
            logging.error("TestCase 7 and 8 failed")
            message7="instance creation failed"
            message8="instance creation failed"
            return False, message7, False, message8
    else:
        logging.info("all servers successfully created")
        try:   
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        except:
            logging.info("Test Case 7 and 8 Failed")
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            for server_id in server_ids:   
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            time.sleep(20)
            pass
            return False
        server_build_wait(nova_ep, token, [server_id])
        server_status= check_server_status(nova_ep, token, server_id)
        if (server_status== "error"):
            logging.info("Test case 7 Passed Successfully")
            message7= ("Test case 7 Passed Successfully, instance creation failed when all hugepages are consumed")
            isPassed7= True
        
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        
        #pause all instances  
        #Chck when all inastances are paused
        for server_id in server_ids:   
            perform_action_on_server(nova_ep,token, server_id, "pause")
        wait_server_pause(nova_ep, token, server_ids)
        logging.info("all Servers Paused")
        logging.info("again creating server")
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_id])
        server_status= check_server_status(nova_ep, token, server_id)
        if (server_status== "error"):
            isPassed8_1=True
            logging.info("Server Creation Failed when other servers paused")
            logging.info("Test case 8 passed when other servers are paused")
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        
        logging.info("unpause servers")
        for server_id in server_ids:   
            perform_action_on_server(nova_ep,token, server_id, "unpause")
        server_build_wait(nova_ep, token, server_ids)
        logging.info("All servers unpaused")

    #Check when all instances are suspended
    for server_id in server_ids:   
        perform_action_on_server(nova_ep,token, server_id, "suspend")
    wait_server_suspend(nova_ep, token, server_ids)
    logging.info("all Servers suspended")
    logging.info("again creating server")
    server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
    server_build_wait(nova_ep, token, [server_id])
    server_status= check_server_status(nova_ep, token, server_id)
    if (server_status== "error"):
        logging.info("Server Creation Failed when other servers suspended")
        logging.info("Test case 8 passed when other servers are suspended")
        isPassed8_2=True
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        
    for server_id in server_ids:   
        perform_action_on_server(nova_ep,token, server_id, "resume")
    server_build_wait(nova_ep, token, server_ids)
    logging.info("All servers resumed")

    #Check when all instances are shutdown
    for server_id in server_ids:   
        perform_action_on_server(nova_ep,token, server_id, "os-stop")
    wait_server_shutdown(nova_ep, token, server_ids)
    logging.info("all Servers shutdown")
    logging.info("again creating server")
    server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
    server_build_wait(nova_ep, token, [server_id])
    server_status= check_server_status(nova_ep, token, server_id)
    if (server_status== "error"):
        logging.info("Server Creation Failed when other servers shutdown")
        logging.info("Test case 8 passed when other servers are shutdown")
        isPassed8_3=True
    if isPassed8_1== True and isPassed8_1== True and isPassed8_3== True:
        isPassed8= True
        message8="Instance creation failed when all hugepages are consumed, when all hosts are suspended, paused or shutdown"
    try:
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        for server_id in server_ids:   
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(20)
    except: 
        pass
    return isPassed7, message7, isPassed8, message8

def hugepages_test_case_9(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""
    try:
        flavor_1_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 2048, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_1_id, False, 1048576)
        flavor_2_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_2", 4096, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_2_id, False, 1048576)
        
        server_id= search_and_create_server(nova_ep, token, "testcase_server", image_id,settings["key_name"], flavor_1_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id]) 
        response =resize_server(nova_ep,token, server_id, flavor_2_id)
        if response==(202):
            isPassed= True
            logging.info("Sccessfully Migrated")
            logging.info("Test Case 9 Passed")
            message= "migration of server from one flavor to other with different ram is successfull, response coder is: {}".format(response)
        else: 
            logging.info("Migration Failed")
            logging.error("Test Case 9 Failed")
            message="migration of server from one flavor to other with different ram is failed, response coder is: {}".format(response)
        logging.info("deleting flavors")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
        logging.info("deleting all servers")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(10)
    except Exception as e:
        logging.error("Hugepage Test case 9 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 9 failed/ error occured"
    return isPassed, message

def hugepages_test_case_10(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 22528, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)
        ssh_output= ssh_into_node(compute0_ip, "grep MemTotal: /proc/meminfo")
        print(ssh_output)
        ssh_output=ssh_output.split("       ")
        ssh_output=ssh_output[1].split(" ")
        available_ram= int(ssh_output[0])/(1024*1024)
        print(available_ram)
        instance_possible= math.floor(int(available_ram)/22)
        print(instance_possible)
        #ssh_output=ssh_output.strip(" ")
        server_ids=[]
        for instance in range (0, instance_possible):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
            server_ids.append(server_id)
        server_build_wait(nova_ep, token, server_ids)
        successfully_created=0
        for i in range(0,instance_possible):
            status= check_server_status(nova_ep, token, server_ids[i])
            if status=="active":
                successfully_created=successfully_created+1
        if(successfully_created >(instance_possible-3) and successfully_created<instance_possible):
            isPassed= True
            logging.info("servers created according to available memory")
            logging.info("Test Case 10 Passed")
            message="servers are  created according to available memory, possible {}, created {}, ram is: {}, atleast should be created {}".format(instance_possible, successfully_created, available_ram, (instance_possible-3) )
        else:
            logging.info("servers are not created according to available memory")
            logging.info("Test Case 10 Failed")
            logging.info("deleting flavor")
            message="servers are  not created according to available memory, possible {}, created {}, ram is: {}, atleast should be created {}".format(instance_possible, successfully_created, available_ram, (instance_possible-3))
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        for server_id in server_ids:   
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(20)
    except Exception as e:
        logging.error("Hugepage Test case 10 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 10 failed/ error occured"
    return isPassed, message

def hugepages_test_case_11(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 28, 60)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_id])
    server_ip= get_server_ip(nova_ep, token, server_id, settings["network1_name"])
    logging.info("Server 1 Ip is: {}".format(server_ip))
    server_port= get_ports(neutron_ep, token, network_id, server_ip)
    logging.info("Server 1 Port is: {}".format(server_port))
    public_network_id= search_network(neutron_ep, token, "public")
    public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
    time.sleep(90)
    create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
    logging.info("Waiting for server to boot")
    time.sleep(90)
    server_floating_ip= get_server_floating_ip(nova_ep, token, server_id, settings["network1_name"])
    response = os.system("ping -c 3 " + server_floating_ip)
    if response == 0:
        isPassed= True
        logging.info ("Ping successfull!")
        logging.info("Test Case 11 Passed")
    else:
        logging.info ("Ping failed")
        logging.error("Test Case 11 Failed")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed



    












