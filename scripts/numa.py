from openstack_functions import *
from hugepages import wait_server_pause, wait_server_suspend, wait_server_shutdown, wait_server_delete
import logging
import math
from volume import *
import subprocess
def parse_vcpus(output): 
    output= output.split('>')
    return output[1][0]


def numa_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    logging.info("Test Case 3 running")
    isPassed= False
    message=flavor_id=server_id="" 
    try:
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0_ip= compute0_ip[0]
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 4096, 4, 10)
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
            output=output[0]
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
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_id != ""):
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    except Exception as e:
        logging.error("Test Case 3 failed")
        message="numa testcase 3 failed/ error occured"
        logging.exception(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_id != ""):
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    logging.info("testcase 3 finished")  
    return isPassed, message
    
def numa_test_case_5_6_9(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    logging.info("testcase 6 starting")  
    isPassed5=isPassed6=isPassed9= isPassed9_1=isPassed9_2= isPassed9_3= False
    message5= message6= message9=flavor_id=""
    server_ids=[]
    try: 
        compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0_ip= compute0_ip[0]
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 4096, 20, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        
        #find cpus of compute node
        cpu_cores= ssh_into_node(compute0_ip, "lscpu | grep  'CPU(s):' ")
        cpu_cores= cpu_cores[0]
        cpu_cores= cpu_cores.split("\n")
        cpu_cores= cpu_cores[0].split(":")
        cpu_cores= cpu_cores[1].strip()
        instance_possible=  math.floor(int(cpu_cores)/20)
        for instance in range (0, (instance_possible+1)):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0 )
            server_ids.append(server_id)
        server_build_wait(nova_ep, token, server_ids)
        flag=True
        count=0
        for i in range (0,instance_possible):
            status= check_server_status(nova_ep, token, server_ids[i])
            if(status != "active"):
                flag== False

        status= check_server_status(nova_ep, token, server_ids[-1])
        if (status=="error" and flag==True):
            isPassed5=isPassed6= True
            logging.info("Numa testcase 6 passed")
            message6="Numa testcase 6 passed, testcase created valid number of instances, instance_possible {}, instance created {}, last instance status is {}, it should be in error state, all other instances are active: {}".format(instance_possible, len(server_ids) ,status, flag)
            message5="Numa testcase 5 passed, testcase created valid number of instances, no new instance created when all cpus consumed, instance_possible {}, instance created {}, last instance status is {}, it should be in error state, all other instances are active: {}".format(instance_possible, len(server_ids) ,status, flag)
            logging.info("deleting extra server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[-1]), token)
            del server_ids[-1]

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
                isPassed9_1=True
                logging.info("Server Creation Failed when other servers paused")
                logging.info("Test case 9 passed when other servers are paused")
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
                isPassed9_2=True
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
                logging.info("Test case 9 passed when other servers are shutdown")
                isPassed9_3=True

            
            if isPassed9_1== True and isPassed9_2== True and  isPassed9_3== True:
                isPassed9=True
                message9="Numa testcase 9 passed, no instance created after all cpus are consumed, when all servers are paused or suspended or shutdown"
            else: 
                message9="Numa testcase 9 failed, new instance created after all cpus are consumed, when all servers are paused or suspended or shutdown"

        else:
            logging.info("Numa testcase 6 failed")
            message6="Numa testcase 6 failed, testcase did not created valid number of instances , instance_possible {},  instance created {}, last instance status is {},  it should be in error state, all other instances are active: {}".format(instance_possible, len(server_ids), status, flag)
            message5="Numa testcase 5 failed, testcase did not created valid number of instances when all cpus are consumed , instance_possible {},  instance created {}, last instance status is {},  it should be in error state, all other instances are active: {}".format(instance_possible, len(server_ids), status, flag)
            message9="Numa testcase 9 failed, can not check instance creation after all cpus are consumed, when all servers are paused or suspended or shutdown, because instace creation is not valid "
        logging.info("deleting flavor")
        delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("deleting all servers")
        for server_id in server_ids:   
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        time.sleep(20)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    except Exception as e:
        logging.error("Test Case 6 failed")
        message6=message5=message9="numa testcase  failed/ error occured"
        logging.exception(e)
        for server_id in server_ids:   
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("testcase 6 finished")  
    return isPassed5, message5, isPassed6, message6, isPassed9, message9

def numa_test_case_7(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    logging.info("testcase 7 starting")  
    isPassed= False
    message=flavor_id=""
   
    try:
        compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0_ip= compute0_ip[0]
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 4096, 4, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server_ids=[]
        for i in range (0,2):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(i), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
            server_ids.append(server_id)
        server_build_wait(nova_ep, token, server_ids) 
        
        instance_1_name= get_server_instance_name(nova_ep, token, server_ids[0])
        output1= ssh_into_node(compute0_ip, " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_1_name))
        output1= output1[0].split("'")
        output1= output1[1].split(",")
        instance_2_name= get_server_instance_name(nova_ep, token, server_ids[1])
        output2= ssh_into_node(compute0_ip, " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_2_name))
        output2= output2[0].split("'")
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
        if(flavor_id!=""):
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
        if(flavor_id!=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        
    logging.info("testcase 7 finished")  
    return isPassed, message
    
def numa_test_case_8(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message= flavor_id=""
    logging.info("testcase 8 starting") 
    
    try:
        compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
        compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0= compute0[0]
        compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
        compute0_ip= compute0_ip[0]
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 4096, 4, 40)
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
            output1= output1[0].split("'")
            output1= output1[1].split(",")

            instance_2_name= get_server_instance_name(nova_ep, token, server_ids[1])
            output2= ssh_into_node(compute0_ip, " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_2_name))
            output2= output2[0].split("'")
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
        
        if(flavor_id!=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[0]), token)
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[1]), token)
        time.sleep(10)
    except Exception as e:
        logging.error("Test Case 8 failed")
        message="numa testcase 8 failed/ error occured"
        logging.exception(e)
        if(flavor_id!=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        logging.info("testcase 8 finished") 
    return isPassed, message

def numa_test_case_10(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    message=flavor_1_id=flavor_2_id=server_id=""
    logging.info("testcase 10 starting") 
    try:   
        flavor_1_id= search_and_create_flavor(nova_ep, token, "numa_flavor1", 4096, 4, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_1_id, True)
        flavor_2_id= search_and_create_flavor(nova_ep, token, "numa_flavor2", 4096, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_2_id, True)
        server_id= search_and_create_server(nova_ep, token, "testcase_server1", image_id,settings["key_name"], flavor_2_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_id]) 
        status= check_server_status(nova_ep, token, server_id)  
        if(status== "active"):
            response= resize_server(nova_ep,token, server_id, flavor_1_id)
            time.sleep(10)
            if response==(202):
                isPassed= True
                logging.info("Sccessfully Migrated")
                logging.info("Test Case 10 Passed")
                message="Test Case 10 Passed, server successfully resized, return code is: {}".format(response)
            else: 
                logging.info("Migration Failed")
                logging.error("Test Case 10 Failed")
                message="Test Case 10 failed, server failed to resiz, return code is: {}".format(response)            
        else:
            logging.error("Test Case 10 Failed")
            message="Test Case 10 failed, server creation failed, its status is: {}".format(status)
        if(flavor_1_id!=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
        if(flavor_2_id!=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
        if (server_id != ""):
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)

    except Exception as e:
        logging.error("Test Case 10 failed")
        message="numa testcase 10 failed/ error occured"
        logging.exception(e)
        if(flavor_1_id!=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
        if(flavor_2_id!=""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
        if (server_id != ""):
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    logging.info("testcase 10 finished") 
    return isPassed, message
    
def numa_test_case_11(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""  
    server_1_id=server_floating_ip_id=flavor_id=""   
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 2048, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        #search and create server
        compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
        compute1= compute1[0]
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error":
            logging.error("Test Case 11 failed")
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
                    logging.info("numa test Case 1 Passed")
                    message="numa numa 1 passed, cold migration of instance is successfull, status code is {}, old host {}, new host {} \n, ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("numa test Case 1 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "hugnumaepage test Case 11 failed, ping failed after cold migration, status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("numa test Case 11 failed, cold vmigration of instance failed, status code is {}, old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="numa test Case 11 failed, cold migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host)
        
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
        logging.exception("numa test Case 11 failed/ error occured")
        message="numa testcase 11 failed/ error occured {}".format(e)
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
    logging.info("numa Test Case 11 finished")
    return isPassed, message

def numa_test_case_12(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    logging.info("testcase 12 started") 
    isPassed=False
    message=flavor_id=server_id=server_floating_ip_id=""
    try:
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 4096, 28, 60)
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

        else:
                logging.error("Numa Test Case 12 Failed, server creation failed")
                message="Test Case 12 failed, server creation failed, its status is: {}".format(status)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)  
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(server_floating_ip_id != ""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)

    except Exception as e:
        logging.error("Test Case 12 failed")
        message="numa testcase 12 failed/ error occured"
        logging.exception(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)  
        if(server_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        if(server_floating_ip_id != ""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    logging.info("testcase 12 finished") 
    return isPassed, message
def numa_test_case_13(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    message=""  
    server_1_id=server_floating_ip_id=flavor_id=""   
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 2048, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
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
                    logging.info("numa test Case 13 Passed")
                    message="numa testcase 13 passed, live migration of instance is successfull, status code is {}, old host {}, new host {}  \n , ping status is: \n {}".format(response, compute1, new_host, stdout)
                else:
                    logging.error("numa test Case 13 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout))
                    message= "numa test Case 13 failed, ping failed after live migration,  status code is {}, old host name is {}, new host name is : {} \n ping status is: \n {}".format(response, compute1, new_host, stdout)
            else:
                logging.error("numa test Case 13 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, ))
                message="numa test Case 13 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {} ".format(response, compute1, new_host, )
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
        logging.exception("numa test Case 13 failed/ error occured")
        message="numa testcase 13 failed/ error occured {}".format(e)
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
    logging.info("numa Test Case 13 finished")
    return isPassed, message

def numa_volume_test_case(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_node_ips, network1_id, security_group_id, image_id):
    message=""
    testcases_passed= 0
    logging.info("starting volume testcases")
    server1_id=floating_1_ip_id=flavor_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]

    
    try:
        flavor_id= search_and_create_flavor(nova_ep, token, "numa_flavor", 2048, 2, 40)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id, network1_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if status1 == "active":
            server1_ip= get_server_ip(nova_ep, token, server1_id, settings["network1_name"])
            server1_port= get_ports(neutron_ep, token, network1_id, server1_ip)
            public_network_id= search_network(neutron_ep, token, settings["external_network_name"])
            public_subnet_id= search_subnet(neutron_ep, token, settings["external_subnet"])
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
            testcases_passed, message= volume_test_cases(cinder_ep, keystone_ep, nova_ep, token, settings, baremetal_node_ips, server1_id, flaoting_1_ip,  flavor_id, network1_id, security_group_id, compute1) 
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
