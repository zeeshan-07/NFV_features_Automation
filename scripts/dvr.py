from openstack_functions import *
import logging
import paramiko
import os
import time
import subprocess
from threading import Thread
import queue
from volume import *
que = queue.Queue()



 
def listen_tcpdump(host_ip, namespace, namespace_type):
    try:
        print("ns is: {}".format(namespace))
        logging.info("Trying to connect with node {}".format(host_ip))
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session = ssh_client.connect(host_ip, username="heat-admin",key_filename=os.path.expanduser("~/.ssh/id_rsa"))  # noqa
        logging.info("SSH Session is established")
        logging.info("Running command in server {}".format(host_ip))
        channel = ssh_client.get_transport().open_session()
        channel.invoke_shell()
        channel.send("sudo ip netns exec {} /bin/bash\n".format(namespace))
        time.sleep(5)        
        channel.send("ip a\n")
        time.sleep(5)
        interfaces= channel.recv(9999)
        interfaces= interfaces.decode("utf-8") 
        interfaces= interfaces.split("\n")
        listen_interfaces=[]
        string_to_search=""
        if(namespace_type=="qrouter"):
            string_to_search= "rfp-"
        if(namespace_type=="floating_ip"):
            string_to_search= "fg-"
        if(namespace_type=="snat"):
            string_to_search= "qg-"

        logging.info("available interfaces are: ")
        for interface in interfaces:
            logging.info(interface)
            if string_to_search in interface[0:10]: 
                logging.info(interface)
                interface= interface.split(':')
                interface= interface[1]
                if "@" in interface:
                    interface= interface.split('@')
                    interface= interface[0]
                listen_interfaces.append(interface)
        
        logging.info("Interfaces to listen are: {}".format(listen_interfaces))
        tcpdump_result=[]
        for listen_interface in listen_interfaces:
            logging.info("lisening to interface "+ listen_interface)
            channel.sendall("timeout 10 tcpdump -i {}\n".format(listen_interface))
            time.sleep(5)
            tcpdump= channel.recv(9999)
            logging.info("tcpdump results: {}".format(tcpdump))
            tcpdump_result.append(tcpdump)
        return_result=""
        temp_result=""
        icmp_received= ""
        for result in tcpdump_result:
            if "ICMP echo reply" in result.decode("utf-8") and "ICMP echo request" in result.decode("utf-8"):
                logging.info("ICMP packet received")
                result.decode("utf-8")
                return_result=result.decode("utf-8")
                temp_result= temp_result+result.decode("utf-8")
                print("Temp Result is: "+ temp_result)
                icmp_received=True
                break
        else:
            logging.info("No ICMP packet received")
            return_result= temp_result
            icmp_received=False
        que.put(icmp_received)
        que.put(return_result )
        return icmp_received, return_result
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        ssh_client.close()
        logging.info("Connection from client has been closed")  

def ssh_conne(server1, server2, settings):
    try:
        command= "ping -c 50 {}".format(server2)
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
        que.put(error)
        return output, error
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        client.close()
        logging.info("Connection from client has been closed")  
  
def dvr_test_case_1(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute1_ip =  [val for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1_ip= compute1_ip[0]
    command="ip netns |grep qrouter"
    oldspaces= ssh_into_node(compute1_ip, command)
    oldspaces= oldspaces[0]
    oldspaces= oldspaces.split('\n')
    print("length is {}".format(len(oldspaces)))
    print(oldspaces)
    server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
    server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute1)

    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id) 


    if status1== "active":
        newspaces= ssh_into_node(compute1_ip, command)
        newspaces= newspaces[0]
        newspaces= newspaces.split('\n')
        print("length is {}".format(len(newspaces)))
        print(newspaces)

        different_qrouterspace = np.setdiff1d(newspaces,oldspaces)
        different_qrouterspace= different_qrouterspace[0].split(' ')
        server_1_qrouter_space= different_qrouterspace[0]
        print("New qrouter space is: {} ".format(server_1_qrouter_space))

        print(newlist)
    else:
        print("Server creation failed")
    
    return "s", "b"

def dvr_test_case_7(baremetal_nodes_ips):
    message=""
    #GET DVR status from controller nodes
    command= "sudo cat /var/lib/config-data/puppet-generated/neutron/etc/neutron/l3_agent.ini | grep dvr"
    controller_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "controller" in key]
    message= "DVR status is: "
    try:
        for node in controller_nodes_ip:
            ssh_output= ssh_into_node(node, command)
            logging.info("agent mode of  controller node {}, is {}".format(node, ssh_output[0].strip()))
            message= message+ " node {} agent mode: {} ".format(node, ssh_output[0].strip())
            if ssh_output[0].strip() != "agent_mode=dvr_snat":
                logging.info("Controller node {} do not have DVR agent mode, agent mode is: {}".format(node, ssh_output))
                logging.error("Testcase 7 failed")
                return False, message
                break
        else:
            logging.info("All controller nodes have DVR_SNAT aget mode")
            logging.info("Testcase 7 Passed")
            message= "DVR testcase 7 passed all controller nodes have dvr_snat agent mode"+ message
            return True, message
    except Exception as e:
        logging.error("DVR Test case 7 failed/ error occured")
        message= message+ "DVR Test case 7 failed/ error occured"
        logging.exception(e)
        return False, message
def dvr_test_case_8(baremetal_nodes_ips):
    message=""
    #GET DVR status from compute nodes
    command= "sudo cat /var/lib/config-data/puppet-generated/neutron/etc/neutron/l3_agent.ini | grep dvr"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    message= "DVR status is: "
    try:
        for node in compute_nodes_ip:
            ssh_output= ssh_into_node(node, command)
            logging.info("agent mode of  compute node {}, is {}".format(node, ssh_output[0].strip()))
            message= message+ " node {} agent mode: {} ".format(node, ssh_output[0].strip())
            if ssh_output[0].strip() != "agent_mode=dvr":
                logging.info("compute node {} do not have DVR agent mode, agent mode is: {}".format(node, ssh_output))
                logging.error("Testcase 8 failed")
                return False, message
                break
        else:
            logging.info("All compute nodes have DVR aget mode")
            logging.info("Testcase 8 Passed")
            message= "DVR testcase 8 passed all compute nodes have dvr agent mode"+ message
            return True, message
    except Exception as e:
        logging.error("DVR Test case 8 failed/ error occured")
        message= message+ " DVR Test case 8 failed/ error occured"
        logging.exception(e)
        return False, message

def dvr_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, router_id, security_group_id, image_id, flavor_id):
    logging.info("DVR testcase 12 started")
    controller0_ip=  [val for key, val in baremetal_node_ips.items() if "controller-0" in key]
    controller0_ip= controller0_ip[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id=""
    try:
        
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network2_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id) 
        status2= check_server_status(nova_ep, token, server_2_id)
        if status1== "active" and status2== "active":
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
            server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server2_port= get_ports(neutron_ep, token, network2_id, server2_ip)
            flaoting_1_ip, floating_1_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
            flaoting_2_ip, floating_2_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)

            logging.info("Waiting for server to boot")
            s1_wait= wait_instance_boot(flaoting_1_ip)
            s2_wait= wait_instance_boot(flaoting_2_ip)
            s2_ssh_wait= wait_instance_ssh(flaoting_2_ip, settings)
            print("ping ssh 1: {}".format(s1_wait))
            print("wait ssh is: {}".format(s2_ssh_wait))
            if s1_wait== True and s2_wait== True and s2_ssh_wait== True:
                #get namspaces
                #router namespace
                router_namespace= "qrouter-"+router_id
                logging.info("Qrouter namespace is: {}".format(router_namespace))
                logging.info("starting threads")
                p1= Thread(target=ssh_conne, args=(flaoting_2_ip, flaoting_1_ip, settings,))
                p2= Thread(target=listen_tcpdump, args=(controller0_ip, router_namespace, "qrouter" ))
                p2.start()
                p1.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()
                icmp_check= que.get()
                tcpdump_message= que.get()
                ping_status= que.get()
                if ping_status=="":
                    if(icmp_check== False):
                        isPassed= True
                        logging.info("DVR testcase 10 passed, icmp is not received on controller (bypassed) qrouter  namespace when both instances each other on different network and different compute nodes")
                        message="DVR testcase 10 passed, icmp is not received on controller (bypassed) qrouter namespace when both instances each other on different network and different compute nodes, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                    else:    
                        message="DVR testcase 10 failed, icmp is  received on controller ( not bypassed) qrouter  namespace when both instances each other on different network and different compute nodes, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                        logging.error("DVR testcase 10 failed, icmp is  received on controller ( not bypassed) qrouter  namespace when both instances each other on different network and different compute nodes")
                else: 
                    message="DVR testcase 10 failed, failed and ping to google failed by instance "
                    logging.error("DVR testcase 10 failed, failed and ping instance floating ip from second instance")
            else:
                message="DVR testcase 10 failed, failed to ssh and ping server/s floating ip"
                logging.error("DVR testcase 10 failed, failed to ssh and ping server/s floating ip")
        else:
            logging.error("DVR testcase 10 failed, one of server creation failed")
            message="DVR testcase 10 failed, one of server creation failed, server 1 status is {} server 2 status is {}".format(status1, status2)

        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if server_2_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if floating_2_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    except Exception as e:
        logging.exception(e)
        message= message+ "DVR testcase 10 failed/ error occured: {}".format(e)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if server_2_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if floating_2_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("DVR testcase 10 finished")
    return isPassed, message

def dvr_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id, flavor_id):
    logging.info("DVR testcase 11 started")
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id=""
    controller_nodes_ip= [val for key, val in baremetal_node_ips.items() if "controller" in key]
    command= "sudo ip netns"
    node_selected=""
    try:
        for controller in controller_nodes_ip:
            namespaces= ssh_into_node(controller, command)
            if("snat-"  in namespaces[0]):
                node_selected= controller
                logging.info("controller node {}  have snat namespace {}".format(controller, namespaces[0]))
                break
        else:
            logging.info("No controller node have snat namespace")
            message= "No controller node have snat namespace"
        node_selected= controller_nodes_ip[1]
        if node_selected != "":
            logging.info("host selected for instance creation is {}".format(node_selected))
           
            server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
            server_build_wait(nova_ep, token, [server_1_id])
            status1= check_server_status(nova_ep, token, server_1_id) 
            if status1== "active":
                public_network_id= search_network(neutron_ep, token, "public")
                public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
                server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
                server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
                flaoting_1_ip, floating_1_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
                logging.info("Waiting for server to boot")
                s1_wait= wait_instance_boot(flaoting_1_ip)
                s1_ssh_wait= wait_instance_ssh(flaoting_1_ip, settings)
                print("ping ssh 1: {}".format(s1_wait))
                print("wait ssh is: {}".format(s1_ssh_wait))
                if s1_wait== True and s1_ssh_wait== True:
                    #get namspaces
                    #router namespace                    
                    logging.info("starting threads")
                    command="ip netns | grep snat"
                    snat_namespace= ssh_into_node(node_selected, command)
                    print("command output namespace: {}".format(snat_namespace))
                    snat_namespace= snat_namespace[0]
                    snat_namespace= snat_namespace.split(' ')
                    snat_namespace= snat_namespace[0]
                    logging.info("Floating Ip namespace is: {}".format(snat_namespace))
                    print("Sending namespace: {}".format(snat_namespace))
                    p1 = Thread(target=ssh_conne, args=(flaoting_1_ip, "8.8.8.8", settings,))
                    p2 = Thread(target=listen_tcpdump, args=(node_selected, snat_namespace, "snat" ))
                    p2.start()
                    p1.start()
                    logging.info("waiting for threads to finish")
                    p2.join()
                    p1.join()
                    icmp_check= que.get()
                    tcpdump_message= que.get()
                    ping_status= que.get()
                    if ping_status=="":
                        if(icmp_check== True):
                            isPassed= True
                            logging.info("DVR testcase 11 passed, icmp received received on controller  (not bypassed) snat  namespace when google is pinged from instance")
                            message="DVR testcase 11 passed, icmp is  received on controller (not bypassed) snat  namespace when google is pinged from instance, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                        else:    
                            message="DVR testcase 11 failed, icmp is not received on controller ( bypassed) snat  namespace when google is pinged from instance, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                            logging.error("DVR testcase 11 failed, icmp is not received on controller (bypassed) snat  namespace when google is pinged from instance")
                    else: 
                        message="DVR testcase 11 failed, failed and ping to google failed by instance "
                        logging.error("DVR testcase 11 failed, failed and ping instance floating ip from second instance")
                else:
                    message="DVR testcase 11 failed, failed to ssh and ping server/s floating ip"
                    logging.error("DVR testcase 11 failed, failed to ssh and ping server/s floating ip")
            else:
                logging.error("DVR testcase 11 failed, one of server creation failed")
                message="DVR testcase 11 failed, one of server creation failed, server 1 status is {}".format(status1)
            
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)        
    except Exception as e:
        logging.exception(e)
        message= message+ " DVR testcase 11 failed/ error occured: {}".format(e)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        time.sleep(2)
    logging.info("DVR testcase 11 finished")
    return isPassed, message

def dvr_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id, flavor_id):
    logging.info("DVR testcase 12 started")
    controller0_ip=  [val for key, val in baremetal_node_ips.items() if "controller-0" in key]
    controller0_ip= controller0_ip[0]
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id=""
    try:
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id) 
        if status1== "active":
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
            flaoting_1_ip, floating_1_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
            logging.info("Waiting for server to boot")
            s1_wait= wait_instance_boot(flaoting_1_ip)
            s1_ssh_wait= wait_instance_ssh(flaoting_1_ip, settings)
            print("ping ssh 1: {}".format(s1_wait))
            print("wait ssh is: {}".format(s1_ssh_wait))
            if s1_wait== True and s1_ssh_wait== True:
                #get namspaces
                #router namespace
                router_namespace= "qrouter-"+router_id
                logging.info("Qrouter namespace is: {}".format(router_namespace))
                logging.info("starting threads")
                p1 = Thread(target=ssh_conne, args=(flaoting_1_ip, "8.8.8.8", settings,))
                p2 = Thread(target=listen_tcpdump, args=(controller0_ip, router_namespace, "qrouter" ))
                p2.start()
                p1.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()
                icmp_check= que.get()
                tcpdump_message= que.get()
                ping_status= que.get()
                if ping_status=="":
                    if(icmp_check== False):
                        isPassed= True
                        logging.info("DVR testcase 12 passed, icmp is not received on controller (bypassed) qrouter  namespace when google is pinged from instance")
                        message="DVR testcase 12 passed, icmp is not received on controller (bypassed) qrouter  namespace when google is pinged from instance, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                    else:    
                        message="DVR testcase 12 failed, icmp is  received on controller ( not bypassed) qrouter  namespace when google is pinged from instance, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                        logging.error("DVR testcase 12 failed, icmp is  received on controller ( not bypassed) qrouter  namespace when google is pinged from instance")
                else: 
                    message="DVR testcase 12 failed, failed and ping to google failed by instance "
                    logging.error("DVR testcase 12 failed, failed and ping instance floating ip from second instance")
            else:
                message="DVR testcase 12 failed, failed to ssh and ping server/s floating ip"
                logging.error("DVR testcase 12 failed, failed to ssh and ping server/s floating ip")
        else:
            logging.error("DVR testcase 12 failed, one of server creation failed")
            message="DVR testcase 12 failed, one of server creation failed, server 1 status is {} ".format(status1)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        time.sleep(2)      
    except Exception as e:
        logging.exception(e)
        message= message+" DVR testcase 12 failed/ error occured: {}".format(e)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
    logging.info("DVR testcase 12 finished")
    return isPassed, message
def dvr_test_case_13(baremetal_nodes_ips):
    message=""
    command= "sudo cat /var/lib/config-data/puppet-generated/neutron/etc/neutron/neutron.conf |grep l3_ha"
    controller_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "controller" in key]
    message= "L3_ha values are: "
    try:
        for node in controller_nodes_ip:
            ssh_output= ssh_into_node(node, command)
            ssh_output= ssh_output[0]

            logging.info("l3_ha of controller node {}, is {}".format(node, ssh_output))
            message= message+ " l3_ha of controller node {}, is {}".format(node, ssh_output)
            if ssh_output != "l3_ha=False":
                logging.error("Controller node {} do not have l3_ha false".format(node))
                logging.error("DVR Testcase 13 failed")
                message= message+" DVR testcase 13 failed"
                return False, message
                break
        else:
            logging.info("All controller nodes have l3_ha false,")
            logging.info("DVR Testcase 13 Passed")
            message= "All controller nodes have l3_ha false "+message
            return True, message
    except Exception as e:
        logging.error("DVR Test case 13 failed/ error occurred")
        message=  "DVR Test case 13 failed/ error occurred " + message
        logging.exception(e)
        return False, message

def dvr_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id, flavor_id):
    logging.info("DVR testcase 16 started")
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id=""
    try:
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id) 
        if status1== "active":
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
            flaoting_1_ip, floating_1_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
            logging.info("Waiting for server to boot")
            s1_wait= wait_instance_boot(flaoting_1_ip)
            s1_ssh_wait= wait_instance_ssh(flaoting_1_ip, settings)
            print("ping ssh 1: {}".format(s1_wait))
            print("wait ssh is: {}".format(s1_ssh_wait))
            if s1_wait== True and s1_ssh_wait== True:
                #get namspaces
                #router namespace
                router_namespace= "qrouter-"+router_id
                logging.info("Qrouter namespace is: {}".format(router_namespace))
                logging.info("starting threads")
                p1 = Thread(target=ssh_conne, args=(flaoting_1_ip, "8.8.8.8", settings,))
                p2 = Thread(target=listen_tcpdump, args=(compute0_ip, router_namespace, "qrouter"))
                p2.start()
                p1.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()
                icmp_check= que.get()
                tcpdump_message= que.get()
                ping_status= que.get()
                if ping_status=="":
                    if(icmp_check== True):
                        isPassed= True
                        logging.info("DVR testcase 16 passed, icmp is received on compute qrouter  namespace when google is pinged from instance")
                        message="DVR testcase 16 passed, icmp is received on compute qrouter  namespace google is pinged from instance, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                    else:    
                        message="DVR testcase 16 failed, icmp is not received on compute qrouter  namespace when google is pinged from instance, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                        logging.error("DVR testcase 16 failed, icmp is not received on compute qrouter  namespace when google is pinged from instance")
                else: 
                    message="DVR testcase 16 failed, failed and ping instance floating ip from second instance"
                    logging.error("DVR testcase 16 failed, failed and ping instance floating ip from second instance")
            else:
                message="DVR testcase 16 failed, failed to ssh and ping server/s floating ip"
                logging.error("DVR testcase 16 failed, failed to ssh and ping server/s floating ip")
        else:
            logging.error("DVR testcase 16 failed, one of server creation failed")
            message="DVR testcase 16 failed, one of server creation failed, server 1 status is {}".format(status1)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)     
    except Exception as e:
        logging.exception(e)
        message= message+ "DVR testcase 16 failed/ error occured: {}".format(e)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
    logging.info("DVR testcase 16 finished")
    return isPassed, message
def dvr_test_case_17(neutron_ep, token):
    message=""
    isPassed=False    
    response= send_get_request("{}/v2.0/agents?agent_type=Metadata+agent".format(neutron_ep), token)
    response= str(response.text)
    total_agents= response.count("Metadata agent")
    if total_agents==6:
        isPassed=True
        logging.info("DVR Testcase 17 passed, all nodes have neutron metadata agent, expected nodes 6, received {}".format(total_agents))
        message= "DVR Testcase 17 passed, all nodes have neutron metadata agent, expected nodes 6, received {}".format(total_agents)
    else:
        logging.error("DVR Testcase 17 failed, all nodes do not have neutron metadata agent, expected nodes 6, received {}".format(total_agents))
        message= "DVR Testcase 17 passed, all nodes do not have neutron metadata agent, expected nodes 6, received {}".format(total_agents)
    return isPassed, message

def dvr_test_case_19(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, router_id, security_group_id, image_id, flavor_id):
    logging.info("DVR testcase 19 started")
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip =  [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    isPassed= False
    message=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id=""
    try:
        server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network2_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id) 
        status2= check_server_status(nova_ep, token, server_2_id) 
        if status1== "active" and status2== "active":
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
            server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
            server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server2_port= get_ports(neutron_ep, token, network2_id, server2_ip)
            flaoting_1_ip, floating_1_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
            flaoting_2_ip, floating_2_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            logging.info("Waiting for server to boot")
            s1_wait= wait_instance_boot(flaoting_1_ip)
            s2_wait= wait_instance_boot(flaoting_2_ip)
            s2_ssh_wait= wait_instance_ssh(flaoting_2_ip, settings)
            print("ping ssh 1: {}".format(s1_wait))
            print("ping ssh 2: {}".format(s2_wait))
            print("wait ssh is: {}".format(s2_ssh_wait))
            if s1_wait== True and s2_wait == True and s2_ssh_wait== True:
                #get namspaces
                #router namespace
                router_namespace= "qrouter-"+router_id
                logging.info("Qrouter namespace is: {}".format(router_namespace))
                command="ip netns | grep fip"
                fip_namespace= ssh_into_node(compute0_ip, command)
                fip_namespace= fip_namespace[0]
                fip_namespace= fip_namespace.split(' ')
                fip_namespace= fip_namespace[0]
                logging.info("Floating Ip namespace is: {}".format(fip_namespace))
                logging.info("starting threads")
                p1 = Thread(target=ssh_conne, args=(flaoting_2_ip, flaoting_1_ip, settings,))
                p2 = Thread(target=listen_tcpdump, args=(compute0_ip, fip_namespace, "floating_ip" ))
                p2.start()
                p1.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()
                icmp_check= que.get()
                tcpdump_message= que.get()
                ping_status= que.get()
                if ping_status=="":
                    if(icmp_check== True):
                        isPassed= True
                        logging.info("DVR testcase 19 passed, icmp is received on floating ip namespace from other network")
                        message="DVR testcase 19 passed, icmp is received on floating ip namespace from other network, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)
                    else:
                        message="DVR testcase 19 failed, icmp is not received on floating ip namespace from other network, icmp status is {}, message is:\n {}\n ".format(icmp_check, tcpdump_message)

                else: 
                    message="DVR testcase 19 failed, failed and ping instance floating ip from second instance"
                    logging.error("DVR testcase 19 failed, failed and ping instance floating ip from second instance")
            else:
                message="DVR testcase 19 failed, failed to ssh and ping server/s floating ip"
                logging.error("DVR testcase 19 failed, failed to ssh and ping server/s floating ip")
        else:
            logging.error("DVR testcase 19 failed, one of server creation failed")
            message="DVR testcase 19 failed, one of server creation failed, server 1 status is {} server 2 status is {}".format(status1, status2)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if server_2_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if floating_2_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
        time.sleep(2)    
    except Exception as e:
        logging.exception(e)
        message= message+ " DVR testcase 19 failed/ error occured: {}".format(e)
      
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if server_2_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if floating_2_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
        time.sleep(2)
    logging.info("DVR testcase 19 finished")
    return isPassed, message
def dvr_test_case_14_15_23(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id, flavor_id):
    isPassed14=isPassed15=isPassed23= False
    message14=message15=message23=server_1_id=server_2_id=floating_1_ip_id=floating_2_ip_id=""
    logging.info("DVR testcase 14 15 23 started")
    compute_nodes_ip= [val for key, val in baremetal_node_ips.items() if "compute" in key]
    command= "sudo ip netns"
    router_namespace= "qrouter-"+router_id
    node_selected=""
    try:
        for compute in compute_nodes_ip:
            namespaces= ssh_into_node(compute, command)
            if(router_namespace not in namespaces[0]):
                node_selected= compute
                logging.info("compute node {} do not have qrouter namespace {}".format(compute, namespaces[0]))
                break
        else:
            message14=message15=message23="All compute nodes have already qrouter namespace please delete them before proceed"
        if node_selected  != "":
            compute_nodes_name= [key for key, val in baremetal_node_ips.items() if node_selected in val]
            compute_nodes_name=compute_nodes_name[0]
            logging.info("host selected for instance creation is {}".format(compute_nodes_name))
           
            server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_nodes_name)
            server_build_wait(nova_ep, token, [server_1_id])
            status1= check_server_status(nova_ep, token, server_1_id) 
            if status1== "active":
                public_network_id= search_network(neutron_ep, token, "public")
                public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
                server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
                server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
                flaoting_1_ip, floating_1_ip_id=  create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
                logging.info("Waiting for server to boot")
                s1_wait= wait_instance_boot(flaoting_1_ip)
                print("ping ssh 1: {}".format(s1_wait))
                if s1_wait== True:
                    namespaces= ssh_into_node(compute, command)
                    if(router_namespace in namespaces[0]):
                        isPassed14=True
                        logging.info("DVR testcase 14 passed, qrouter namespace is created in compute node, namespaces are \n{}\n".format(namespaces[0]))
                        message14="DVR testcase 14 passed, qrouter namespace is created in compute node, namespaces are \n{}\n".format(namespaces[0])
                    else:
                        logging.info("DVR testcase 14 failed, qrouter namespace is not created in compute node, namespaces are \n{}\n".format(namespaces[0]))
                        message14="DVR testcase 14 failed, qrouter namespace is not created in compute node, namespaces are \n{}\n".format(namespaces[0])
   
                    if("fip-" in namespaces[0]):
                        isPassed15=True
                        logging.info("DVR testcase 15 passed, floatingip namespace is created in compute node, namespaces are \n{}\n".format(namespaces[0]))
                        message15="DVR testcase 15 passed, floatingip namespace is created in compute node, namespaces are \n{}\n".format(namespaces[0])
                    else:
                        logging.info("DVR testcase 15 failed, floatingip namespace is not created in compute node, namespaces are \n{}\n".format(namespaces[0]))
                        message15="DVR testcase 15 failed, floatingip namespace is not  created in compute node, namespaces are \n{}\n".format(namespaces[0])
                    
                    logging.info("deleting  servers")
                    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
                    time.sleep(10)
                    server_1_id=""
                    namespaces= ssh_into_node(compute, command)
                    if(router_namespace not in namespaces[0]):
                        isPassed23=True
                        logging.info("DVR testcase 23 passed, qrouter namespace is deleted in compute node after deleting instance, namespaces are \n{}\n".format(namespaces[0]))
                        message23="DVR testcase 23 passed, qrouter namespace is deleted in compute node after deleting instance, namespaces are \n{}\n".format(namespaces[0])
                    else:
                        logging.info("DVR testcase 23 failed, qrouter namespace is not deleted in compute node after deleting instance, namespaces are \n{}\n".format(namespaces[0]))
                        message23="DVR testcase 23 failed, qrouter namespace is not deleted in compute node after deleting instance, namespaces are \n{}\n".format(namespaces[0])
                else:
                    message14="DVR testcase 14 failed, failed to ssh and ping server/s floating ip"
                    message15="DVR testcase 15 failed, failed to ssh and ping server/s floating ip"
                    message23="DVR testcase 23 failed, failed to ssh and ping server/s floating ip"
                    logging.error("DVR testcase 14,15,23 failed, failed to ssh and ping server/s floating ip")
            else:
                logging.error("DVR testcase 14,15,23 failed, one of server creation failed")
                message14="DVR testcase 14 failed, one of server creation failed, server 1 status is {}".format(status1)
                message15="DVR testcase 15 failed, one of server creation failed, server 1 status is {}".format(status1)
                message23="DVR testcase 23 failed, one of server creation failed, server 1 status is {}".format(status1)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
    except Exception as e:
        logging.exception(e)
        message14= message14+ " DVR testcase 14 failed/ error occured: {}".format(e)
        message15= message15+" DVR testcase 15 failed/ error occured: {}".format(e)
        message23= message23+" DVR testcase 23 failed/ error occured: {}".format(e)
        if server_1_id != "":
            logging.info("deleting server")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        time.sleep(10)
        if floating_1_ip_id != "":
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
    logging.info("DVR testcase 14,15,23 finished")
   
    return isPassed14, message14, isPassed15, message15, isPassed23, message23

def dvr_test_case_31(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("DVR Test Case 31 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute2 =  [key for key, val in baremetal_node_ips.items() if "compute-2" in key]
    compute2= compute2[0]
    try:
       
        #search and create server
        server1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1)
        server_build_wait(nova_ep, token, [server1_id])
        status1= check_server_status(nova_ep, token, server1_id)
        if  status1 == "error":
            logging.error("Test Case 31 failed")
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
                    logging.info("DVR test Case 31 Passed")
                    message="DVR testcase 31 passed, live migration of instance is successfull, status code is {}, old host {}, new host {} \n".format(response, compute1, new_host)
                else:
                    logging.error("DVR test Case 31 failed, ping failed after live migration")
                    message= "DVR test Case 31 failed, ping failed after live migration"
            else:
                logging.error("live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host))
                message="live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, compute1, new_host)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    except Exception as e:
        logging.exception("DVR test Case 31 failed/ error occured")
        message= message+" DVR testcase 31 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)
    logging.info("DVR Test Case 31 finished")
    return isPassed, message

def dvr_test_case_32(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id, flavor_id):  
    logging.info("HCI Test Case 32 running")
    isPassed= False
    message=""
    server1_id=server_floating_ip_id=server2_floating_ip_id=""
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    try:
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
        
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)            
    except Exception as e:
        logging.exception("DVR test Case 32 failed/ error occured")
        message= metadata+" DVR testcase 32 failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        
        if(server1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server1_id), token)
        if(server_floating_ip_id ==""):
            logging.info("releasing floating ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, server_floating_ip_id), token)    
    logging.info("DVR Test Case 32 finished")
    return isPassed, message

def dvr_volume_test_case(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_node_ips):
    logging.info("starting volume testcases")
    server1_id= "6faa117e-9349-4303-a31f-29663f916409"
    server2_id= "299182c3-bb2c-4bbf-af84-4e4ae6602b4e"
    floating_ip= "100.67.62.98"
    message, message2= volume_test_cases(cinder_ep, keystone_ep, nova_ep, token, settings, baremetal_node_ips, server1_id, server2_id, floating_ip)
    print(message)
    print(message2)








