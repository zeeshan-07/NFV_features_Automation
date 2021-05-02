from openstack_functions import *
import logging
import paramiko
import os
import time
import math
import pexpect
from subprocess import Popen, PIPE
import subprocess



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

def barbican_test_case_1(nova_ep, neutron_ep, image_ep, barbican_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    key= create_ssl_certificate(settings)
    image_signature= sign_image(settings)
    barbican_key_id= add_key_to_store(barbican_ep, token, key)

    image_id= create_barbican_image(image_ep, token, "barbican", "bare", "qcow2", "public", image_signature, barbican_key_id)
    image_file= open(os.path.expanduser(settings["image_file"]), 'rb')
    upload_file_to_image(image_ep, token, image_file, image_id)

    logging.info("Barbican Test Case 1 running")
    isPassed= False
    message=""
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False)
    #search and create server
    server_1_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_1_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    if  status1 == "error":
        logging.error("Barbican testcase 1 failed")
        logging.error("Instances creation failed")
        message="instance creation failed with signed image"
    else:
        isPassed=True
        message="Barbican testcase 1 passed, instance creation successfull with signed image, instance status is: {}".format(status1)
        logging.info("Barbican testcase 1 passed, instance creation successfull with signed image, instance status is: {}".format(status1))
    return isPassed, message

def barbican_test_case_1_2_3_4(barbican_ep, token):  
    isPassed1=isPassed2=isPassed3=isPassed4=False
    message1= message2=message3=message4=""

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
            message3="Barbican testcase 3 passed, secret successfully created and payload verified, payload received is: {}".format(payload)
def barbican_test_case_5(barbican_ep, token):  
    isPassed=False
    message1=""
    try:
        #Generating Symmetric key Key
        secret_id= add_symmetric_key_to_store(barbican_ep, token)
        if secret_id != "":
            isPassed1=True
            message1= "Barbican testcase 5 passed, symmetric key successfully created, its id is: {}".format(secret_id)
            time.sleep(5)
            #searching secret
            logging.info("searching secret")
            search_secret= get_secret(barbican_ep, token, secret_id)
            if(search_secret== None):
                message2= "Barbican testcase 2 failed, secret not found in list"
            else:
                isPassed2=True
                message2= "Barbican testcase 2 passed, secret  found in list"
                logging.info("Barbican testcase 2passed, secret successfully created and payload verified, payload received is: {}".format(payload))
            
            #else: 
            #    message3="Barbican testcase 3 failed, secret created but verification failed, payload received is: {}".format(payload)
            #    logging.error("Barbican testcase 3 failed, secret created but verification failed, payload received is: {}".format(payload))

            #Delete Secret
            logging.info("Delete Secret")
            delete_resource("{}/v1/secrets/{}".format(barbican_ep, secret_id), token)
            #searching secret
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
        logging.except(e)   
        message1= "Barbican testcase 5 failed/ error occured"
        message= "Barbican testcase 5 failed/ error occured"
        message= "Barbican testcase 5 failed/ error occured"
        message= "Barbican testcase 5 failed/ error occured"

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
                isPassed1=True
                message= "Barbican testcase 5 passed, symmetric key successfully created, its id is: {}".format(secret_id)
    
        else:
            message= "Barbican testcase 5 failed, symmetric key not created"
    except Exception as e:
        message= "Barbican testcase 5 failed/ error occured"
        logging.except(e)
        
    return isPassed, message
