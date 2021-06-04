from openstack_functions import *
import logging
import paramiko
import time
import math
import subprocess
from volume import *
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
            ssh_output= ssh_output[0]
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
            ssh_output= ssh_output[0]
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
    message=server_id=flavor_id=""
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 4096, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)
    #search and create server
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        output= ssh_into_node(compute0_ip, " grep Huge /proc/meminfo")
        output=output[0]
        hugepg_free_before= parse_hugepage_size(output, "HugePages_Free:")
        server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_id])  
        if( check_server_status(nova_ep, token, server_id)== "active"):
            instance_name= get_server_instance_name(nova_ep, token, server_id)
            command= "sudo cat /etc/libvirt/qemu/{}.xml | grep 'page size'".format(instance_name)
            output= ssh_into_node(compute0_ip, command)
            output=output[0]
            hgpages= output.split("'")
            logging.info("Instance hugepage size is: {}".format(output[1]))
            if hgpages[1]=="1048576":
                logging.info("Instance has valid hugepage size")
                output= ssh_into_node(compute0_ip, " grep Huge /proc/meminfo")
                output=output[0]
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
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)     
    except Exception as e:
        logging.error("Hugepage Test case 3 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 3 failed/ error occured"
        message="server creation failed"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    return isPassed, message

def hugepages_test_case_4(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    # Search and Create Flavor
    isPassed= False
    message=server_id=flavor_id=""
    #search and create server
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 4096, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 2048)
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
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)    
    except Exception as e:
        logging.error("Hugepage Test case 4 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 4 failed/ error occured"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    return isPassed, message    
    
def hugepages_test_case_6(nova_ep, neutron_ep, glance_ep, token, settings):
  
    command= "sudo grep enabled_filters /var/lib/config-data/nova_libvirt/etc/nova/nova.conf"
    compute_nodes_ip= ["192.168.10.1", "192123", "44"]
    for node in compute_nodes_ip:
        ssh_output= ssh_into_node("", command)
        ssh_output=ssh_output[0]
        #ssh_output= ssh_output.read().decode('ascii')
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
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0_ip= compute0_ip[0]
        output= ssh_into_node(compute0_ip, " grep Huge /proc/meminfo")
        output=output[0]
        hugepg_free= parse_hugepage_size(output, "HugePages_Free:")
        print(hugepg_free)
        instance_possible= math.floor(int(hugepg_free)/20)
        print(instance_possible)
        flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 20480, 2, 40)
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
                pass
                return False, message7, False, message8
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
            isPassed8_2=True
            
        logging.info("deleting server")
        if( server_id!= ""):
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
        if isPassed8_1== True and isPassed8_2== True and isPassed8_3== True:
            isPassed8= True
            message8="Instance creation failed when all hugepages are consumed, when all hosts are suspended, paused or shutdown"
        try:
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            if( server_id!= ""):
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            for server_id in server_ids: 
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        except: 
            pass
    except Exception as e:
        logging.error("hugepage testcase 7 and 8 failed/ error occured")
        message="hugepage testcase 7 and 8 failed/ error occured"
    return isPassed7, message7, isPassed8, message8
def hugepages_test_case_9(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=server_id=flavor_1_id=flavor_2_id=""
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
            logging.info("Sccessfully resized server")
            logging.info("Test Case 9 Passed")
            message= "migration of server from one flavor to other with different ram is successfull, response coder is: {}".format(response)
        else: 
            logging.info("Migration Failed")
            logging.error("Test Case 9 Failed")
            message="migration of server from one flavor to other with different ram is failed, response coder is: {}".format(response)
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_1_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
        if(flavor_2_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
    except Exception as e:
        logging.error("Hugepage Test case 9 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 9 failed/ error occured"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_1_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
        if(flavor_2_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
    return isPassed, message

def hugepages_test_case_10(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    server_ids=[]
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 22528, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)
        ssh_output= ssh_into_node(compute0_ip, "grep MemTotal: /proc/meminfo")
        ssh_output=ssh_output[0]
        print(ssh_output)
        ssh_output=ssh_output.split("       ")
        ssh_output=ssh_output[1].split(" ")
        available_ram= int(ssh_output[0])/(1024*1024)
        print(available_ram)
        instance_possible= math.floor(int(available_ram)/22)
        print(instance_possible)
        #ssh_output=ssh_output.strip(" ")
        
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
    except Exception as e:
        logging.error("Hugepage Test case 10 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 10 failed/ error occured"
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        for server_id in server_ids:   
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    return isPassed, message

def hugepages_test_case_11(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=server_id=server_floating_ip=flavor_id=""
    # Search and Create Flavor
    try: 
        flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 4096, 28, 60)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id])
        server_ip= get_server_ip(nova_ep, token, server_id, settings["network1_name"])
        logging.info("Server 1 Ip is: {}".format(server_ip))
        server_port= get_ports(neutron_ep, token, network_id, server_ip)
        logging.info("Server 1 Port is: {}".format(server_port))
        public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
        time.sleep(10)
        logging.info("Waiting for server to boot")
        server_floating_ip= get_server_floating_ip(nova_ep, token, server_id, settings["network1_name"])
        response = os.system("ping -c 3 " + server_floating_ip)
        if response == 0:
            isPassed= True
            logging.info ("Ping successfull!")
            logging.info("Test Case 11 Passed")
            message="hugepage test case 11 passed, instance creatred and pinged sucessfully "
        else:
            logging.info ("Ping failed")
            logging.error("Test Case 11 Failed")
            message="hugepage test case failed, instance creatred and ping failed "
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_floating_ip !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip), token)
    except Exception as e:
        logging.error("Hugepage Test case 11 failed/ error occured")
        logging.exception(e)
        message= "Hugepage Test case 11 failed/ error occured"
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_floating_ip !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip), token)

    
    return isPassed, message

def hugepages_test_case_12(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""  
    server_1_id=server_floating_ip_id=flavor_id=""   
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 2048, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576) 
        #search and create server
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error":
            logging.error("Test Case 12 failed")
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
            time.sleep(30)
            if response==202:
                logging.info("confirming migration")
                perform_action_on_server(nova_ep,token, server_1_id, "confirmResize")

            logging.info("migration status code is: {}".format(response))
            logging.info("waiting for migration")
            time.sleep(30)
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
                    logging.info("hugepage test Case 12 Passed")
                    message="hugepage testcase 12 passed, cold migration of instance is successfull, status code is {}, old host {}, new host {} \n, ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("hugepage test Case 12 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "hugepage test Case 12 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("hugepage test Case 12 failed, cold vmigration of instance failed, status code is {}, old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="hugepage test Case 12 failed, cold migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host)
        
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token) 
    except Exception as e:
        logging.exception("hugepage test Case 12 failed/ error occured")
        message="hugepage testcase 12 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token) 
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)   
    logging.info("hugepage Test Case12 finished")
    return isPassed, message

def hugepages_test_case_13(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""  
    server_1_id=server_floating_ip_id=flavor_id=""   
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 2048, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576) 
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        compute2 =  [key for key, val in baremetal_node_ips.items() if "compute-2" in key]
        compute2= compute2[0]
        #search and create server
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error":
            logging.error("Test Case 13 failed")
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
                    logging.info("hugepage test Case 13 Passed")
                    message="hugepage testcase 13 passed, live migration of instance is successfull, status code is {}, old host {}, new host {}  \n , ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("hugepage test Case 13 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "hugepage test Case 13 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("hugepage test Case 13 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, ))
                message="hugepage test Case 13 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, )
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token) 
    except Exception as e:
        logging.exception("hugepage test Case 13 failed/ error occured")
        message="hugepage testcase 13 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_floating_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token) 
    logging.info("hugepage Test Case 13 finished")
    return isPassed, message

def hugepages_volume_test_case(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_node_ips, network1_id, security_group_id, image_id):
    message=""
    testcases_passed= 0
    logging.info("starting volume testcases")
    server1_id=floating_1_ip_id=flavor_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]

    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "hugepage_flavor", 2048, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)
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
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token) 
    except Exception as e:
        logging.exception(e)
        message= "volume testcases skipped, error/exception occured {}".format(str(e))
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token) 
        if(floating_1_ip_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(flavor_id !=""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token) 
    return testcases_passed, message













