from openstack_functions import *
import logging
import paramiko
import os
from test_cases import *
import time
import math
import queue
from threading import Thread

tcpdump_queue= queue.Queue()
ping_queue= queue.Queue()

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
        error= stderr.read().decode('ascii')
        return output
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        ssh_client.close()
        logging.info("Connection from client has been closed") 
def listen_tcp_dump(host_ip, command):
    #tcpdump_queue.queue.clear()
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
        print(output)
        error= stderr.read().decode('ascii')
        tcpdump_queue.put(error)
        tcpdump_queue.put(output)
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
        command= "ping  -c 100 {}".format(server2)
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
        ping_queue.put(error)
        ping_queue.put(output)
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        client.close()
        logging.info("Connection from client has been closed")  
def ssh_conne2(server1, server2, settings):
    try:
        command= "ping  -c 5 {}".format(server2)
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
    retries=0
    try:
        #Remove old host entries
        command= "ssh-keygen -R {}".foramt(ip)
        os.system(command)
    except:
        pass
    while(1):
        try:
            client= paramiko.SSHClient()
            paramiko.AutoAddPolicy()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
            break
        except:
            pass
            logging.info("Waiting for server to ssh")
            time.sleep(30)
        retries=retries+1
        if(retries==10):
            break

def get_vfs_count():
    command= "cat ~/pilot/templates/neutron-sriov.yaml |grep NumSriovVfs"
    result= os.popen(command).read()
    result= result.split(':')
    result= result[1].strip()
    return result
def get_last_created_presenter_port(node):
    command= "sudo ovs-dpctl show"
    presenter_ports= ssh_into_node(node, command)
    presenter_ports= presenter_ports.split('\n')
    presenter_ports= presenter_ports[-2]
    presenter_ports= presenter_ports.split(":")
    print("presenter port is: {}".format(presenter_ports[0]))
    return presenter_ports
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
def sriov_vflag_test_case_3(baremetal_nodes_ips):
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
                vflags=""
                output= output+"Compute Node: {} ".format(node)
                total_flags= vflags.count("vf")
                output= output+ " interface {} total vflags are {} \n".format(interface,total_flags)
                output= output+ vflags
                if(total_flags !=16):
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

def sriov_vflag_test_case_6(baremetal_nodes_ips):
    logging.info("SRIOV Test Case 6 running")
    isPassed= False
    messager=output=""
    error=0
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    try:
        for node in compute_nodes_ip:
            command= "sudo ovs-vsctl get Open_vSwitch . other_config:hw-offload"
            status= ssh_into_node(node, command )
            logging.info("hw offload status is: ".format(status))
            output=output+" Node: {} , hw-offload status {}".format(node, status)
            if(status.strip()!= '"true"'):
                error=1
        if (error==1 ):
            message= "Sriov testcase 6 failed, all compute nodes do not have hw-offload, \n"+output
            logging.info(message= "Sriov testcase 6 failed, all compute nodes do not have hw-offload, \n"+output)
        else: 
            isPassed= True
            message= "Sriov testcase 6 passed, all compute nodes have hw-offload true, \n"+output
            logging.info("Sriov testcase 6 passed, all compute nodes have hw-offload true, \n"+output)
    except Exception as e:
        logging.exception("sriov_vflag testcase 6 failed/ error occured {}".format(e))
        message= "sriov_vflag testcase 6 failed/ error occured {}".format(e)
    logging.info("SRIOV Test Case 6 finished")
    return isPassed, message

def sriov_vflag_test_case_7_9(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 7 and 9 running")
    isPassed7=isPassed9= False
    message7=message9=""
    server_1_id=flavor_id=port_1_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    try:
        #get old presenter ports
        old_port=get_last_created_presenter_port(compute0_ip)
        logging.info("Last created presenter port is: {}".format(old_port))
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        if  status1 == "error" :
            logging.error("Test Case 7 and 9  failed")
            logging.error("Instances creation failed")
            message="instance creation failed, its status is {}".format(status1)
        else:
            isPassed7= True
            message7= "SRIOV VFLAG testcase 7 passed, srviov vflag instance created successfully, its status is {}".format(status1)
            logging.info("SRIOV VFLAG testcase 7 passed, srviov vflag instance created successfully, its status is {}".format(status1))

            #get new presenter ports
            new_port=get_last_created_presenter_port(compute0_ip)
            logging.info("New created presenter port is: {}".format(new_port))

            if(old_port != new_port):
                isPassed9=True
                message9= "SRIOV VFLAG testcase 9 passed, instance presenter port created successfully, old port is {}, new port is {}".format(old_port, new_port)
                logging.info("SRIOV VFLAG testcase 9 passed, instance presenter port created successfully, old port is {}, new port is {}".format(old_port, new_port))
            else:
                message9= "SRIOV VFLAG testcase 9 passed, instance presenter port  not created, old port is {}, new port is {}".format(old_port, new_port)
                logging.error("SRIOV VFLAG testcase 9 passed, instance presenter port not created, old port is {}, new port is {}".format(old_port, new_port))
            
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
 
    except Exception as e:
        logging.exception("Test Case 7 and 9 failed/ error occured")
        message="sriov instance and presenter port creation failed/ error occured {}".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
    logging.info("SRIOV Test Case 7 and 9 finished")
    return isPassed7, message7, isPassed9, message9
    
def sriov_vflag_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 10 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute1_ip= [val for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1_ip= compute1_ip[0]

    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)
        compute1_old_port=get_last_created_presenter_port(compute1_ip)

        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        port_2_id, port_2_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_2", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova1", security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 10 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 10 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
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

            #get new presenter ports
            compute0_new_port=get_last_created_presenter_port(compute0_ip)
            compute1_new_port=get_last_created_presenter_port(compute1_ip)
            #compare old and new presenter ports
            if(compute0_old_port == compute0_new_port) or compute1_old_port == compute1_new_port:
                message= "SRIOV VFLAG testcase 10 failed, instance presenter port not created, \n compute0  old port is {}, new port is {}, \n compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port)
                logging.info( "SRIOV VFLAG testcase 10 failed, instance presenter port not created, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
                port_to_listen= (compute1_new_port[1])
                logging.info("Instance 2 presenter port to listen is: {}".format(port_to_listen))
  
                command1= "sudo timeout 120 tcpdump -nnn -i {} | grep 'ICMP echo'".format(port_to_listen)
                p1= Thread(target=listen_tcp_dump, args=(compute1_ip, command1))
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2= Thread(target=ssh_conne, args=(flaoting_1_ip, flaoting_2_ip, settings ))
                p1.start()
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()

                #Getting threads output from queue
                tcpdump_error=tcpdump_queue.get()
                tcpdump_output= tcpdump_queue.get()
                ping_error=ping_queue.get()
                ping_output= ping_queue.get()

                # Check if error occured
                if(ping_error != ""):
                    message="SRIOV VFLAG testcase 10 failed, Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error)
                    logging.info("Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error))
                else:
                    ping_output= ping_output.split("\n") 
                    total_ping_requests= tcpdump_output.count("ICMP echo request")
                    total_ping_reply= tcpdump_output.count("ICMP echo reply")
                    if(total_ping_requests==1 and total_ping_reply==1):
                        isPassed=True
                        message="SRIOV VFLAG testcase 10 passed, two instances on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.info("SRIOV VFLAG testcase 10 passed, two instances on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10]))
                    else:
                        message="SRIOV VFLAG testcase 10 failed, two instances on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.error("SRIOV VFLAG testcase 10 failed, two instances on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are:  \n{}\n".format(tcpdump_output, ping_output[0:10]))
            
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 10 failed/ error occured")
        message="Test Case 10 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 10 finished")
    return isPassed, message
  
def sriov_vflag_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 11 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute1_ip= [val for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1_ip= compute1_ip[0]

    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)
        compute1_old_port=get_last_created_presenter_port(compute1_ip)

        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        port_2_id, port_2_ip= create_port(neutron_ep, token, network2_id, subnet2_id, "test_case_port_2", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova1", security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 11 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 11 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
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

            #get new presenter ports
            compute0_new_port=get_last_created_presenter_port(compute0_ip)
            compute1_new_port=get_last_created_presenter_port(compute1_ip)
            #compare old and new presenter ports
            if(compute0_old_port == compute0_new_port) or compute1_old_port == compute1_new_port:
                message= "SRIOV VFLAG testcase 11 failed, instance presenter port not created, \n compute0  old port is {}, new port is {}, \n compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port)
                logging.info( "SRIOV VFLAG testcase 11 failed, instance presenter port not created, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
                port_to_listen= (compute1_new_port[1])
                logging.info("Instance 2 presenter port to listen is: {}".format(port_to_listen))
  
                command1= "sudo timeout 120 tcpdump -nnn -i {} | grep 'ICMP echo'".format(port_to_listen)
                p1= Thread(target=listen_tcp_dump, args=(compute1_ip, command1))
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2= Thread(target=ssh_conne, args=(flaoting_1_ip, flaoting_2_ip, settings ))
                p1.start()
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()

                #Getting threads output from queue
                tcpdump_error=tcpdump_queue.get()
                tcpdump_output= tcpdump_queue.get()
                ping_error=ping_queue.get()
                ping_output= ping_queue.get()

                # Check if error occured
                if(ping_error != ""):
                    message="SRIOV VFLAG testcase 11 failed, Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error)
                    logging.info("Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error))
                else:
                    ping_output= ping_output.split("\n") 
                    total_ping_requests= tcpdump_output.count("ICMP echo request")
                    total_ping_reply= tcpdump_output.count("ICMP echo reply")
                    if(total_ping_requests==1 and total_ping_reply==1):
                        isPassed=True
                        message="SRIOV VFLAG testcase 11 passed, two instances on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.info("SRIOV VFLAG testcase 11 passed, two instances on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10]))
                    else:
                        message="SRIOV VFLAG testcase 11 failed, two instances on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.error("SRIOV VFLAG testcase 11 failed, two instances on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are:  \n{}\n".format(tcpdump_output, ping_output[0:10]))
            
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 11 failed/ error occured")
        message="Test Case 11 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 11 finished")
    return isPassed, message
  
def sriov_vflag_test_case_12(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 12 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]

    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)
        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        port_2_id, port_2_ip= create_port(neutron_ep, token, network2_id, subnet2_id, "test_case_port_2", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id])
        instance1_port=get_last_created_presenter_port(compute0_ip)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova0", security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id,])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 12 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 12 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
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

            #get new presenter ports
            
            instance2_port=get_last_created_presenter_port(compute0_ip)
            #compare old and new presenter ports
            if(compute0_old_port == instance1_port or instance1_port == instance2_port):
                message= "SRIOV VFLAG testcase 12 failed, instance presenter port not created, \n compute0  old port is {},  instance 1 port is  {}, instqance 2 port is {} ".format(compute0_old_port, instance1_port, instance2_port)
                logging.info( "SRIOV VFLAG testcase 12 failed, instance presenter port not created, compute0  old port is {},  instance 1 port is  {}, instqance 2 port is {} ".format(compute0_old_port, instance1_port, instance2_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, instance 1 port is  {}, instqance 2 port is {} ".format(compute0_old_port, instance1_port, instance2_port))
                port_to_listen= (instance2_port[1])
                logging.info("Instance 2 presenter port to listen is: {}".format(port_to_listen))
                command1= "sudo timeout 120 tcpdump -nnn -i {} | grep 'ICMP echo'".format(port_to_listen)
                p1= Thread(target=listen_tcp_dump, args=(compute0_ip, command1))
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2= Thread(target=ssh_conne, args=(flaoting_1_ip, flaoting_2_ip, settings ))
                p1.start()
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()

                #Getting threads output from queue
                tcpdump_error=tcpdump_queue.get()
                tcpdump_output= tcpdump_queue.get()
                ping_error=ping_queue.get()
                ping_output= ping_queue.get()

                # Check if error occured
                if(ping_error != ""):
                    message="SRIOV VFLAG testcase 12 failed, Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error)
                    logging.info("Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error))
                else:
                    ping_output= ping_output.split("\n") 
                    total_ping_requests= tcpdump_output.count("ICMP echo request")
                    total_ping_reply= tcpdump_output.count("ICMP echo reply")
                    if(total_ping_requests==1 and total_ping_reply==1):
                        isPassed=True
                        message="SRIOV VFLAG testcase 12 passed, two instances on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.info("SRIOV VFLAG testcase 12 passed, two instances on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10]))
                    else:
                        message="SRIOV VFLAG testcase 12 failed, two instances on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.error("SRIOV VFLAG testcase 12 failed, two instances on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are:  \n{}\n".format(tcpdump_output, ping_output[0:10]))
            
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 12 failed/ error occured")
        message="Test Case 12 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 12 finished")
    return isPassed, message
  
def sriov_vflag_test_case_13(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 13 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute1_ip= [val for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1_ip= compute1_ip[0]

    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)

        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network_id, security_group_id, compute1, "nova1" )
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 13 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 13 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
            server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.debug("Server 1 ip: {}".format(flaoting_1_ip))
            logging.debug("Server 2 ip: {}".format(flaoting_2_ip))
            logging.info("ssh into server1")

            #get new presenter ports
            compute0_new_port=get_last_created_presenter_port(compute0_ip)
            #compare old and new presenter ports
            if(compute0_old_port == compute0_new_port):
                message= "SRIOV VFLAG testcase 13 failed, instance presenter port not created, \n compute0  old port is {}, new port is {} ".format(compute0_old_port, compute0_new_port)
                logging.info( "SRIOV VFLAG testcase 13 failed, instance presenter port not created, compute0  old port is {}, new port is {}".format(compute0_old_port, compute0_new_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, new port is {}".format(compute0_old_port, compute0_new_port ))
                port_to_listen= (compute0_new_port[1])
                logging.info("Instance 2 presenter port to listen is: {}".format(port_to_listen))
  
                command1= "sudo timeout 120 tcpdump -nnn -i {} | grep 'ICMP echo'".format(port_to_listen)
                p1= Thread(target=listen_tcp_dump, args=(compute0_ip, command1))
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2= Thread(target=ssh_conne, args=(flaoting_2_ip, flaoting_1_ip, settings ))
                p1.start()
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()

                #Getting threads output from queue
                tcpdump_error=tcpdump_queue.get()
                tcpdump_output= tcpdump_queue.get()
                ping_error=ping_queue.get()
                ping_output= ping_queue.get()

                # Check if error occured
                if(ping_error != ""):
                    message="SRIOV VFLAG testcase 13 failed, Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error)
                    logging.info("Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error))
                else:
                    ping_output= ping_output.split("\n") 
                    total_ping_requests= tcpdump_output.count("ICMP echo request")
                    total_ping_reply= tcpdump_output.count("ICMP echo reply")
                    if(total_ping_requests==1 and total_ping_reply==1):
                        isPassed=True
                        message="SRIOV VFLAG testcase 13 passed, sriov and simple instances on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.info("SRIOV VFLAG testcase 13 passed, sriov and simple instances  on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10]))
                    else:
                        message="SRIOV VFLAG testcase 13 failed, sriov and simple instances  on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.error("SRIOV VFLAG testcase 13 failed, sriov and simple instances  on different compute and same network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are:  \n{}\n".format(tcpdump_output, ping_output[0:10]))
            
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 13 failed/ error occured")
        message="Test Case 13 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 13 finished")
    return isPassed, message
        
def sriov_vflag_test_case_14(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 14 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute1_ip= [val for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1_ip= compute1_ip[0]

    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)

        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network2_id, security_group_id, compute1, "nova1" )
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 14 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 14 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server2_port= get_ports(neutron_ep, token, network2_id, server2_ip)
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.debug("Server 1 ip: {}".format(flaoting_1_ip))
            logging.debug("Server 2 ip: {}".format(flaoting_2_ip))
            logging.info("ssh into server1")

            #get new presenter ports
            compute0_new_port=get_last_created_presenter_port(compute0_ip)
            #compare old and new presenter ports
            if(compute0_old_port == compute0_new_port):
                message= "SRIOV VFLAG testcase 14 failed, instance presenter port not created, \n compute0  old port is {}, new port is {} ".format(compute0_old_port, compute0_new_port)
                logging.info( "SRIOV VFLAG testcase 14 failed, instance presenter port not created, compute0  old port is {}, new port is {}".format(compute0_old_port, compute0_new_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, new port is {}".format(compute0_old_port, compute0_new_port ))
                port_to_listen= (compute0_new_port[1])
                logging.info("Instance 2 presenter port to listen is: {}".format(port_to_listen))
  
                command1= "sudo timeout 120 tcpdump -nnn -i {} | grep 'ICMP echo'".format(port_to_listen)
                p1= Thread(target=listen_tcp_dump, args=(compute0_ip, command1))
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2= Thread(target=ssh_conne, args=(flaoting_2_ip, flaoting_1_ip, settings ))
                p1.start()
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()

                #Getting threads output from queue
                tcpdump_error=tcpdump_queue.get()
                tcpdump_output= tcpdump_queue.get()
                ping_error=ping_queue.get()
                ping_output= ping_queue.get()

                # Check if error occured
                if(ping_error != ""):
                    message="SRIOV VFLAG testcase 14 failed, Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error)
                    logging.info("Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error))
                else:
                    ping_output= ping_output.split("\n") 
                    total_ping_requests= tcpdump_output.count("ICMP echo request")
                    total_ping_reply= tcpdump_output.count("ICMP echo reply")
                    if(total_ping_requests==1 and total_ping_reply==1):
                        isPassed=True
                        message="SRIOV VFLAG testcase 14 passed, sriov and simple instances on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.info("SRIOV VFLAG testcase 14 passed, sriov and simple instances  on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10]))
                    else:
                        message="SRIOV VFLAG testcase 14 failed, sriov and simple instances  on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.error("SRIOV VFLAG testcase 14 failed, sriov and simple instances  on different compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are:  \n{}\n".format(tcpdump_output, ping_output[0:10]))
            
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 14 failed/ error occured")
        message="Test Case 14 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 14 finished")
    return isPassed, message
def sriov_vflag_test_case_15(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, network2_id, subnet2_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 15 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]

    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)

        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_build_wait(nova_ep, token, [server_1_id])
        #get new presenter ports
        compute0_new_port=get_last_created_presenter_port(compute0_ip)
        server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  network2_id, security_group_id, compute0, "nova0" )
        server_build_wait(nova_ep, token, [server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 15 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 15 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
        else:
            public_network_id= search_network(neutron_ep, token, "public")
            public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
            server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network2_name"])
            server2_port= get_ports(neutron_ep, token, network2_id, server2_ip)
            flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
            flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
            logging.info("Waiting for server to boot")
            wait_instance_boot(flaoting_1_ip)
            wait_instance_boot(flaoting_2_ip)
            wait_instance_ssh(flaoting_1_ip, settings)
            wait_instance_ssh(flaoting_2_ip, settings)
            logging.debug("Server 1 ip: {}".format(flaoting_1_ip))
            logging.debug("Server 2 ip: {}".format(flaoting_2_ip))
            logging.info("ssh into server1")

            #compare old and new presenter ports
            if(compute0_old_port == compute0_new_port):
                message= "SRIOV VFLAG testcase 15 failed, instance presenter port not created, \n compute0  old port is {}, new port is {} ".format(compute0_old_port, compute0_new_port)
                logging.info( "SRIOV VFLAG testcase 15 failed, instance presenter port not created, compute0  old port is {}, new port is {}".format(compute0_old_port, compute0_new_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, new port is {}".format(compute0_old_port, compute0_new_port ))
                port_to_listen= (compute0_new_port[1])
                logging.info("Instance 2 presenter port to listen is: {}".format(port_to_listen))
  
                command1= "sudo timeout 120 tcpdump -nnn -i {} | grep 'ICMP echo'".format(port_to_listen)
                p1= Thread(target=listen_tcp_dump, args=(compute0_ip, command1))
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2= Thread(target=ssh_conne, args=(flaoting_2_ip, flaoting_1_ip, settings))
                p1.start()
                time.sleep(10) # make sure tcpdump started listening begore ping command run
                p2.start()
                logging.info("waiting for threads to finish")
                p2.join()
                p1.join()

                #Getting threads output from queue
                tcpdump_error=tcpdump_queue.get()
                tcpdump_output= tcpdump_queue.get()
                ping_error=ping_queue.get()
                ping_output= ping_queue.get()

                # Check if error occured
                if(ping_error != ""):
                    message="SRIOV VFLAG testcase 15 failed, Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error)
                    logging.info("Error occured when pinging and listening port, \n tcpdump error is: \n{} \n ping error is \n{} \n".format(tcpdump_error, ping_error))
                else:
                    ping_output= ping_output.split("\n") 
                    total_ping_requests= tcpdump_output.count("ICMP echo request")
                    total_ping_reply= tcpdump_output.count("ICMP echo reply")
                    if(total_ping_requests==1 and total_ping_reply==1):
                        isPassed=True
                        message="SRIOV VFLAG testcase 15 passed, sriov and simple instances on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.info("SRIOV VFLAG testcase 15 passed, sriov and simple instances  on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10]))
                    else:
                        message="SRIOV VFLAG testcase 15 failed, sriov and simple instances  on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are: \n{}\n".format(tcpdump_output, ping_output[0:10])
                        logging.error("SRIOV VFLAG testcase 15 failed, sriov and simple instances  on same compute and different network created successfully along with representer ports, during ping from instance 1 to instance 2 ICMP packet are not received only 1 time, \n TCPDUMP results are: \n {}\n first 10 ping results out of 100 are:  \n{}\n".format(tcpdump_output, ping_output[0:10]))
            
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 15 failed/ error occured")
        message="Test Case 15 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 15 finished")
    return isPassed, message

def sriov_vflag_test_case_16(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 16 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute1_ip= [val for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1_ip= compute1_ip[0]
    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)
        compute1_old_port=get_last_created_presenter_port(compute1_ip)

        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        port_2_id, port_2_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_2", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova1", security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 16 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 16 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
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

            #get new presenter ports
            compute0_new_port=get_last_created_presenter_port(compute0_ip)
            compute1_new_port=get_last_created_presenter_port(compute1_ip)
            #compare old and new presenter ports
            if(compute0_old_port == compute0_new_port) or compute1_old_port == compute1_new_port:
                message= "SRIOV VFLAG testcase 16 failed, instance presenter port not created, \n compute0  old port is {}, new port is {}, \n compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port)
                logging.info( "SRIOV VFLAG testcase 16 failed, instance presenter port not created, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
            output1, error1= ssh_conne2(flaoting_1_ip, flaoting_2_ip, settings)
            #Powering off 1 instance
            perform_action_on_server(nova_ep,token, server_2_id, "os-stop")
            logging.info("Powering off Instance")
            time.sleep(20)
            perform_action_on_server(nova_ep,token, server_2_id, "os-start")
            logging.info("Powering ON Instance")
            wait_instance_boot(flaoting_2_ip)
            output2, error2= ssh_conne2(flaoting_1_ip, flaoting_2_ip, settings)
            if error1=="" or error2=="":
                message= "SRIOV VFLAG testcase 16 passed, instances can ping eachother  after reboot, ping status before shutdown is: \n {}\n ping status after reboot is: \n {}".format(output1, output2)
                logging.info("SRIOV VFLAG testcase 16 passed, instances can ping eachother  after reboot, ping status before shutdown is: \n {}\n ping status after reboot is: \n {}".format(output1, output2))
            else:
                message= "SRIOV VFLAG testcase 16 failed, instances can not ping eachother  after reboot, ping status before shutdown is: \n {}\n ping status after reboot is: \n {}".format(output1, output2)
                logging.error("SRIOV VFLAG testcase 16 failed, instances can not ping eachother  after reboot, ping status before shutdown is: \n {}\n ping status after reboot is: \n {}".format(output1, output2))


            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 16 failed/ error occured")
        message="Test Case 16 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 16 finished")
    return isPassed, message

def sriov_vflag_test_case_17(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 17 running")
    isPassed= False
    message=""
    server_1_id=server_2_id=port_1_id=port_2_id=floating_1_ip_id=floating_2_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute0_ip= [val for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0_ip= compute0_ip[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]
    compute1_ip= [val for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1_ip= compute1_ip[0]
    try:
        #get old presenter ports
        compute0_old_port=get_last_created_presenter_port(compute0_ip)
        compute1_old_port=get_last_created_presenter_port(compute1_ip)

        # Search and Create Flavor
        flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
        #search and create server
        port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1", "vflag" )
        port_2_id, port_2_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_2", "vflag" )
        server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "nova0", security_group_id, compute0)
        server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova1", security_group_id, compute1)
        server_build_wait(nova_ep, token, [server_1_id, server_2_id])
        status1= check_server_status(nova_ep, token, server_1_id)
        status2= check_server_status(nova_ep, token, server_2_id)
        if  status1 == "error" or  status2 == "error":
            logging.error("Test Case 17 failed")
            logging.error("Instances creation failed")
            message="SRIOV VFLAG test case 17 failed,  one of the instance creation is failed, status of instances is: {} {}".format(status1, status2)
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

            #get new presenter ports
            compute0_new_port=get_last_created_presenter_port(compute0_ip)
            compute1_new_port=get_last_created_presenter_port(compute1_ip)
            #compare old and new presenter ports
            if(compute0_old_port == compute0_new_port) or compute1_old_port == compute1_new_port:
                message= "SRIOV VFLAG testcase 17 failed, instance presenter port not created, \n compute0  old port is {}, new port is {}, \n compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port)
                logging.info( "SRIOV VFLAG testcase 17 failed, instance presenter port not created, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
            else:
                logging.info("presenter ports created successfully, compute0  old port is {}, new port is {}, compute 1 old port is {}, new port is {}".format(compute0_old_port, compute0_new_port, compute1_old_port, compute1_new_port))
            output1, error1= ssh_conne2(flaoting_1_ip, flaoting_2_ip, settings)
            #Powering off 1 instance
            response= migrate_server(nova_ep,token, server_2_id)
            if(response == 202): 
                logging.info("Waiting for migration")
                time.sleep(20)
                wait_instance_boot(flaoting_2_ip)
                output2, error2= ssh_conne2(flaoting_1_ip, flaoting_2_ip, settings)
                if error1=="" or error2=="":
                    message= "SRIOV VFLAG testcase 17 passed, instances can ping eachother  after live migration, ping status before migration is: \n {}\n ping status after reboot is: \n {}\n, migration status code is {} ".format(output1, output2, response)
                    logging.info("SRIOV VFLAG testcase 17 passed, instances can ping eachother  after live migration, ping status before migration is: \n {}\n ping status after reboot is: \n {}\n, migration status code is {} ".format(output1, output2, response))
                else:
                    message= "SRIOV VFLAG testcase 17 failed, instances can not ping eachother  after live migration, ping status before migration is: \n {}\n ping status after reboot is: \n {}\n, migration status code is {} ".format(output1, output2, response)
                    logging.error("SRIOV VFLAG testcase 17 failed, instances can not ping eachother  after live migration, ping status before migration is: \n {}\n ping status after reboot is: \n {}\n, migration status code is {} ".format(output1, output2, response))
            else:
                message= "SRIOV VFLAG testcase 17 failed, live migration failed, status code is: {}".format(response)
                logging.error("SRIOV VFLAG testcase 17 failed, live migration failed, status code is: {}".format(response))

            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
            time.sleep(2)
    except Exception as e:
        logging.exception("Test Case 17 failed/ error occured")
        message="Test Case 17 failed/ error occured {} ".format(e)
        logging.exception(e)
        logging.error(e)
        if(flavor_id != ""):
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(server_2_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
            time.sleep(10)
        if(port_1_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
            time.sleep(5)
        if(port_2_id!= ""):
            logging.info("deleting port")
            delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
            time.sleep(5)
        if(floating_1_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_1_ip_id), token)
        if(floating_2_ip_id != ""):
            logging.info("releasing ip")
            delete_resource("{}/v2.0/floatingips/{}".format(neutron_ep, floating_2_ip_id), token)
    logging.info("SRIOV Test Case 17 finished")
    return isPassed, message
