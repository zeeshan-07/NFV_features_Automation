from openstack_functions import *
import paramiko


def volume_build_wait(cinder_ep, token, volume_ids, project_id):
    while True:
        flag=0
        for volume in volume_ids:
            status= check_volume_status(cinder_ep, token, volume, project_id)
            print(status)
            if  (status == "creating"):
                logging.info("Waiting for volume/s to build")
                flag=1
                time.sleep(10)
        if flag==0:
            break

def volume_test_cases(cinder_ep, keystone_ep, nova_ep, token, settings, baremetal_node_ips, server1_id, server2_id, server_floating_ip):  
    project_id= find_admin_project_id(keystone_ep, token)
    test1=test2=test3=test4=test5=test6=test7=test8=test9=""
    message=""
    testpassed=0
    logging.info("project is is: "+project_id)
    volume_id= create_volume(cinder_ep, token, project_id)
    if(volume_id != None):
        logging.info("Volume id "+volume_id)
        volume_build_wait(cinder_ep, token, [volume_id], project_id)
        volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
        if(volume_status== "error"):
            test1= " \n Volume Testcase 1 failed, Volume creation failed, volume status is: {}".format(volume_status)
            message= message+ test1
            return testpassed, message
        else:
            testpassed= testpassed+1
            message= message+ test1
            test1= "\n Volume Testcase 1 Passed, Volume successfully created"
    else:
        test1= " \n Volume Testcase 1 failed, Volume creation failed"
        message= message+ test1
        return testpassed, message


    attach_volume(nova_ep, token, project_id, server1_id, volume_id)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    
    if(volume_status != "in-use"):    
        test2= " \n Volume Testcase 2 failed, Volume  attachment to server failed, volume status is: {}".format(volume_status)
        message= message+ test2
        return testpassed, message
    else:
        test2= " \n Volume Testcase 2 passed, Volume successfully attached to server, volume status is: {}".format(volume_status)
        testpassed= testpassed+1
        message= message+ test2

    coldmigration, test3= cold_migrate_instance(nova_ep, token, server1_id, server_floating_ip)
    if(coldmigration==True):
        testpassed= testpassed+1
        message= message+ test3
    else:
        message= message+ test3
    
    live_migrate, test4= cold_migrate_instance(nova_ep, token, server1_id, server_floating_ip)
    if(live_migrate==True):
        testpassed= testpassed+1
        message= message+ test4
    else:
        message= message+ test4


    return testpassed, message





    
 

        
        
        #       delete_resource("{}/v2.1/servers/{}/os-volume_attachments/{}".format(nova_ep,server1_id, volume_id), token)
        #volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
        #print("volume status is: "+volume_status)
        #time.sleep(5)
       
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    print("volume status is: "+volume_status)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    print("volume status is: "+volume_status)
    time.sleep(20)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    
    print("volume status is: "+volume_status)
    time.sleep(5)
def create_volume(cinder_ep, token, project_id):
    volume_id= None
    try:
        volume_id= search_and_create_volume(cinder_ep, token, project_id, "testcase_volume1", 8)
    except Exception as e:
        logging.exception(e)
    return volume_id
def attach_volume(nova_ep, token, project_id, server1_id, volume_id):
    try:
        attach_volume_to_server( nova_ep, token, project_id, server1_id, volume_id, "/dev/vdd")
        time.sleep(20)
    except Exception as e:
        logging.exception(e)
def cold_migrate_instance(nova_ep, token, server1_id, server_floating_ip):
    isPassed=False
    message=""
    try:
        old_host= get_server_host(nova_ep, token, server1_id)
        logging.info("old host is {}".format(old_host))
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
            if(response == 202 and new_host != old_host):
                response2 = os.system("ping -c 3 " + server_floating_ip)
                if response2 == 0:
                    isPassed= True
                    logging.info ("Ping successfull!")
                    message="\n Volume Testcase 3 passed, cold migration of instance is successfull, status code is {}, old host {}, new host {} \n".format(response, old_host, new_host)
                else:
                    message= "\n Volume Testcase 3 failed, cold migration failed , ping failed after cold migration"
            else:
                logging.error("\n Volume Testcase 3 failed, cold migration of instance failed, status code is {}, old host name is {}, new host name is : {}".format(response, old_host, new_host))
                message="\n Volume Testcase 3 failed, cold migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, old_host, new_host)
        logging.info("restrting instance to ensure it is pingable")
        reboot_server(nova_ep,token, server_id)
        time.sleep(10)
        wait_instance_boot(server_floating_ip)
    except Exception as e:
        logging.exception(e)
    return isPassed, message

def live_migrate_instance(nova_ep, token, server1_id, server_floating_ip):
    isPassed=False
    message=""
    try:
        old_host= get_server_host(nova_ep, token, server1_id)
        logging.info("old host is {}".format(old_host))
        logging.info("live migrating server")
        response= live_migrate_server(nova_ep,token, server1_id)
        logging.info("migration status code is: {}".format(response))
        logging.info("waiting for migration")
        time.sleep(30)
        wait_instance_boot(server_floating_ip)
        new_host= get_server_host(nova_ep, token, server1_id)
        logging.info("new host is: "+new_host)
        if(response == 202 and new_host != old_host):
            response2 = os.system("ping -c 3 " + server_floating_ip)
            if response2 == 0:
                isPassed= True
                logging.info ("Ping successfull!")
                logging.info("DVR test Case 31 Passed")
                message="\n Volume Testcase 4 passed, live migration of instance is successfull, status code is {}, old host {}, new host {} \n".format(response, old_host, new_host)
            else:
                logging.error("\n Volume Testcase 3 failed, ping failed after live migration")
                message= "\n Volume Testcase 3 failed, ping failed after live migration"
        else:
            logging.error("\n Volume Testcase 3 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, old_host, new_host))
            message="\n Volume Testcase 3 failed, live migration of instance failed, status code is {},  old host name is {}, new host name is : {}".format(response, old_host, new_host)
        logging.info("restrting instance to ensure it is pingable")
        reboot_server(nova_ep,token, server_id)
        time.sleep(10)
        wait_instance_boot(server_floating_ip)
    except Exception as e:
        logging.exception(e)
    return isPassed, message
