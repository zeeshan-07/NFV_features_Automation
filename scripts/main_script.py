import requests
import json
import os
import sys
from automation_code import *
from openstack import connection

def main(args):
    print(args)
    # reading & then conversion of json file into python dictionary
    json_file = "var_info.json"
    if os.path.exists(json_file):
        try:
            with open(json_file) as data_file:
                data_info = json.load(data_file)

        except:
            print("Failed to load Json_File")
    else:
        print("\nFile not found!!! Exception Occurred \n")



    username= (data_info['username'])
    password= (data_info["password"])


    #Authenticate User
    payload= {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "name": username,
                        "domain": {
                            "name": "Default"
                        },
                        "password": password}
                }
            },
            "scope": {
                "project": {
                    "domain": {
                        "id": "default"

                    },
                    "name": "admin"
                }
            }
        }
    }

    #Send Authentication Requesrt
    res = requests.post('http://100.82.39.60:5000/v3/auth/tokens',
                        headers = {'content-type':'application/json'},
                        data=json.dumps(payload))

    #Check Response
    if res.status_code == 200:
    #    print ('Successfully Authenticated with Keystone')
        token= res.headers.get('X-Subject-Token')
    else:
        res.raise_for_status()
    #print(res.text)
    token= res.headers.get('X-Subject-Token')
    res= json.loads(res.text)
    #print(json.dumps(res, indent=1))

    
    admin_id= find_admin_project_id(token)
    print(admin_id)

    ########### Basic Env Setup
    create_keypair(data_info["key_name"],token)
    create_security_group(data_info["security_group"],token)
    add_icmp_rule(data_info["security_group"],token)
    add_ssh_rule(data_info["security_group"],token)
    create_keypair(data_info["key_name"],token)
    image_verify(data_info["image"],token)
    flavor_verify(data_info["flavor"],token)




    if  args[1] == 'numa':
        #### Test Case_3 
        flavor_for_numaandhuge(data_info["flavor1"],token,4)
        create_network(data_info["network_1"],data_info["mtu"],data_info["subnet_name"],data_info["cidr"],token)
        create_server(data["server1"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        
        comm = "sudo -i virsh dumpxml " + data_info["server1"] + " | grep vcpupin | awk 'NR{count++} END {print count}'"  # noqa
        server_vcpus = ssh_into_compute_node(conn, command=comm)
        print (server_vcpus)
        flavor_vcpus = conn.get_flavor(data["numa_flavor"]).vcpus
        print(flavor_vcpus)
        if server_vcpus == flavor_vcpus:
            logger.info("Test Case 3 is successfully verified")
            logger.info("vcpus pinned are same as numa flavor vcpus")

        else:
            logger.info("Test is failed, vcpus are not equal")
        
        #delete_server(data_info["server1"],token)
        #delete_flavor(data_info["flavor1"],token)

        #### Test case_5
        flavor_for_numaandhuge(data_info["flavor1"],token,80)
        create_server(data["server1"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        create_server(data["server2"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        server_status= check_server_status(data_info["server2"],token)
        if server_status == 'false':
            print("Test case 5 Successfully passed")
        else:
            print("Failed to perform Test caser 5")
        #delete_server(data_info["server1"],token)
        #delete_server(data_info["server2"],token)
        #delete_flavor(data_info["flavor1"],token)
        
        
        ######## Test case 6 
        flavor_for_numaandhuge(data_info["flavor1"],token,40)
        create_server(data["server1"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        create_server(data["server2"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        create_server(data["server3"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        server_status= check_server_status(data_info["server3"],token)
        if server_status == 'false':
            print("Test case 6 Successfully passed")
        else:
            print("Failed to perform Test caser 6")
        #delete_server(data_info["server1"],token)
        #delete_server(data_info["server2"],token)
        #delete_server(data_info["server3"],token)
        #delete_flavor(data_info["flavor1"],token)

        ######## Test cases 7
        flavor_for_numaandhuge(data_info["flavor1"],token,4)
        create_server(data["server1"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)

        vm1_id = conn.get_server('numa7_vm1')
        vm2_id = conn.get_server('numa7_vm2')
        for i in range(1, 5):
            comm_1 = "sudo -i virsh dumpxml " + vm1_id + " | grep cpuset | gawk 'FNR == " + i + " {print $2}' FPAT='[0-9]+'"  # noqa
            comm_2 = "sudo -i virsh dumpxml " + vm2_id + " | grep cpuset | gawk 'FNR == " + i + " {print $2}' FPAT='[0-9]+'"  # noqa

            output_1 = ssh_into_compute_node(conn, command=comm_1)
            output_2 = ssh_into_compute_node(conn, command=comm_2)
            if output_1 != output_2:
                logger.info("Cpus are not equal: Test is going well")

            else:
                logger.info("Cpus are equal: Test is Failed")
                logger.info("Verification of Test case 7 is failed")
                logger.info("Exiting from loop")
                break
        
        ###### Test Case 8

        ###### Test Cases 9
        flavor_for_numaandhuge(data_info["flavor1"],token,40)
        create_server(data["server1"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        create_server(data["server2"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)

        conn.stop_server(data_info["server1"])
        conn.stop_server(data_info["server2"])
        create_server(data["server2"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        server_status= check_server_status(data_info["server3"],token)
        if server_status == 'false':
            print("Test case 6 Successfully passed")
        else:
            print("Failed to perform Test caser 6")
        #delete_server(data_info["server1"],token)
        #delete_server(data_info["server2"],token)
        #delete_server(data_info["server3"],token)
        #delete_flavor(data_info["flavor1"],token)

        ##### Test Case 10

        ##### Test Caes 11
        flavor_for_numaandhuge(data_info["flavor1"],token,4)
        create_server(data["server1"],data_info["image"],data_info["key_name"],data_info["flavor1"],data_info["net_1"],data_info["security_group"],token)
        #migrate_server(token)

    else:
        print ('Please pass feature name')

    
    if args[0] == 'ceph' :
        print(args[1] +" Feature validation with ceph")

    else:
        print("Please pass backend storage")

    #create_volume(data_info["vol_name1"],data_info["vol_size1"],admin_id,token)
    #attach_volume("myserver","vdn",admin_id,token)
    #delete_volume(data_info["vol_name1"],admin_id,token)
    #create_keypair(data_info["key_name"],data_info["fingerprint"],data_info["key_type"],data_info["public_key"],data_info["key_user_id"],token)
    #flavor_verify(data_info["flavor"],token)    
    #image_verify(data_info["image"],token)
    #network_1_id= create_network(data_info["network_1"],data_info["mtu"],data_info["subnet_name"],data_info["cidr"],token)

main(sys.argv[1:])


