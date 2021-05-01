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

def volume_test_cases(image_ep, cinder_ep, keystone_ep, nova_ep, token, settings, baremetal_node_ips, server1_id, server_floating_ip, flavor_id, network_id, security_group_id, compute1):  
    project_id= find_admin_project_id(keystone_ep, token)
    test1=test2=test3=test4=test5=test6=test7=test8=test9=test10=test11=test12=""
   
    divider="\n--------------------------------------------------------------------------\n"
    message=divider
    testpassed=0
    logging.info("project is is: "+project_id)
    ##Create Volume
    logging.info("creating volume")
    volume_id= create_volume(cinder_ep, token, project_id)
    if(volume_id != None):
        logging.info("Volume id "+volume_id)
        volume_build_wait(cinder_ep, token, [volume_id], project_id)
        volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
        if(volume_status== "error"):
            test1= " \n Volume Testcase 1 failed, Volume creation failed, volume status is: {}".format(volume_status)
            message= message+ test1+divider
            delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,volume_id), token)
            return testpassed, message
        else:
            testpassed= testpassed+1
            test1= "\n Volume Testcase 1 Passed, Volume successfully created"
            message= message+ test1+divider
           
    else:
        test1= " \n Volume Testcase 1 failed, Volume creation failed"
        message= message+ test1+divider
        return testpassed, message
    
    ##Attach volume
    logging.info("Attaching volume to server")
    attach_volume(nova_ep, token, project_id, server1_id, volume_id)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    
    if(volume_status != "in-use"):    
        test2= " \n Volume Testcase 2 failed, Volume  attachment to server failed, volume status is: {}".format(volume_status)
        message= message+ test2+divider
        delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,volume_id), token)
        return testpassed, message
    else:
        test2= " \n Volume Testcase 2 passed, Volume successfully attached to server, volume status is: {}".format(volume_status)
        testpassed= testpassed+1
        message= message+ test2+divider

    ##Live migration of instance when volume attached
    logging.info("live migrating instance with attached volume")
    live_migrate, test3= live_migrate_instance(nova_ep, token, server1_id, server_floating_ip, compute1)
    if(live_migrate==True):
        testpassed= testpassed+1
        message= message+ test3+divider
    else:
        message= message+ test3+divider
    
    ##Cold migration of instance when volume attached
    logging.info("cold migrating instance with attached volume")
    coldmigration, test4= cold_migrate_instance(nova_ep, token, server1_id, server_floating_ip)
    if(coldmigration==True):
        testpassed= testpassed+1
        message= message+ test4+divider
    else:
        message= message+ test4+divider

    ##Create snapshot of instance
    logging.info("createing snapshot of instance")
    try:
        snapshot_server_id=instance_snapshot_id=""
        instance_snapshot_id= create_server_snapshot (nova_ep,token, server1_id, "testcase_server_snapshot")
    
        if (instance_snapshot_id == None):
            test5= "\n Volume Testcase 5 failed, creation of image snapshot failed"
            test6= "\n Volume Testcase 6 failed, creation of image from snapshot failed because snapshot creation failed"
        else:
            logging.info("wait for image to become active")
            time.sleep(30)
            test5= "\n Volume Testcase 5 passed, creation of image snapshot successfull"
            testpassed= testpassed+1

            #Now create instance from snapshot
            logging.info("creating instance from snapshot")
            snapshot_server_id= search_and_create_server(nova_ep, token, "testcase_server_from_snapshot", instance_snapshot_id, settings["key_name"], flavor_id, network_id, security_group_id) 
            server_build_wait(nova_ep, token, [snapshot_server_id])
            status= check_server_status(nova_ep, token, snapshot_server_id) 
            if status== "active":
                testpassed= testpassed+1
                test6= "\n Volume Testcase 6 passed, creation of image from snapshot is successfull, server status is: {}".format(status)

            else:
                test6= "\n Volume Testcase 6 failed, creation of image from snapshot is failed, server status is: {}".format(status) 
        if(snapshot_server_id != ""):
            delete_resource("{}/v2.1/servers/{}".format(nova_ep,snapshot_server_id), token)
        if(instance_snapshot_id) !="" :
            #delete_resource("{}/v2.1/flavors/{}".format(nova_ep,instance_snapshot_id), token)
            delete_resource("{}/v2/images/{}".format(image_ep, instance_snapshot_id), token)

            instance_snapshot_id
    except Exception as e:
        logging.info(e)
        test6=  "volume testcase 6 "+test6+ str(e)
        test5=  "volume testcase 5 "+test5+ str(e)
    message= message+ test5+divider
    message= message+ test6+divider
    
    ##Detach Volume
    logging.info("detaching volume from server")
    try:
        delete_resource("{}/v2.1/servers/{}/os-volume_attachments/{}".format(nova_ep,server1_id, volume_id), token)
        time.sleep(20)
    except Exception as e:
        logging.exception(e)
        test7=  "volume testcase 7 " +test7+str(e)
    volume_status= check_volume_status(cinder_ep, token, volume_id, project_id)
    if(volume_status != "in-use"):
        logging.info("volume successfully detached from server")
        testpassed= testpassed+1
        test7= "\n Volume Testcase 7 passed, volume successfully detached, its status is {}".format(volume_status)
        message= message+ test7+divider
    else:
        test7=  "\n Volume Testcase 7 failed, volume failed to detach, its status is {} ".format(volume_status)+ test7  
        message= message+ test7+divider
        delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,volume_id), token)
        return testpassed, message
    
    ## create volume snapshot
    logging.info("creating snapshot of volume")
    try: 
        snapshot_id= create_volume_snapshot(cinder_ep, token, project_id, volume_id, "testcase_volume_snapshot")
        logging.info("snapshot id is: {}".format(snapshot_id))
        if( snapshot_id == None):
            test8= "\n Volume Testcase 8 failed, creation of volume snapshot failed"
            test9= "\n Volume Testcase 9 failed, creation of volume from snapshot failed because snapshot creation failed"
        else:
            test8= "\n Volume Testcase 8 passed, creation of volume snapshot successfull"
            time.sleep(30)
            testpassed= testpassed+1
            #Now create volume from snapshot
            logging.info("creating volume from snapshot")
            snapshot_volume_id= create_volume_from_snapshot(cinder_ep, token, project_id, "testcase_volume_from_snapshot", snapshot_id)
            volume_build_wait(cinder_ep, token, [snapshot_volume_id], project_id)
            volume_status= check_volume_status(cinder_ep, token, snapshot_volume_id, project_id)
            if(volume_status== "error"):
                test9= "\n Volume Testcase 9 failed, creation of volume from snapshot failed, volume status is {}".format(volume_status)
            else:
                test9= "\n Volume Testcase 9 passed, creation of volume from snapshot is successfull, volume status is {}".format(volume_status)
                testpassed= testpassed+1
                delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,snapshot_volume_id), token)
                delete_resource("{}/v3/{}/snapshots/{}".format(cinder_ep, project_id,snapshot_id), token)
                
    except Exception as e:
        logging.exception(e)
        test8= "volume testcase 8 "+test8+str(e)
        test9=  "volume testcase 9 "+test9+ str(e)
    message= message+ test8+divider
    message= message+ test9+divider
    
    #upscale volume
    logging.info("upscaling volume")
    upscale_status= upscale_voume(cinder_ep, token, project_id, volume_id, "138")
    if(upscale_status == True):
        testpassed= testpassed+1
        test10="\n Volume Testcase 10 passed, volume successfully upscaled"
        time.sleep(30)
    else: 
        test10="\n Volume Testcase 10 failed, volume failed to upscale"
    message= message+ test10+divider
    
    #migrate_voume(cinder_ep, token, project_id, volume_id)

    #replicating volume
    logging.info("replicating volume")
    replicated_volume_id= replicate_volume(cinder_ep, token, project_id, "testcase_replicated_volume", volume_id)
    if(replicated_volume_id is not None):
        volume_build_wait(cinder_ep, token, [replicated_volume_id], project_id)
        volume_status= check_volume_status(cinder_ep, token, replicated_volume_id, project_id)
        if(volume_status != "error"):
            testpassed= testpassed+1
            test11="\n Volume Testcase 11 passed, volume successfully replicated its status is: {}".format(volume_status)
        else:
            test11="\n Volume Testcase 11 failed, volume failed to replicate byt its  status is: {}".format(volume_status)
        logging.info("deleting replicated volume")
        delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,replicated_volume_id), token)
    else:
        test11="\n Volume Testcase 11 failed, volume failed to replicate"
    message= message+ test11+divider

    #deleting volume
    logging.info("deleting volume")
    delete_resource("{}/v3/{}/volumes/{}".format(cinder_ep, project_id,volume_id), token)
    volume_id= search_volume(cinder_ep, token, "testcase_volume1", project_id)
    if volume_id == None:
        testpassed= testpassed+1
        test12="\n Volume Testcase 12 passed, volume successfully deleted"
    else:
        test12="\n Volume Testcase 12 failed, volume failed to delete"
    message= message+ test12+divider
    
    return testpassed, message


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
        time.sleep(30)
        if response==202:
            logging.info("confirming migrate")
            perform_action_on_server(nova_ep,token, server1_id, "confirmResize")
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
                    message="\n Volume Testcase 4 passed, cold migration of instance is successfull when volume is attached, status code is {}, old host {}, new host {} \n".format(response, old_host, new_host)
                else:
                    message= "\n Volume Testcase 4 failed, cold migration failed when volume is attached, ping failed after cold migration"
            else:
                logging.error("\n Volume Testcase 4 failed, cold migration of instance failed when volume is attached, status code is {}, old host name is {}, new host name is : {}".format(response, old_host, new_host))
                message="\n Volume Testcase 4 failed, cold migration of instance failed when volume is attached, status code is {},  old host name is {}, new host name is : {}".format(response, old_host, new_host)
        logging.info("restrting instance to ensure it is pingable")
        reboot_server(nova_ep,token, server1_id)
        time.sleep(10)
        wait_instance_boot(server_floating_ip)
    except Exception as e:
        logging.exception(e)
    return isPassed, message

def live_migrate_instance(nova_ep, token, server1_id, server_floating_ip, host):
    isPassed=False
    message=""
    try:
        old_host= get_server_host(nova_ep, token, server1_id)
        logging.info("old host is {}".format(old_host))
        logging.info("live migrating server")
        response= live_migrate_server(nova_ep,token, server1_id, host)
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
                logging.info("volume testcase 3 Passed")
                message="\n Volume Testcase 3 passed, live migration of instance is successfull when volume is attached, status code is {}, old host {}, new host {} \n".format(response, old_host, new_host)
            else:
                logging.error("\n Volume Testcase 3 failed when volume is attached, ping failed after live migration")
                message= "\n Volume Testcase 3 failed when volume is attached, ping failed after live migration"
        else:
            logging.error("\n Volume Testcase 3 failed, live migration of instance failed when volume is attached, status code is {},  old host name is {}, new host name is : {}".format(response, old_host, new_host))
            message="\n Volume Testcase 3 failed, live migration of instance failed when volume is attached, status code is {},  old host name is {}, new host name is : {}".format(response, old_host, new_host)
        logging.info("restrting instance to ensure it is pingable")
        reboot_server(nova_ep,token, server1_id)
        time.sleep(10)
        wait_instance_boot(server_floating_ip)
    except Exception as e:
        logging.exception(e)
    return isPassed, message

def detach_volume(nova_ep, token, project_id, server1_id, volume_id):
    try:
        detath_volume_to_server( nova_ep, token, project_id, server1_id, volume_id, "/dev/vdd")
        time.sleep(20)
    except Exception as e:
        logging.exception(e)