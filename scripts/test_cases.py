import requests
import json
import os
import sys
from automation_code import *
import argparse

def parse_arguments():
# Verify Arguments
    parser = argparse.ArgumentParser(description='Pass settings file, feature and deployment type for test cases')
    parser.add_argument('-s', '--settings',
                        help=' settings file',
                        required=True)
    parser.add_argument('-f', '--feature',
                        help='features enabled in deplyment',
                        required=True)
    parser.add_argument('-d', '--deployment',
                        help='deployment type, flex or ceph',
                        required=True)
    return parser.parse_args()

def read_settings(settings_file):
    settings=null
    #read settings from json file
    if os.path.exists(settings_file):
        try:
            with open(json_file) as data_file:
                settings = json.load(data_file)

        except:
            print("Failed to load settings file")
    else:
        print("\nFile not found!!! Exception Occurred \n")
    return settings

def get_authentication_token(username, password, neutron_ep):
    #authenticate user with keystone
    token= null
    payload= {"auth": {"identity": {"methods": ["password"],"password":
                      {"user": {"name": username, "domain": {"name": "Default"},"password": password} }},
                "scope": {"project": {"domain": {"id": "default"},"name": "admin"}}}}
    # Request Api for authentication
    res = requests.post(url+'/auth/tokens',
                        headers = {'content-type':'application/json'},
                        data=json.dumps(payload))
    #Validate Response
    if res.status_code == 200:
        print("Successfully Authenticated")
        token= res.headers.get('X-Subject-Token')
    else:
        print("Authenticated Failed")
        res.raise_for_status()
    return token

def setup_environment(keypair_name, security_group_name, token):
    #Basic Environment Setup
    create_keypair(settings["key_name"],token)
    create_security_group(settings["security_group"],token)
    add_icmp_rule(settings["security_group"],token)
    add_ssh_rule(settings["security_group"],token)
    create_keypair(settings["key_name"],token)
    image_verify(settings["image"],token)
    flavor_verify(settings["flavor"],token)

def numa_test_cases():
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

def main():
    #Parse Arguments
    arguments= parse_arguments()

    #Validate Arguments
    if arguments.feature != "numa":
        raise ValueError("Invalid Argument "+ arguments.feature)
    if arguments.deployment != "ceph":
        raise ValueError("Invalid Argument "+ arguments.feature)

    #Read Settings File
    settings= read_settings(arguments.settings)

    #Create Endpoints
    keystone_ep= settings.dashboard_ip+":5000/v3"
    #neutron_ep=
    #Get Authentication token
    token= get_authentication_token(settings.username, settings.password, keystone_ep )

    #Setup basic Environment
    setup_environment()

    #Run Test Cases
    if arguments.feature== "numa":
        #Run Numa Test Cases
        numa_test_cases()
    if arguments.feature== "hugepages":
        hugepages_test_cases()



    admin_id= find_admin_project_id(token)
    print(admin_id)




    #create_volume(data_info["vol_name1"],data_info["vol_size1"],admin_id,token)
    #attach_volume("myserver","vdn",admin_id,token)
    #delete_volume(data_info["vol_name1"],admin_id,token)
    #create_keypair(data_info["key_name"],data_info["fingerprint"],data_info["key_type"],data_info["public_key"],data_info["key_user_id"],token)
    #flavor_verify(data_info["flavor"],token)
    #image_verify(data_info["image"],token)
    #network_1_id= create_network(data_info["network_1"],data_info["mtu"],data_info["subnet_name"],data_info["cidr"],token)


if __name__ == "__main__":
    main()
