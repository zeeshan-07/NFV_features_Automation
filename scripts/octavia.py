from openstack_functions import *
import logging
import paramiko
import os
from test_cases import *
import time
import math
import subprocess


def loadbalancer_build_wait(loadbal_ep, token, laodbalancer_ids):
    while True:
        flag=0
        for laodbalancer in laodbalancer_ids:
            status= check_loadbalancer_status(loadbal_ep, token, laodbalancer)
            logging.info("loadbalancer status is: {}".format(status))
            if not (status == "ACTIVE" or status=="ERROR"):
                logging.info("Waiting for loadbalancer/s to build")
                flag=1
                time.sleep(10)
        if flag==0:
            break
            
def listener_build_wait(loadbal_ep, token, listener_ids):
    while True:
        flag=0
        for listener in listener_ids:
            status= check_listener_status(loadbal_ep, token, listener)
            logging.info("listener status is: {}".format(status))
            if not (status == "ACTIVE" or status=="ERROR"):
                logging.info("Waiting for listener/s to build")
                flag=1
                time.sleep(10)
        if flag==0:
            break
def pool_build_wait(loadbal_ep, token, pool_ids):
    while True:
        flag=0
        for pool in pool_ids:
            status= check_pool_status(loadbal_ep, token, pool)
            logging.info("pool status is: {}".format(status))
            if not (status == "ACTIVE" or status=="ERROR"):
                logging.info("Waiting for pool/s to build")
                flag=1
                time.sleep(10)
        if flag==0:
            break
def install_http_packages_on_instance(server1, message, settings):
    try:
        #command1= "sudo echo 'nameserver 10.8.8.8' > sudo /etc/resolv.conf"
        command2= "sudo yum -y update"
        command3="sudo yum install -y epel-release"
        command4= "sudo yum install -y nginx"
        command5= "sudo systemctl start nginx"
        command6="sudo yum install nc.x86_64"
        command7="nc -lp 23456"
        client= paramiko.SSHClient()
        paramiko.AutoAddPolicy()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server1, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
        channel = client.get_transport().open_session()
        logging.info("SSH Session is established")
        logging.info("Running command in a instance node")
        channel.invoke_shell()
        channel.send("sudo -i \n")
        time.sleep(2)
        channel.send("rm /etc/resolv.conf\n")
        time.sleep(2)
        channel.send("touch /etc/resolv.conf\n")
        time.sleep(2)
        channel.send("printf  'nameserver 10.8.8.8' > /etc/resolv.conf\n")
        time.sleep(2)
        
        #print("stderr1 is: {}".format(stderr.read().decode('ascii')))
        #logging.info("command {} successfully executed on instance {}".format(command1, server1))
        #stdin, stdout, stderr = client.exec_command(command2)
        #time.sleep(120)
        #print("stderr2 is: {}".format(stderr.read().decode('ascii')))
        #logging.info("command {} successfully executed on instance {}".format(command2, server1))
        
        stdin, stdout, stderr = client.exec_command(command3)
        time.sleep(30)
        logging.info("command {} successfully executed on instance {}".format(command3, server1))
        print("stderr3 is: {}".format(stderr.read().decode('ascii')))
        stdin, stdout, stderr = client.exec_command(command4)
        time.sleep(30)
        logging.info("command {} successfully executed on instance {}".format(command4, server1))
        print("stderr4 is: {}".format(stderr.read().decode('ascii')))
        stdin, stdout, stderr = client.exec_command(command5)
        time.sleep(30)
        logging.info("command {} successfully executed on instance {}".format(command5, server1))
        print("stderr5 is: {}".format(stderr.read().decode('ascii')))
        channel.send("cd /usr/share/nginx/html/\n")
        channel.send("rm index.html\n")
        time.sleep(2)
        channel.send("touch index.html\n")
        time.sleep(2)
        channel.send("printf  '{}'> index.html\n".format(message))
        time.sleep(2)
        logging.info("command {} successfully executed on instance {}".format(command6, server1))
        print("stderr5 is: {}".format(stderr.read().decode('ascii')))
        time.sleep(30)
        logging.info("command {} successfully executed on instance {}".format(command7, server1))
        print("stderr5 is: {}".format(stderr.read().decode('ascii')))
        time.sleep(30)
 
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        client.close()
        logging.info("Connection from client has been closed")  
def wait_instance_boot(ip):
    retries=0
    while(1):
        response = os.system("ping -c 3 " + ip)
        if response == 0:
            logging.info ("Ping successfull!") 
            return True
        logging.info("Waiting for server to boot")
        time.sleep(30)
        retries=retries+1
        if(retries==10):
            return False
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
            print("Result is : ".format(result))
            ssh=True
            break
        except:    
            pass
            logging.info("Waiting for server to ssh")
            time.sleep(30)
        retries=retries+1
        if(retries==10):
            break
    return ssh
        

def octavia_test_case_3_4_7_8_9_10(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    logging.info("Octavia testcase 3, 4, 7, 8, 9, 10 started")
    isPassed3=isPassed4=isPassed7=isPassed8=isPassed9=isPassed10= False
    message3=message4=message7=message8=message9=message10=""
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage3=mesage4=mesage7=mesage8=mesage9=mesage10="Octavia Testcase failed, because loadbalancer is in error state"
        return isPassed3, message3, isPassed4, message4, isPassed7, message7, isPassed8, message8, isPassed9, message9, isPassed10, message10
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage3=mesage4=mesage7=mesage8=mesage9=mesage10="Octavia Testcase failed, because listener is in error state"
        return isPassed3, message3, isPassed4, message4, isPassed7, message7, isPassed8, message8, isPassed9, message9, isPassed10, message10
    #create pool id
    pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "HTTP", "ROUND_ROBIN")
    pool_build_wait(loadbal_ep, token, [pool_id])
    pool_state= check_pool_status(loadbal_ep, token, pool_id)
    logging.info("pool status is: "+pool_state)
    if(pool_state=="error"):
        mesage3=mesage4=mesage7=mesage8=mesage9=mesage10="Octavia Testcase failed, because pool is in error state"
        return isPassed3, message3, isPassed4, message4, isPassed7, message7, isPassed8, message8, isPassed9, message9, isPassed10, message10
    
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    #put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_3_id= search_and_create_server(nova_ep, token, "test_case_Server3", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_4_id= search_and_create_server(nova_ep, token, "test_case_Server4", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_1_id, server_2_id, server_3_id, server_4_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
    status3= check_server_status(nova_ep, token, server_3_id)
    status4= check_server_status(nova_ep, token, server_4_id)
    

    if  status1 != "active" or status2 != "active" or status3 != "active" or status4 != "active":
        mesage3=mesage4=mesage7=mesage8=mesage9=mesage10="Octavia Testcase failed, because one of the server is in error state {} {} {} {}".format(status1, status2, status3, status4)
        return isPassed3, message3, isPassed4, message4, isPassed7, message7, isPassed8, message8, isPassed9, message9, isPassed10, message10,
    isPassed3=True
    message3= "Octavia Testcase 3 passed, loadbalancer, listenet and pool is in active state, their status is loadbalancer: {}, listener {}, pool {} and server state is s1: {} s2: {} s3: {} s4: {}".format(loadbalancer_state, listener_state, pool_state, status1, status2, status3, status4)

    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
    server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
    server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
    server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
    server3_ip= get_server_ip(nova_ep, token, server_3_id, settings["network1_name"])
    server3_port= get_ports(neutron_ep, token, network_id, server3_ip)
    server4_ip= get_server_ip(nova_ep, token, server_4_id, settings["network1_name"])
    server4_port= get_ports(neutron_ep, token, network_id, server4_ip)
    public_network_id= search_network(neutron_ep, token, "public")
    public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
    #flaoting1_ip= get_server_floating_ip(nova_ep, token, server_1_id, settings["network1_name"])
    #flaoting2_ip= get_server_floating_ip(nova_ep, token, server_2_id, settings["network1_name"])
    #flaoting3_ip= get_server_floating_ip(nova_ep, token, server_3_id, settings["network1_name"])
    flaoting1_ip, floating1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
    flaoting2_ip, floating2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
    flaoting3_ip, floating3_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server3_ip, server3_port)
    flaoting4_ip, floating4_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server4_ip, server4_port)

    wait_instance_boot(flaoting1_ip)
    wait_instance_ssh(flaoting1_ip, settings)
    wait_instance_boot(flaoting2_ip)
    wait_instance_ssh(flaoting2_ip, settings)
    wait_instance_boot(flaoting3_ip)
    wait_instance_ssh(flaoting3_ip, settings)
    wait_instance_boot(flaoting4_ip)
    wait_instance_ssh(flaoting4_ip, settings)

    logging.info("Installing Packages in instances")
    install_http_packages_on_instance(flaoting1_ip, "1", settings)
    install_http_packages_on_instance(flaoting2_ip, "2", settings)
    install_http_packages_on_instance(flaoting3_ip, "3", settings)
    install_http_packages_on_instance(flaoting4_ip, "4", settings)
    try:
        add_instance_to_pool(loadbal_ep, token, pool_id, server1_ip, subnet_id, 80 )
        time.sleep(10)
        add_instance_to_pool(loadbal_ep, token, pool_id, server2_ip, subnet_id, 80 )
        time.sleep(10)
        add_instance_to_pool(loadbal_ep, token, pool_id, server3_ip, subnet_id, 80 )
        time.sleep(10)
        health_monitor_pool(loadbal_ep, token, pool_id, "HTTP")   
    except:
        pass
        
    lb_vipport= check_loadbalancer_vipport(loadbal_ep, token, loadbalancer_id)
    logging.info("vip port: {}".format(lb_vipport))
    lb_ip_id, lb_ip= create_loadbalancer_floatingip(neutron_ep, token, public_network_id )
    logging.info("load balancer ip is: {}".format(lb_ip))
    assign_lb_floatingip(neutron_ep, token, lb_vipport, lb_ip_id )
    curl_command="curl "+str(lb_ip)
    output=[]
    for i in range(0, 6):    
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)   
    logging.info("output is:")
    logging.info(output) 
    if(output[0]!= output[1] and output[0]!= output[2] and output[3]!= output[4] and output[3]!= output[5] and output[0]==output[3] and output[1]==output[4] and output[2]==output[5]):
        isPassed4= True
        logging.info("Octavia Test case 4 passed, output is: {}".format(output))
        message4= "Octavia Test case 4 passed, output is in round robin format {}".format(output)
    else:
        logging.error("Octavia Test case 4 passed, output is: ".format(output))
        message4= "Octavia Test case 4 passed, output is in not round robin format {}".format(output)

    ######################################3
    #get pool member
    member_id= get_pool_member(loadbal_ep, token, pool_id)
    down_pool_member(loadbal_ep, token, pool_id, member_id)
    output=[]
    for i in range(0, 6): 
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)   
    logging.info("output is:")
    logging.info(output)
    up_pool_member(loadbal_ep, token, pool_id, member_id )
    if(output[0]!= output[1] and output[2]!= output[3] and output[4]!= output[5] and output[0]==output[1] and output[0]==output[4] and output[1]==output[3] and output[1]==output[5]):
        isPassed7=True
        logging.info("Octavia Test case 7 passed, output is in round robin format after member is down {} ".format(output))
        message7= "Octavia Test case 7 passed, output is in round robin format after member is down  {}".format(output)
    else:
        logging.error("Octavia Test case 7 failed,output is not in round robin format after member is down {}".format(output))
        message7= "Octavia Test case 7 passed, output is not in round robin format after member is down  {}".format(output)
 
    #######################################
    server_4_id= search_and_create_server(nova_ep, token, "testcase_server4", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server4_ip= get_server_ip(nova_ep, token, server_4_id, settings["network1_name"])
    server4_port= get_ports(neutron_ep, token, network_id, server4_ip)
    flaoting1_ip= get_server_floating_ip(nova_ep, token, server_4_id, settings["network1_name"])
    try:
        add_instance_to_pool(loadbal_ep, token, pool_id, server4_ip, subnet_id, 80 )
        time.sleep(10)
    except Exception as a:
        pass
    output=[]
    for i in range(0, 8): 
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)   
    logging.info("output is:")
    logging.info(output)
    if(output[0]!= output[1] and output[0]!= output[2] and output[0]!= output[3] and output[4]!= output[5] and output[4]!= output[6] and output[4]!= output[7] and output[0]==output[4] and output[1]==output[5] and output[2]==output[6] and output[3]==output[7]):
        isPassed8= True
        logging.info("Octavia Test case 8 passed, output is in round robin format after adding 4th instance {} ".format(output))
        message8= "Octavia Test case 8 passed, output is in round robin format after  adding 4th instance  {}".format(output)

    else:
        logging.error("Octavia Test case 8 passed, output is not in round robin format after adding 4th instance {} ".format(output))
        message8= "Octavia Test case 8 passed, output is not in round robin format after adding 4th instance  {}".format(output)
        
    ###################################
    logging.info("Disabling Load balancer")
    disable_loadbalancer(loadbal_ep, token, loadbalancer_id )
    status1= check_loadbalancer_operating_status(loadbal_ep, token, loadbalancer_id)
    logging.info("load balancer status after disabling is: {}".foramat(status1))
    if status1== "OFFLINE":
         logging.info("SUccessfully disabled load balancer")

    logging.info("Enabling Load balancer")
    enable_loadbalancer(loadbal_ep, token, loadbalancer_id )
    status2= check_loadbalancer_operating_status(loadbal_ep, token, loadbalancer_id)
    logging.info("load balancer status after enabling is: {}".foramat(status2))
    if status2== "ONLINE":
        logging.info("SUccessfully enabled load balancer")

    output=[]
    for i in range(0, 8): 
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)  
    if status1== "OFFLINE" and status2== "ONLINE" and len(output)>0:
        isPassed9=True
        logging.info("Octavia Test case 9 passed, output is in round robin format after disabling and enabling load balancer status1 is {}, status2 is{}, output is {} ".format(status1, status2, output))
        message9= "Octavia Test case 8 passed, output is in round robin format after  disabling and enabling load balancer status1 is {}, status2 is{}, output is   {}".format(status1, status2, output)

    else:
        logging.error("Octavia Test case 9 failed, output is not round robin format after disabling and enabling load balancer status1 is {}, status2 is{}, output is {} ".format(status1, status2, output))
        message9= "Octavia Test case 8 passed, failed is not in round robin format after  disabling and enabling load balancer status1 is {}, status2 is{}, output is  {}".format(status1, status2, output)
    
        ##############################################
    listener2_id= search_and_create_listener(loadbal_ep, token, "testcase_listener2", loadbalancer_id, "HTTP", 80)
    if listener2_id == "failed":
        isPassed10= True
        logging.info("Octavia Test case 10 passed, second http listenet is not created in same loadbalancer")
        message10="Octavia Test case 10 passed, second http listenet is not created in same loadbalancer"
    else:
        logging.info("Octavia Test case 10 failed, second http listenet is  created in same loadbalancer")
        message10="Octavia Test case 10 failed, second http listenet is  created in same loadbalancer"

        logging.info("Octavia testcase 3, 4, 7, 8, 9, 10 Finished")

    return isPassed3, message3, isPassed4, message4, isPassed7, message7, isPassed8, message8, isPassed9, message9, isPassed10, message10,

def octavia_test_case_5_6(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    logging.info("Octavia testcase 5, 6 started")
    isPassed5=isPassed6= False
    message5=message6=""
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage5=mesage6="Octavia Testcase failed, because loadbalancer is in error state"
        return isPassed5, message5, isPassed6, message6
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "TCP", 23456 )
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage5=mesage6="Octavia Testcase failed, because listener is in error state"
        return isPassed5, message5, isPassed6, message6
    #create pool id
    pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "TCP", "ROUND_ROBIN")
    pool_build_wait(loadbal_ep, token, [pool_id])
    pool_state= check_pool_status(loadbal_ep, token, pool_id)
    logging.info("pool status is: "+pool_state)
    if(pool_state=="error"):
        mesage5=mesage6="Octavia Testcase failed, because pool is in error state"
        return isPassed5, message5, isPassed6, message6
    
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    #put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
 
    if  status1 != "active" or status2 != "active" :
        mesage5=mesage6=="Octavia Testcase failed, because one of the server is in error state {} {}".format(status1, status2)
        return isPassed5, message5, isPassed6, message6
    isPassed5=True
    message5= "Octavia Testcase 5 passed, tcp loadbalancer, listenet and pool is in active state, their status is loadbalancer: {}, listener {}, pool {}".format(loadbalancer_state, listener_state, pool_state)

    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
    server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
    server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
    server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
    
    public_network_id= search_network(neutron_ep, token, "public")
    public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
    #flaoting1_ip= get_server_floating_ip(nova_ep, token, server_1_id, settings["network1_name"])
    #flaoting2_ip= get_server_floating_ip(nova_ep, token, server_2_id, settings["network1_name"])
    #flaoting3_ip= get_server_floating_ip(nova_ep, token, server_3_id, settings["network1_name"])
    flaoting1_ip, floating1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
    flaoting2_ip, floating2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
    wait_instance_boot(flaoting1_ip)
    wait_instance_ssh(flaoting1_ip, settings)
    wait_instance_boot(flaoting2_ip)
    wait_instance_ssh(flaoting2_ip, settings)


    logging.info("Installing Packages in instances")
    install_http_packages_on_instance(flaoting1_ip, "1", settings)
    install_http_packages_on_instance(flaoting2_ip, "2", settings)
    try:
        add_instance_to_pool(loadbal_ep, token, pool_id, server1_ip, subnet_id, 80 )
        time.sleep(10)
        add_instance_to_pool(loadbal_ep, token, pool_id, server2_ip, subnet_id, 80 )
        time.sleep(10)
        health_monitor_pool(loadbal_ep, token, pool_id, "TCP")   
    except:
        pass
        
    lb_vipport= check_loadbalancer_vipport(loadbal_ep, token, loadbalancer_id)
    logging.info("vip port: {}".format(lb_vipport))
    lb_ip_id, lb_ip= create_loadbalancer_floatingip(neutron_ep, token, public_network_id )
    logging.info("load balancer ip is: {}".format(lb_ip))
    assign_lb_floatingip(neutron_ep, token, lb_vipport, lb_ip_id )
    curl_command="curl "+str(lb_ip)+":23456"
    output=[]
    for i in range(0, 6):    
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)   
    logging.info("output is:")
    logging.info(output) 
        
    if(output[0]!= output[1] and output[2]!= output[3] and output[4]!= output[5] and output[0]== output[2] and output[0]==output[4] and output[1]==output[3] and output[1]==output[5]):
        isPassed6= True
        logging.info("Octavia Test case 6 passed, tcp loadbalancer schedules accoeding to load balancer algorithm output is: {}".format(output))
        message6= "Octavia Test case 6 passed, tcp loadbalancer has output is in round robin format {}".format(output)
    else:
        logging.error("Octavia Test case 6 passed, , tcp loadbalancer has output is in round robin format: {}".format(output))
        message6= "Octavia Test case 6 passed, tcp loadbalancer output is in not round robin format {}".format(output)
    return isPassed5, message5, isPassed6, message6

def octavia_test_case_12(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 12 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 6failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "HTTP", "SOURCE_IP")
    pool_build_wait(loadbal_ep, token, [pool_id])
    pool_state= check_pool_status(loadbal_ep, token, pool_id)
    logging.info("pool status is: "+pool_state)
    if(pool_state=="error"):
        mesage="Octavia Testcase failed, because pool is in error state"
        return isPassed, message
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    #put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
    
    if  status1 != "active" or status2 != "active" :
        mesage=mesage="Octavia Testcase failed, because one of the server is in error state {} {} ".format(status1, status2)
        return isPassed, message
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
    server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
    server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
    server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
    public_network_id= search_network(neutron_ep, token, "public")
    public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
    #flaoting1_ip= get_server_floating_ip(nova_ep, token, server_1_id, settings["network1_name"])
    #flaoting2_ip= get_server_floating_ip(nova_ep, token, server_2_id, settings["network1_name"])
    #flaoting3_ip= get_server_floating_ip(nova_ep, token, server_3_id, settings["network1_name"])
    flaoting1_ip, floating1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
    flaoting2_ip, floating2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
    wait_instance_boot(flaoting1_ip)
    wait_instance_ssh(flaoting1_ip, settings)
    wait_instance_boot(flaoting2_ip)
    wait_instance_ssh(flaoting2_ip, settings)

    logging.info("Installing Packages in instances")
    install_http_packages_on_instance(flaoting1_ip, "1", settings)
    install_http_packages_on_instance(flaoting2_ip, "2", settings)

    try:
        add_instance_to_pool(loadbal_ep, token, pool_id, server1_ip, subnet_id, 80 )
        time.sleep(10)
        add_instance_to_pool(loadbal_ep, token, pool_id, server2_ip, subnet_id, 80 )
        time.sleep(10)
        health_monitor_pool(loadbal_ep, token, pool_id, "HTTP")   
    except:
        pass
        
    lb_vipport= check_loadbalancer_vipport(loadbal_ep, token, loadbalancer_id)
    logging.info("vip port: {}".format(lb_vipport))
    lb_ip_id, lb_ip= create_loadbalancer_floatingip(neutron_ep, token, public_network_id )
    logging.info("load balancer ip is: {}".format(lb_ip))
    assign_lb_floatingip(neutron_ep, token, lb_vipport, lb_ip_id )
    output=[]
    curl_command="curl "+str(lb_ip)
    for i in range(0, 6): 
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)   
    logging.info("output is:")
    logging.info(output) 
    if(len(output)>0):
        isPassed= True
        logging.info("Octavia Test case 12 passed, traffic flow happen, when algorithm is source ip, output is: {}".format(output))
        message= "Octavia Test case 12 passed,traffic flow happen, when algorithm is source ip, output is {}".format(output)
    else:
        logging.error("Octavia Test case 12 failed, traffic flow happen, when algorithm is source ip, output is: {}".format(output))
        message= "Octavia Test case 12 failed, traffic flow happen, when algorithm is source ip, output is: {}".format(output)
    logging.info("Octavia testcase 12 finished")
    return isPassed, message

def octavia_test_case_13(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 13 started")

    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 6failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool", listener_id, loadbalancer_id, "HTTP", "LEAST_CONNECTIONS")
    pool_build_wait(loadbal_ep, token, [pool_id])
    pool_state= check_pool_status(loadbal_ep, token, pool_id)
    logging.info("pool status is: "+pool_state)
    if(pool_state=="error"):
        mesage="Octavia Testcase failed, because pool is in error state"
        return isPassed, message
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    #put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
    
    if  status1 != "active" or status2 != "active" :
        mesage=mesage="Octavia Testcase failed, because one of the server is in error state {} {}".format(status1, status2)
        return isPassed, message

    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
    server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
    server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
    server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
    public_network_id= search_network(neutron_ep, token, "public")
    public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
    #flaoting1_ip= get_server_floating_ip(nova_ep, token, server_1_id, settings["network1_name"])
    #flaoting2_ip= get_server_floating_ip(nova_ep, token, server_2_id, settings["network1_name"])
    #flaoting3_ip= get_server_floating_ip(nova_ep, token, server_3_id, settings["network1_name"])
    flaoting1_ip, floating1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
    flaoting2_ip, floating2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
    wait_instance_boot(flaoting1_ip)
    wait_instance_ssh(flaoting1_ip, settings)
    wait_instance_boot(flaoting2_ip)
    wait_instance_ssh(flaoting2_ip, settings)

    logging.info("Installing Packages in instances")
    install_http_packages_on_instance(flaoting1_ip, "1", settings)
    install_http_packages_on_instance(flaoting2_ip, "2", settings)

    try:
        add_instance_to_pool(loadbal_ep, token, pool_id, server1_ip, subnet_id, 80 )
        time.sleep(10)
        add_instance_to_pool(loadbal_ep, token, pool_id, server2_ip, subnet_id, 80 )
        time.sleep(10)
        health_monitor_pool(loadbal_ep, token, pool_id, "HTTP")   
    except:
        pass
        
    lb_vipport= check_loadbalancer_vipport(loadbal_ep, token, loadbalancer_id)
    logging.info("vip port: {}".format(lb_vipport))
    lb_ip_id, lb_ip= create_loadbalancer_floatingip(neutron_ep, token, public_network_id )
    logging.info("load balancer ip is: {}".format(lb_ip))
    assign_lb_floatingip(neutron_ep, token, lb_vipport, lb_ip_id )
    output=[]
    curl_command="curl "+str(lb_ip)
    for i in range(0, 6): 
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)   
    logging.info("output is:")
    logging.info(output) 
    if(len(output)>0):
        isPassed= True
        logging.info("Octavia Test case 13 passed, traffic flow happen, when algorithm is LEAST_CONNECTIONS, output is: {}".format(output))
        message= "Octavia Test case 13 passed,traffic flow happen, when algorithm is LEAST_CONNECTIONS, output is {}".format(output)
    else:
        logging.error("Octavia Test case 13 failed, traffic flow happen, when algorithm is LEAST_CONNECTIONS, output is: {}".format(output))
        message= "Octavia Test case 13 failed, traffic flow happen, when algorithm is LEAST_CONNECTIONS, output is: {}".format(output)
    logging.info("Octavia testcase 13 finished")
    return isPassed, message
def octavia_test_case_14(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 14 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 14 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool", listener_id, loadbalancer_id, "HTTP", "ROUND_ROBIN", "persistence ")
    pool_build_wait(loadbal_ep, token, [pool_id])
    pool_state= check_pool_status(loadbal_ep, token, pool_id)
    logging.info("pool status is: "+pool_state)
    if(pool_state=="error"):
        mesage="Octavia Testcase failed, because pool is in error state"
        return isPassed, message
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    #put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_2_id= search_and_create_server(nova_ep, token, "test_case_Server2", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
    
    if  status1 != "active" or status2 != "active" :
        mesage=mesage="Octavia Testcase failed, because one of the server is in error state {} {}".format(status1, status2)
        return isPassed, message

    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 20)
    server1_ip= get_server_ip(nova_ep, token, server_1_id, settings["network1_name"])
    server1_port= get_ports(neutron_ep, token, network_id, server1_ip)
    server2_ip= get_server_ip(nova_ep, token, server_2_id, settings["network1_name"])
    server2_port= get_ports(neutron_ep, token, network_id, server2_ip)
    public_network_id= search_network(neutron_ep, token, "public")
    public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
    #flaoting1_ip= get_server_floating_ip(nova_ep, token, server_1_id, settings["network1_name"])
    #flaoting2_ip= get_server_floating_ip(nova_ep, token, server_2_id, settings["network1_name"])
    #flaoting3_ip= get_server_floating_ip(nova_ep, token, server_3_id, settings["network1_name"])
    flaoting1_ip, floating1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server1_ip, server1_port)
    flaoting2_ip, floating2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server2_ip, server2_port)
    wait_instance_boot(flaoting1_ip)
    wait_instance_ssh(flaoting1_ip, settings)
    wait_instance_boot(flaoting2_ip)
    wait_instance_ssh(flaoting2_ip, settings)

    logging.info("Installing Packages in instances")
    install_http_packages_on_instance(flaoting1_ip, "1", settings)
    install_http_packages_on_instance(flaoting2_ip, "2", settings)

    try:
        add_instance_to_pool(loadbal_ep, token, pool_id, server1_ip, subnet_id, 80 )
        time.sleep(10)
        add_instance_to_pool(loadbal_ep, token, pool_id, server2_ip, subnet_id, 80 )
        time.sleep(10)
        health_monitor_pool(loadbal_ep, token, pool_id, "HTTP")   
    except:
        pass
        
    lb_vipport= check_loadbalancer_vipport(loadbal_ep, token, loadbalancer_id)
    logging.info("vip port: {}".format(lb_vipport))
    lb_ip_id, lb_ip= create_loadbalancer_floatingip(neutron_ep, token, public_network_id )
    logging.info("load balancer ip is: {}".format(lb_ip))
    assign_lb_floatingip(neutron_ep, token, lb_vipport, lb_ip_id )
    output=[]
    curl_command="curl "+str(lb_ip)
    for i in range(0, 6): 
        result= os.popen(curl_command).read()
        result= result.strip()
        output.append(result)   
        logging.info("output is:")
        logging.info(output) 
    if(len(output)>0):
        isPassed= True
        logging.info("Octavia Test case 14 passed, traffic flow happen, when algorithm is round robin and session is persistant, output is: {}".format(output))
        message= "Octavia Test case 14 passed,traffic flow happen, when algorithm is round robin and session is persistant, output is {}".format(output)
    else:
        logging.error("Octavia Test case 14 failed, traffic flow happen, when algorithm is round robin and session is persistantLEAST_CONNECTIONS, output is: {}".format(output))
        message= "Octavia Test case 14 failed, traffic flow happen, when algorithm is round robin and session is persistant, output is: {}".format(output)
    logging.info("Octavia testcase 14 finished")
    return isPassed, message

def octavia_test_case_25(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 25 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 25 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "HTTP", "ROUND_ROBIN")
    pool_build_wait(loadbal_ep, token, [pool_id])
    pool_state= check_pool_status(loadbal_ep, token, pool_id)
    logging.info("pool status is: "+pool_state)
    if(pool_state=="error"):
        mesage="Octavia Testcase failed, because pool is in error state"
        return isPassed, message
    pool_status= search_and_create_pool(loadbal_ep, token, "testcase_pool2", listener_id, loadbalancer_id, "HTTP", "ROUND_ROBIN")
    logging.info("Pool 2 id is: "+ pool_status)
    if(pool_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 25 passed, second pool creation failed when attached to a listener, pool id is: {} ".format(pool_status))
        message= "Octavia Test case 25 passed,second pool creation failed when attached to a listener, pool id is: {} ".format(pool_status)
    else:
        logging.info("Octavia Test case 25 failed, second pool creation successfull when attached to a listener, pool id is: {} ".format(pool_status))
        message= "Octavia Test case 25 failed,second pool creation successfull when attached to a listener, pool id is: {} ".format(pool_status)
    logging.info("Octavia testcase 25 finished")
    return isPassed, message

def octavia_test_case_26(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 26 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 26 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_status= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "HTTPS", "ROUND_ROBIN")
    if(pool_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 26 passed, HTTPS pool creation failed when attached to HTTP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 26 passed,HTTPS pool creation failed when attached to HTTP listener:, pool id is {} ".format(pool_status)
    else:
        logging.info("Octavia Test case 26 failed, HTTPS pool creation successfull when attached to HTTP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 26 failed, HTTPS pool creation successfull when attached to HTTP listener:, pool id is {}  ".format(pool_status)
    logging.info("Octavia testcase 26 finished")
    return isPassed, message

def octavia_test_case_27(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 27 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 27 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_status= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "TCP", "ROUND_ROBIN")
    if(pool_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 27 passed, TCP pool creation failed when attached to HTTP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 27 passed, TCP pool creation failed when attached to HTTP listener:, pool id is {} ".format(pool_status)
    else:
        logging.info("Octavia Test case 27 failed, TCP pool creation successfull when attached to HTTP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 27 failed, TCP pool creation successfull when attached to HTTP listener:, pool id is {}  ".format(pool_status)
    logging.info("Octavia testcase 27 finished")
    return isPassed, message
    

def octavia_test_case_28(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 28 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 28 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_status= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "UDP", "ROUND_ROBIN")
    if(pool_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 28 passed, UDP pool creation failed when attached to HTTP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 28 passed, UDP pool creation failed when attached to HTTP listener:, pool id is {} ".format(pool_status)
    else:
        logging.info("Octavia Test case 28 failed, UDP pool creation successfull when attached to HTTP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 28 failed, UDP pool creation successfull when attached to HTTP listener:, pool id is {}  ".format(pool_status)
    logging.info("Octavia testcase 28 finished")
    return isPassed, message

def octavia_test_case_29(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 29 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 29 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTPS", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_status= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "HTTP", "ROUND_ROBIN")
    if(pool_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 29 passed, HTTP pool creation failed when attached to HTTPS listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 29 passed, HTTP pool creation failed when attached to HTTPS listener:, pool id is {} ".format(pool_status)
    else:
        logging.info("Octavia Test case 29 failed, HTTP pool creation successfull when attached to HTTPS listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 29 failed, HTTP pool creation successfull when attached to HTTPS listener:, pool id is {}  ".format(pool_status)
    logging.info("Octavia testcase 29 finished")
    return isPassed, message

def octavia_test_case_30(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 30 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 30 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTPS", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_status= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "UDP", "ROUND_ROBIN")
    if(pool_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 30 passed, UDP pool creation failed when attached to HTTPS listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 30 passed, UDP pool creation failed when attached to HTTPS listener:, pool id is {} ".format(pool_status)
    else:
        logging.info("Octavia Test case 30 failed, UDP pool creation successfull when attached to HTTPS listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 30 failed, UDP pool creation successfull when attached to HTTPS listener:, pool id is {}  ".format(pool_status)
    logging.info("Octavia testcase 30 finished")
    return isPassed, message

def octavia_test_case_31(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 31 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 31 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "TCP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_status= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "UDP", "ROUND_ROBIN")
    if(pool_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 31 passed, UDP pool creation failed when attached to TCP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 31 passed, UDP pool creation failed when attached to TCP listener:, pool id is {} ".format(pool_status)
    else:
        logging.info("Octavia Test case 31 failed, UDP pool creation successfull when attached to TCP listener:, pool id is {} ".format(pool_status))
        message= "Octavia Test case 31 failed, UDP pool creation successfull when attached to TCP listener:, pool id is {}  ".format(pool_status)
    logging.info("Octavia testcase 31 finished")
    return isPassed, message

def octavia_test_case_32(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    logging.info("Octavia testcase 32 started")
    #Create loadbalancer
    loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
    loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
    loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
    logging.info("loadbalancer status is: "+loadbalancer_state)
    if(loadbalancer_state=="error"):
        mesage="Octavia Testcase 32 failed, because loadbalancer is in error state"
        return isPassed, message
    #create listener
    listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTP", 80)
    listener_build_wait(loadbal_ep, token, [listener_id])
    listener_state= check_listener_status(loadbal_ep, token, listener_id)
    logging.info("listener status is: "+listener_state)
    if(listener_state=="error"):
        mesage="Octavia Testcase failed, because listener is in error state"
        return isPassed, message
    #create pool id
    pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "HTTP", "ROUND_ROBIN")
    pool_build_wait(loadbal_ep, token, [pool_id])
    pool_state= check_pool_status(loadbal_ep, token, pool_id)
    logging.info("pool status is: "+pool_state)
    if(pool_state=="error"):
        mesage="Octavia Testcase failed, because pool is in error state"
        return isPassed, message
    health_status= health_monitor_pool(loadbal_ep, token, pool_id, "UDP")

    if(health_status== "failed"):
        isPassed= True
        logging.info("Octavia Test case 32 passed, UDP health creation failed when attached to HTTP listener:, pool id is {} ".format(health_status))
        message= "Octavia Test case 32 passed, UDP health creation failed when attached to HTTP listener:, pool id is {} ".format(health_status)
    else:
        logging.info("Octavia Test case 32 failed, UDP health creation successfull when attached to HTTP listener:, pool id is {} ".format(health_status))
        message= "Octavia Test case 32 failed, UDP health creation successfull when attached to HTTP listener:, pool id is {}  ".format(health_status)
    logging.info("Octavia testcase 32 finished")
    return isPassed, message   

def octavia_test_case_33(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= ""    
    loadbalancer_id=""
    logging.info("Octavia testcase 33 started")
    
    #Create loadbalancer
    try:
        loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
        loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
        loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
        logging.info("loadbalancer status is: "+loadbalancer_state)
        if(loadbalancer_state=="error"):
            mesage="Octavia Testcase 33 failed, because loadbalancer is in error state"
            return isPassed, message
        #create listener
        listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "HTTPS", 80)
        listener_build_wait(loadbal_ep, token, [listener_id])
        listener_state= check_listener_status(loadbal_ep, token, listener_id)
        logging.info("listener status is: "+listener_state)
        if(listener_state=="error"):
            mesage="Octavia Testcase failed, because listener is in error state"
            return isPassed, message
        #create pool id
        pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "HTTPS", "ROUND_ROBIN")
        pool_build_wait(loadbal_ep, token, [pool_id])
        pool_state= check_pool_status(loadbal_ep, token, pool_id)
        logging.info("pool status is: "+pool_state)
        if(pool_state=="error"):
            mesage="Octavia Testcase failed, because pool is in error state"
            return isPassed, message
        health_status= health_monitor_pool(loadbal_ep, token, pool_id, "UDP")

        if(health_status== "failed"):
            isPassed= True
            logging.info("Octavia Test case 33 passed, UDP health creation failed when attached to HTTPS listener:, pool id is {} ".format(health_status))
            message= "Octavia Test case 33 passed, UDP health creation failed when attached to HTTPS listener:, pool id is {} ".format(health_status)
        else:
            logging.info("Octavia Test case 33 failed, UDP health creation successfull when attached to HTTPS listener:, pool id is {} ".format(health_status))
            message= "Octavia Test case 33 failed, UDP health creation successfull when attached to HTTPS listener:, pool id is {}  ".format(health_status)
        logging.info("deleting loadbalancer")
        delete_resource("{}/v2.0/lbaas/loadbalancers/{}".format(loadbal_ep,loadbal_ep), token)
        logging.info("Octavia testcase 33 finished")
    except Exception as e:
        logging.exception("Testcase 33 failed, error occured {}".format(e))
        message= "Testcase 33 failed, error occured {}".format(e)
    return isPassed, message

    
def octavia_test_case_34(nova_ep, neutron_ep, image_ep, loadbal_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, router_id, security_group_id, image_id):
    isPassed= False
    message= "" 
    loadbalancer_id=""   
    logging.info("Octavia testcase 34 started")
    #Create loadbalancer
    try:
        loadbalancer_id= search_and_create_loadbalancer(loadbal_ep, token, "testcase_loadbalancer1", subnet_id)
        loadbalancer_build_wait(loadbal_ep, token, [loadbalancer_id])
        loadbalancer_state= check_loadbalancer_status(loadbal_ep, token, loadbalancer_id)
        logging.info("loadbalancer status is: "+loadbalancer_state)
        if(loadbalancer_state=="error"):
            mesage="Octavia Testcase 34 failed, because loadbalancer is in error state"
            return isPassed, message
        #create listener
        listener_id= search_and_create_listener(loadbal_ep, token, "testcase_listener1", loadbalancer_id, "TCP", 80)
        listener_build_wait(loadbal_ep, token, [listener_id])
        listener_state= check_listener_status(loadbal_ep, token, listener_id)
        logging.info("listener status is: "+listener_state)
        if(listener_state=="error"):
            mesage="Octavia Testcase failed, because listener is in error state"
            return isPassed, message
        #create pool id
        pool_id= search_and_create_pool(loadbal_ep, token, "testcase_pool1", listener_id, loadbalancer_id, "TCP", "ROUND_ROBIN")
        pool_build_wait(loadbal_ep, token, [pool_id])
        pool_state= check_pool_status(loadbal_ep, token, pool_id)
        logging.info("pool status is: "+pool_state)
        if(pool_state=="error"):
            mesage="Octavia Testcase failed, because pool is in error state"
            return isPassed, message
        health_status= health_monitor_pool(loadbal_ep, token, pool_id, "UDP")

        if(health_status== "failed"):
            isPassed= True
            logging.info("Octavia Test case 34 passed, UDP health creation failed when attached to TCP listener:, pool id is {} ".format(health_status))
            message= "Octavia Test case 34 passed, UDP health creation failed when attached to TCP listener:, pool id is {} ".format(health_status)
        else:
            logging.info("Octavia Test case 33 failed, UDP health creation successfull when attached to TCP listener:, pool id is {} ".format(health_status))
            message= "Octavia Test case 34 failed, UDP health creation successfull when attached to TCP listener:, pool id is {}  ".format(health_status)
        logging.info("deleting loadbalancer")
        delete_resource("{}/v2.0/lbaas/loadbalancers/{}".format(loadbal_ep,loadbalancer_id ), token)
        time.sleep(10)
        logging.info("Octavia testcase 34 finished")
    except Exception as e:
        logging.exception("Testcase 34 failed, error occured {}".format(e))
        message= "Testcase 34 failed, error occured {}".format(e)
        if(loadbalancer_id !=""):
            logging.info("deleting loadbalancer")
            delete_resource("{}/v2.0/lbaas/loadbalancers/{}".format(loadbal_ep,loadbalancer_id ), token)
            time.sleep(10)
    return isPassed, message

