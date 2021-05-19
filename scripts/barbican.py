from openstack_functions import *
import logging
import paramiko
import os
import time
import math
import pexpect
from subprocess import Popen, PIPE
import subprocess
from volume import *



'''
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
def ssh_conne(server1, server2, settings):
    try:
        command= "ssh-keygen -R {}".format(server1)
        os.system(command)
    except:
        pass
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
'''
def create_ssl_certificate(settings):
    logging.info("Generating Certificate")
    os.popen("openssl genrsa -out ~/testcase_private_key.pem 1024")
    time.sleep(2)
    os.popen("openssl rsa -pubout -in ~/testcase_private_key.pem -out ~/testcase_public_key.pem")
    time.sleep(2)
    proc = subprocess.Popen("openssl req -new -key ~/testcase_private_key.pem -out ~/testcase_cert_request.csr", shell=True, stdin=PIPE)
    time.sleep(2)
    s= "aa\naa\naa\naa\naa\naa\naa\naaaa\naaaa\n"
    s= s.encode('utf-8')
    proc.communicate(s)
    time.sleep(10)    
    os.popen("openssl x509 -req -days 14 -in ~/testcase_cert_request.csr -signkey ~/testcase_private_key.pem -out ~/x509_testcase_signing_cert.crt")
    time.sleep(4)
    private_key=os.popen("base64 ~/x509_testcase_signing_cert.crt") 
    time.sleep(4)
    private_key= private_key.read()
    return private_key
def sign_image(settings):
    #Sign image with Private Key
    logging.info("Signing image with private key")
    command= "openssl dgst -sha256 -sign ~/testcase_private_key.pem -sigopt rsa_padding_mode:pss -out ~/testcase_cirros-0.4.0.signature {}".format(os.path.expanduser(settings["image_file"]))
    os.popen(command)
    time.sleep(4)
    os.popen("base64 -w 0 ~/testcase_cirros-0.4.0.signature  > ~/testcase_cirros-0.4.0.signature.b64")
    time.sleep(4)
    image_signature= os.popen("cat ~/testcase_cirros-0.4.0.signature.b64")
    image_signature=image_signature.read()
    print(image_signature)
    return image_signature


def barbican_test_case_1_2_3_4(barbican_ep, token):  
    isPassed1=isPassed2=isPassed3=isPassed4=False
    message1= message2=message3=message4=""
    try:
        #Creating Secret
        logging.info("Creating Secret")
        secret_id= create_secret(barbican_ep, token, "testcae_secret", "test_case payload")
        if secret_id != "":
            isPassed1=True
            message1= "Barbican testcase 1 passed, secret successfully created, its id is: {}".format(secret_id)
            time.sleep(5)
            #searching secret
            logging.info("searching secret")
            search_secret= get_secret(barbican_ep, token, secret_id)
            if(search_secret== None):
                message2= "Barbican testcase 2 failed, secret not found in list"
            else:
                isPassed2=True
                message2= "Barbican testcase 2 passed, secret  found in list"
            
            #updating secret
            #logging.info("updating secret")
            #update_status= update_secret(barbican_ep, token, secret_id,"test_case payload" )
            #if (update_status== True):
            #    isPassed3= True
            #    message3= "Barbican testcase 3 passed, secret updated"
            #else:
            #     message3= "Barbican testcase 3 failed, secret not updated"
            
            #Get Payload
            logging.info("Getting Payload")
            payload= get_payload(barbican_ep, token, secret_id)
            if(payload== "test_case payload"):
                isPassed3=True
                message3="Barbican testcase 3 passed, secret successfully created and payload verified, payload , expected is 'test_case payload', received is: {}".format(payload)
            else:
                    message3="Barbican testcase 3 failed, failed to verify payload, expected is 'test_case payload',  received is: {}".format(payload)

            #Delete Secret
            logging.info("Delete Secret")
            delete_resource("{}/v1/secrets/{}".format(barbican_ep, secret_id), token)
            #searching secret
            logging.info("verifying secret deletion")
            search_secret= get_secret(barbican_ep, token, secret_id)
            if(search_secret != None):
                message4= "Barbican testcase 4 failed, secret not deleted"
            else:
                isPassed4=True
                message4= "Barbican testcase 4 passed, secret successfully deleted"

        else:
            message1= "Barbican testcase 1 failed, secret creation failed"
            message2= "Barbican testcase 2 failed, secret creation failed"
            message3= "Barbican testcase 3 failed, secret creation failed"
            message4= "Barbican testcase 4 failed, secret creation failed"
    except Exception as e: 
        logging.exception(e)   
        message1= "Barbican testcase 1 failed/ error occured"
        message2= "Barbican testcase 2 failed/ error occured"
        message3= "Barbican testcase 3 failed/ error occured"
        message4= "Barbican testcase 4 failed/ error occured"
    
    return isPassed1, message1, isPassed2, message2, isPassed3, message3, isPassed4, message4

def barbican_test_case_5(barbican_ep, token):  
    isPassed=False
    message=""
    try:
        #Generating Symmetric key Key
        secret_id= add_symmetric_key_to_store(barbican_ep, token)
        if secret_id != "":
            time.sleep(10)
            #searching secret
            logging.info("searching secret")
            search_secret= get_key(barbican_ep, token, secret_id)
            if( search_secret != None):
                isPassed=True
                message= "Barbican testcase 5 passed, symmetric key successfully created, its id is: {}".format(secret_id)
    
        else:
            message= "Barbican testcase 5 failed, symmetric key not created"
    except Exception as e:
        message= "Barbican testcase 5 failed/ error occured"
        logging.exception(e)
        
    return isPassed, message

def barbican_test_case_6_7_8_9(keystone_ep, cinder_ep, nova_ep, neutron_ep, image_ep, barbican_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, flavor_id):  
    logging.info("Barbican Test Case 7 running")
    isPassed6=isPassed7= isPassed8=isPassed9=False
    message6= message7=message8= message9=server_1_id= image_id=volume_id=project_id=""
    try:
        key= create_ssl_certificate(settings)
        image_signature= sign_image(settings)
        barbican_key_id= add_key_to_store(barbican_ep, token, key)

        image_id= create_barbican_image(image_ep, token, "barbican", "bare", "qcow2", "public", image_signature, barbican_key_id)
        status= get_image_status(image_ep, token, image_id)
        if status== "queued":
            image_file= open(os.path.expanduser(settings["image_file"]), 'rb')
            upload_file_to_image(image_ep, token, image_file, image_id)
            time.sleep(5)
                
        status= get_image_status(image_ep, token, image_id)
        if status== "active":
            isPassed6=True
            message6= "Barbican testcase 6 passed, image signature successfully validated, image status is {}".format(status)
            
            #creating server
            server_1_id= search_and_create_server(nova_ep, token, "barbican_server", image_id, settings["key_name"], flavor_id,  network_id, security_group_id)
            server_build_wait(nova_ep, token, [server_1_id])
            status1= check_server_status(nova_ep, token, server_1_id)
            if  status1 == "error":
                logging.error("Barbican testcase 7 failed")
                logging.error("Instances creation failed")
                message7="Barbican testcase 7 failed, instance creation failed with signed image, its status is {}".format(status1)
            else: 
                isPassed7=True
                message7="Barbican testcase 7 passed, instance successfully created  with signed image, its status is {}".format(status1)
            
            #Creating Volume
            project_id= find_admin_project_id(keystone_ep, token)
            volume_id= search_and_create_volume(cinder_ep, token, project_id, "barbican_volume", 8,image_id)
            if(volume_id != None):
                logging.info("Volume id "+volume_id)
                volume_build_wait(cinder_ep, token, [volume_id], project_id)
                volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
                if(volume_status== "error"):
                    message8= "Barbican testcase 8 failed, Volume creation failed with signed image, volume status is: {}".format(volume_status)
                    message9= "Barbican testcase 9 failed, image validation for volume failed, because volume is not created"
                    delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,volume_id), token)
                else:
                    isPassed8= True
                    message8= "Barbican testcase 8 passed, Volume creation successfull with signed image, volume status is: {}".format(volume_status)
                    volume_metadata= get_volume_metadata(cinder_ep, token, volume_id, project_id)
                    print(volume_metadata)
                    if( "'signature_verified': 'True'" in str(volume_metadata)):
                        isPassed9= True
                        message9= "Barbican testcase 9 passed, image signature for volume is is successfull, {}, ".format(volume_metadata)
                    else:
                        message9= "Barbican testcase 9 failed, image signature for volume is failed, {}, ".format(volume_metadata)

        else:
            message6= "Barbican testcase 6 failed, image signature validation failed, image status is {}".format(status)
            message7= "Barbican testcase 7 failed, image creation failed, instance not created"
            message8= "Barbican testcase 8 failed, image signature validation failed, volume not crerated"
            message9= "Barbican testcase 9 failed, volume creation failed, due to image varification failed"
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(image_id != ""):
            logging.info("deleting image")
            delete_resource("{}/v2/images/{}".format(image_ep, image_id), token)
        if(volume_id !=""):
            delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,volume_id), token)

    except Exception as e:
        message6= "Barbican testcase 6 failed/ error occured"
        message7= "Barbican testcase 7 failed/ error occured"
        message8= "Barbican testcase 8 failed/ error occured"
        message9= "Barbican testcase 9 failed/ error occured"
        logging.exception(e)
        if(server_1_id != ""):
            logging.info("deleting all servers")
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
        if(image_id != ""):
            logging.info("deleting image")
            delete_resource("{}/v2/images/{}".format(image_ep, image_id), token)
        if(volume_id !=""):
            delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,volume_id), token)


    return isPassed6, message6, isPassed7, message7, isPassed8, message8, isPassed9, message9


def barbican_volume_test_case(nova_ep, neutron_ep, image_ep, cinder_ep, keystone_ep, token, settings, baremetal_node_ips, flavor_id, network1_id, security_group_id, image_id):
    message=""
    testcases_passed= 0
    logging.info("starting volume testcases")
    server1_id=floating_1_ip_id=""
    compute0 =  [key for key, val in baremetal_node_ips.items() if "compute-0" in key]
    compute0= compute0[0]
    compute1 =  [key for key, val in baremetal_node_ips.items() if "compute-1" in key]
    compute1= compute1[0]

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