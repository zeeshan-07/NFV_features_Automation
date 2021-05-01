import requests
import json
import os
import time
import logging
import paramiko

def send_get_request(api_url, token, header="application/json"):
    try:
        return requests.get(api_url, headers= {'content-type': header, 'X-Auth-Token': token}) 
    except Exception as e:
        logging.error( "request processing failure ", stack_info=True)
        logging.exception(e)

def send_put_request(api_url, token, payload, header='application/json'):
    try:
       return requests.put(api_url, headers= {'content-type':header, 'X-Auth-Token': token}, data=json.dumps(payload))
    except Exception as e:
        logging.error( "request processing failure ", stack_info=True)
        logging.exception(e)

def send_post_request(api_url, token, payload, header='application/json'):
    try:
        #'OpenStack-API-Version': 'compute 2.74',
        return requests.post(api_url, headers= {'content-type':header, 'OpenStack-API-Version': 'compute 2.74', 'X-Auth-Token': token}, data=json.dumps(payload))
    except Exception as e:
       logging.error( "request processing failure ", stack_info=True)
       logging.exception(e)
def send_delete_request(api_url, token, header='application/json' ):
    try:
        requests.delete(api_url, headers= {'content-type':header, 'X-Auth-Token': token})
        time.sleep(5)
    except Exception as e:
       logging.error( "request processing failure ", stack_info=True)
       logging.exception(e)
def delete_resource(api_url, token):
    send_delete_request(api_url, token)


def parse_json_to_search_resource(data, resource_name, resource_key, resource_value, return_key):
    data= data.json()
    for res in (data[resource_name]):
        if resource_value in res[resource_key]:
            logging.warning("{} already exists".format(resource_value))
            return res[return_key]
            break
    else:
        logging.info("{} does not exist".format(resource_value))

def get_authentication_token(keystone_ep, username, password):
    #authenticate user with keystone
    payload= {"auth": {"identity": {"methods": ["password"],"password":
                      {"user": {"name": username, "domain": {"name": "Default"},"password": password} }},
                "scope": {"project": {"domain": {"id": "default"},"name": "admin"}}}}
    logging.debug("authenticating user")
    response= send_post_request("{}/v3/auth/tokens".format(keystone_ep), None, payload)
    logging.info("successfully authenticated") if response.ok else response.raise_for_status()
    return response.headers.get('X-Subject-Token')
def search_network(neutron_ep, token, network_name):
    #get list of networks
    response= send_get_request("{}/v2.0/networks".format(neutron_ep), token)
    logging.info("successfully received networks list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "networks", "name", network_name, "id")
def get_network_detail(neutron_ep, token, network_id):
    #get list of networks
    response= send_get_request("{}/v2.0/networks/{}".format(neutron_ep, network_id), token)
    logging.info("successfully received networks list") if response.ok else response.raise_for_status()
    response= response.json()
    return response
'''
Networks
'''
def create_network(neutron_ep, token, network_name, mtu_size, network_provider_type, is_external):
    #create network
    payload= {
        "network": {
            "name": network_name,
            "admin_state_up": True,
            "mtu": mtu_size,
            "provider:network_type": network_provider_type,
            "router:external": is_external,
            "provider:physical_network": "physint"
            }
        }

    response= send_post_request('{}/v2.0/networks'.format(neutron_ep), token, payload)
    logging.debug(response.text)
    logging.info("successfully created network {}".format(network_name)) if response.ok else response.raise_for_status()
    data=response.json()
    return data['network']['id']
def search_and_create_network(neutron_ep, token, network_name, mtu_size, network_provider_type, is_external):
    network_id= search_network(neutron_ep, token, network_name)    
    if network_id is None:
        network_id =create_network(neutron_ep, token, network_name, mtu_size, network_provider_type, False)  
    logging.debug("network id is: {}".format(network_id))
    return network_id
def create_port(neutron_ep, token, network_id, subnet_id, name, property=None ):
    payload= {"port": {
        "binding:vnic_type": "direct", 
        "network_id": network_id, 
	    "admin_state_up": 'true', 
        "fixed_ips": [{"subnet_id": subnet_id}], "name": name}}
    
    payload_port_property= {"binding:profile": {"capabilities": ["switchdev"]},
}
    if property is not None:
        payload= {"port":{**payload["port"], **payload_port_property}}
    response= send_post_request('{}/v2.0/ports'.format(neutron_ep), token, payload)
    print(response.text)
    logging.info("successfully created port") if response.ok else response.raise_for_status()
    data=response.json()
    return data["port"]["id"], data["port"]["fixed_ips"][0]["ip_address"]

'''
Subnets
'''
def search_subnet(neutron_ep, token, subnet_name):
    #get list of subnets
    response= send_get_request("{}/v2.0/subnets".format(neutron_ep), token)
    logging.info("Successfully Received Subnet List") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "subnets", "name", subnet_name, "id")

def create_subnet(neutron_ep, token, subnet_name, network_id, cidr, external= False, gateway=None, pool_start= None, pool_end= None):
    #create internal subnet
    payload= {
        "subnet": {
            "name": subnet_name,
            "network_id": network_id,
            "ip_version": 4,
            "cidr": cidr
            }
        }
    payload_external_subnet={"enable_dhcp": "true","gateway_ip": gateway,
               "allocation_pools": [{"start": pool_start, "end": pool_end}]}
    if external== True:
        payload= {"subnet":{**payload["subnet"], **payload_external_subnet}}
    response= send_post_request("{}/v2.0/subnets".format(neutron_ep), token, payload)
    logging.info("successfully created subnet") if response.ok else response.raise_for_status()
    data= response.json()
    return data['subnet']['id']
def search_and_create_subnet(neutron_ep, token, subnet_name, network_id, subnet_cidr):
    subnet_id= search_subnet(neutron_ep, token, subnet_name)    
    if subnet_id is None:
        subnet_id =create_subnet(neutron_ep, token, subnet_name, network_id, subnet_cidr) 
    logging.debug("subnet id is: {}".format(subnet_id)) 
    return subnet_id

'''
Flavor
'''

def search_flavor(nova_ep, token, flavor_name):
    # get list of flavors
    response= send_get_request("{}/v2.1/flavors".format(nova_ep), token)
    logging.info("successfully received flavor list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "flavors", "name", flavor_name, "id")

def create_flavor(nova_ep, token, flavor_name, flavor_ram, flavor_vcpus, flavor_disks):
    # create Flavor
    payload={
        "flavor": {
            "name": flavor_name,
            "ram":  flavor_ram,
            "vcpus": flavor_vcpus,
            "disk": flavor_disks,
            "rxtx_factor" : "1",
            "os-flavor-access:is_public": "true"
        }
    }
    response= send_post_request("{}/v2.1/flavors".format(nova_ep), token, payload)
    logging.info("successfully created flavor") if response.ok else response.raise_for_status()
    data= response.json()
    return data['flavor']['id']
def search_and_create_flavor(nova_ep, token, flavor_name, ram, vcpu, disks):
    flavor_id= search_flavor(nova_ep, token, flavor_name)    
    if flavor_id is None:
        flavor_id= create_flavor(nova_ep, token, flavor_name, ram, vcpu, disks)   
    logging.debug("flavor id is: {}".format(flavor_id))
    return flavor_id
def put_extra_specs_in_flavor(nova_ep, token, flavor_id,is_numa, mem_page_size="large"):
    #add extra specs to flavors
    if is_numa== True:
        payload= {
            "extra_specs": {
                "hw:cpu_policy": "dedicated", 
                "hw:cpu_thread_policy": "require",
                "hw:numa_nodes": "1", 
                "hw:mem_page_size": "large"
                }
        }
    else: 
        payload={
                "extra_specs": {
                    "hw:cpu_policy": "dedicated",
                    "hw:mem_page_size": mem_page_size,
                    "hw:cpu_thread_policy": "prefer",
                    "hw:numa_nodes": "1",
                    #"hw:emulator_threads_policy": "isolate"
                }  

        }
    response= send_post_request("{}/v2.1/flavors/{}/os-extra_specs".format(nova_ep, flavor_id), token, payload)
    print(response.text)
    logging.info("successfully added extra specs to  flavor {}".format(flavor_id)) if response.ok else response.raise_for_status()
def put_ovs_dpdk_specs_in_flavor(nova_ep, token, flavor_id):
    payload={
                "extra_specs": {
                    "hw:cpu_policy": "dedicated",
                    "hw:mem_page_size": "large",
                    "hw:cpu_thread_policy": "require",
                    "hw:numa_nodes": "1", 
                    "hw:numa_mempolicy":"preferred",
                    #"dpdk": "true"
                }
        }  
    response= send_post_request("{}/v2.1/flavors/{}/os-extra_specs".format(nova_ep, flavor_id), token, payload)
    logging.info("successfully added extra specs to  flavor {}".format(flavor_id)) if response.ok else response.raise_for_status()
'''
Router
'''
def search_router(neutron_ep, token, router_name):
    response= send_get_request("{}/v2.0/routers".format(neutron_ep), token)
    logging.info("successfully received router list") if response.ok else response.raise_for_status()

    return parse_json_to_search_resource(response, "routers", "name", router_name, "id")

def create_router(neutron_ep, token, router_name, network_id, subnet_id):
    payload={"router":
        {"name": router_name,
        "admin_state_up":" true",
        "external_gateway_info": {
            "network_id": network_id,
            "enable_snat": "true",
            "external_fixed_ips": [
                {
                    "subnet_id": subnet_id
                }
            ]
        }
        }

    }
    response= send_post_request('{}/v2.0/routers'.format(neutron_ep), token, payload)
    print(response.text)
    logging.info("successfully created router {}".format(router_name)) if response.ok else response.raise_for_status()  
    data= response.json()
    return data['router']['id']
def set_router_gateway(neutron_ep, token, router_id, network_id):
    print(router_id)
    payload={"router": {"external_gateway_info": {"network_id": network_id}}}
    response= send_post_request("{}/v2.0/routers/{}".format(neutron_ep,router_id), token, payload)
    print(response.text)
    logging.info("successfully set gateway to router {}".format(router_id)) if response.ok else response.raise_for_status()  
def add_interface_to_router(neutron_ep, token, router_id, subnet_id):
    payload={
    "subnet_id": subnet_id
    }
    
    response= send_put_request('{}/v2.0/routers/{}/add_router_interface'.format(neutron_ep,router_id), token, payload)
    print(response.text)
    logging.info("successfully added interface to router {}".format(router_id)) if response.ok else response.raise_for_status()  
def remove_interface_to_router(neutron_ep, token, router_id, subnet_id):
    payload={
    "subnet_id": subnet_id
    }
    
    response= send_put_request('{}/v2.0/routers/{}/remove_router_interface'.format(neutron_ep,router_id), token, payload)
    print(response.text)
    logging.info("successfully removed interface from router {}".format(router_id)) if response.ok else response.raise_for_status()  

def get_default_security_group_id(neutron_ep, token, project_id):
    response= send_get_request("{}/v2.0/security-groups".format(neutron_ep), token)
    logging.info("successfully received security group list") if response.ok else response.raise_for_status()
    data= response.json()
    for res in (data["security_groups"]):
        if(res["name"]== "default" and res["tenant_id"]== project_id):
            return res["id"]
            break
def search_security_group(neutron_ep, token, security_group_name):
    response= send_get_request("{}/v2.0/security-groups".format(neutron_ep), token)
    logging.info("successfully received security group list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "security_groups", "name", security_group_name, "id")

def create_security_group(neutron_ep, token, security_group_name):
    payload= {
    "security_group": {
        "name": security_group_name,
        }
    }
    response = send_post_request('{}/v2.0/security-groups'.format(neutron_ep), token, payload)
    logging.info("successfully created security Group {}".format(security_group_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["security_group"]["id"]

def search_and_create_security_group(neutron_ep, token, security_group_name):
    security_group_id= search_security_group(neutron_ep, token, security_group_name) 
    if security_group_id is None:
        security_group_id= create_security_group(neutron_ep, token, security_group_name)
    logging.debug("security group id is: {}".format(security_group_id)) 
    return security_group_id

def add_icmp_rule_to_security_group(neutron_ep, token, security_group_id):
    payload= {"security_group_rule":{
            "direction": "ingress",
            "ethertype":"IPv4",
            "direction": "ingress",
            "remote_ip_prefix": "0.0.0.0/0",
            "protocol": "icmp",
            "security_group_id": security_group_id
        }
    }
    response= send_post_request('{}/v2.0/security-group-rules'.format(neutron_ep), token, payload)
    logging.info("Successfully added ICMP rule to Security Group") if response.ok else response.raise_for_status()
def add_ssh_rule_to_security_group(neutron_ep, token, security_group_id):
    payload= {"security_group_rule": {
        "direction": "ingress",
        "ethertype":"IPv4",
        "direction": "ingress",
         "remote_ip_prefix": "0.0.0.0/0",
        "protocol": "tcp",
        "port_range_min": "22",
        "port_range_max": "22",
        "security_group_id": security_group_id
        }
        }
    response= send_post_request('{}/v2.0/security-group-rules'.format(neutron_ep), token, payload)
    logging.info("Successfully added SSH rule to Security Group") if response.ok else response.raise_for_status()

'''
Keypair
'''
def search_keypair(nova_ep, token, keypair_name):
    response= send_get_request("{}/v2.1/os-keypairs".format(nova_ep), token)
    logging.info("successfully received keypair list") if response.ok else response.raise_for_status()
    data= response.json()
    for res in (data["keypairs"]):
        if keypair_name in res["keypair"]["name"]:
            logging.warning("{} already exists".format(keypair_name))
            return res["keypair"]["public_key"]
            break      
    else:
        logging.info("{} does not exist".format(keypair_name))

def create_keypair(nova_ep, token, keypair_name):
    payload={
        "keypair":{
            "name": keypair_name,
            #"type": "ssh" 
            }
        }
    #nova_ep="http://192.168.140.252:8774/V2.2"
    response= send_post_request('{}/v2.1/os-keypairs'.format(nova_ep), token, payload)
    logging.info("successfully created keypair {}".format(keypair_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["keypair"]["private_key"]
def search_and_create_kaypair(nova_ep, token, key_name):
    keypair_public_key= search_keypair(nova_ep, token, key_name)
    if keypair_public_key is None:
        keypair_public_key= create_keypair(nova_ep, token, key_name)
    logging.debug("Keypair public key is: {}".format(keypair_public_key))
    return keypair_public_key

'''
Image
'''
def search_image(nova_ep, token, image_name):
    response= send_get_request("{}/v2.1/images".format(nova_ep), token)
    logging.info("successfully received images list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "images", "name", image_name, "id")

def create_image(nova_ep, token, image_name, container_format, disk_format, image_visibility):
    payload ={
        "container_format": container_format,
        "disk_format":disk_format,
        "name": image_name,
        "visibility":  image_visibility,
    }
    response = send_post_request("{}/v2.1/images".format(nova_ep), token, payload)
    logging.info("successfully created image {}".format(image_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["id"]
    
def get_image_status(nova_ep, token, image_id):
    response= send_get_request("{}/v2.1/images/{}".format(nova_ep, image_id), token)
    logging.info("successfully received image status") if response.ok else response.raise_for_status()
    data= response.json()
    return(data["status"])

def upload_file_to_image(image_ep, token, image_file, image_id):
    #image_file= open("cirros-0.5.1-x86_64-disk.img", "r")
    #response = send_put_request("{}/v2.1/images/{}/file".format(image_ep, image_id), token, image_file, "application/octet-stream")
    try:
        response= requests.put("{}/v2.1/images/{}/file".format(image_ep, image_id), headers= {'content-type':"application/octet-stream", 'X-Auth-Token': token}, data=image_file)
        print(response.text)
    except Exception as e:
        logging.error( "request processing failure ", stack_info=True)
        print(e)
    logging.info("successfully uploaded file to image") if response.ok else response.raise_for_status()
def search_and_create_image(image_ep, token, image_name, container_format, disk_format, image_visibility, image_file_path):
    image_id= search_image(image_ep, token, image_name)
    if image_id is None:
        image_id= create_image(image_ep, token, image_name, container_format, disk_format, image_visibility)    
    status= get_image_status(image_ep, token, image_id)
    print(status)
    if status== "queued":
        print("Successfully Queued")
        image_file= open(image_file_path, 'rb')
        logging.info("uploading image file")
        upload_file_to_image(image_ep, token, image_file, image_id)
        logging.debug("image id is: {}".format(image_id))
    return image_id


'''
Servers
'''
def receive_all_server(nova_ep, token):
    response= send_get_request("{}/v2.1/servers/detail".format(nova_ep), token)
    logging.info("successfully received server list") if response.ok else response.raise_for_status()
    return response.json()

def search_server(nova_ep, token, server_name):
    response= send_get_request("{}/v2.1/servers".format(nova_ep), token)
    logging.info("successfully received server list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "servers", "name", server_name, "id")

def create_server(nova_ep, token, server_name, image_id, keypair_name, flavor_id,  network_id, security_group_id, host=None, availability_zone= None):
    payload= {"server": {"name": server_name, "imageRef": image_id,
        "key_name": keypair_name, "flavorRef": flavor_id, 
        "max_count": 1, "min_count": 1, "networks": [{"uuid": network_id}], 
        "security_groups": [{"name": security_group_id}]}}   
    payload_manual_host={
        "host": host
        }
    #"networks": [{"uuid": network_id}]
    payload_availability_zone={
        "availability_zone": availability_zone
        }
    if host is not None:
        payload= {"server":{**payload["server"], **payload_manual_host}}
    if availability_zone is not None:
        payload= {"server":{**payload["server"], **payload_availability_zone}}
    response = send_post_request('{}/v2.1/servers'.format(nova_ep), token, payload)
    print(response.text)
    logging.info("successfully created server {}".format(server_name)) if response.ok else  response.raise_for_status()
    data= response.json()
    return data["server"]["links"][0]["href"]  
def create_sriov_server(nova_ep, token, server_name, image_id, keypair_name, flavor_id,  port_id, availability_zone ,security_group_id, host=None):
    print("Securit Group Id is: "+security_group_id)
    payload= {"server": {"name": server_name, "imageRef": image_id,
        "key_name": keypair_name, "flavorRef": flavor_id, "security_groups": [{"name": security_group_id}],
        "max_count": 1, "min_count": 1, "networks": [{"port": port_id}], 
         "availability_zone": availability_zone}}   
    payload_manual_host={
        "host": host
        }
    if host is not None:
        payload= {"server":{**payload["server"], **payload_manual_host}}
    response = send_post_request('{}/v2.1/servers'.format(nova_ep), token, payload)
    print(response.text)
    logging.info("successfully created sriov server {}".format(server_name)) if response.ok else  response.raise_for_status()
    data= response.json()
    return data["server"]["links"][0]["href"]  
def get_server_detail(token, server_url):
    response = send_get_request(server_url, token)
    logging.info("Successfully Received Server Details") if response.ok else response.raise_for_status()
    data= response.json()
    return data["server"]["id"]
def get_server_host(nova_ep, token, server_id):
    response = send_get_request("{}/v2.1/servers/{}".format(nova_ep, server_id) , token)
    logging.info("Successfully Received Server Details") if response.ok else response.raise_for_status()
    data= response.json()
    return data["server"]["OS-EXT-SRV-ATTR:host"]

def check_server_status(nova_ep, token, server_id):
    response = send_get_request("{}/v2.1/servers/{}".format(nova_ep, server_id), token)
    print(response.text)
    data= response.json()
    return data["server"]["OS-EXT-STS:vm_state"] if response.ok else response.raise_for_status()

def parse_server_ip(data, network, network_type):
    data=data.json()
    for networks in data["server"]["addresses"][str(network)]:
        if networks["OS-EXT-IPS:type"] == network_type:
            #logging.info("received {} ip address of server".format())
            return networks["addr"]

def get_server_ip(nova_ep, token, server_id, network):
    
    response = send_get_request('{}/v2.1/servers/{}'.format(nova_ep, server_id), token)
    print(response.text)
    logging.info("received server network detail") if response.ok else response.raise_for_status()
    return parse_server_ip(response, network, "fixed")

def get_server_floating_ip(nova_ep, token, server_id, network):
    response = send_get_request('{}/v2.1/servers/{}'.format(nova_ep, server_id), token)
    logging.info("received server network detail") if response.ok else response.raise_for_status()
    return parse_server_ip(response, network, "floating")

def get_server_instance_name(nova_ep, token, server_id):
    response = send_get_request("{}/v2.1/servers/{}".format(nova_ep, server_id) , token)
    logging.info("Successfully Received Server Details") if response.ok else response.raise_for_status()
    data= response.json()
    return data["server"]["OS-EXT-SRV-ATTR:instance_name"]
def perform_action_on_server(nova_ep,token, server_id, action):
    payload={
    action: None
    }
    response= send_post_request("{}/v2.1/servers/{}/action".format(nova_ep, server_id), token, payload)
    return response.status_code
def create_server_snapshot (nova_ep,token, server_id, snapshot_name):
    payload={
    "createImage" : {
        "name" : snapshot_name,
        "metadata": {}
        }
    }
    
    response= send_post_request("{}/v2.1/servers/{}/action".format(nova_ep, server_id), token, payload)
    print(response.text)
    if(response.status_code == 202):
        data= response.json()
        return data["image_id"]
    else:
        return None

def resize_server(nova_ep,token, server_id, flavor_id):
    payload= {
    "resize" : {
        "flavorRef" : flavor_id,
        "OS-DCF:diskConfig": "AUTO"
        }
    }
    response= send_post_request("{}/v2.1/servers/{}/action".format(nova_ep, server_id), token, payload)
    print(response.text)
    return response.status_code
def reboot_server(nova_ep,token, server_id):
    payload={
    "reboot" : {
        "type" : "HARD"
         }
    }
    response=send_post_request("{}/v2.1/servers/{}/action".format(nova_ep, server_id), token, payload)
    logging.info(response.text)
    return response.status_code

def live_migrate_server(nova_ep,token, server_id, host=None):
    payload= {
        "os-migrateLive": {
            "block_migration": "auto",
            "host": host
        }
        }

    response=send_post_request("{}/v2.1/servers/{}/action".format(nova_ep, server_id), token, payload)
    logging.info(response.text)
    return response.status_code

def search_and_create_server(nova_ep, token, server_name, image_id, key_name, flavor_id,  network_id, security_group_id, host=None, availability_zone= None):
    server_id= search_server(nova_ep, token, server_name)
    if server_id is None:
        time.sleep(10)
        server_url= create_server(nova_ep, token, server_name, image_id, key_name, flavor_id,  network_id, security_group_id, host, availability_zone)
        time.sleep(5)
        server_id= get_server_detail(token, server_url)
    logging.debug("Server id: "+server_id)    
    return server_id
def search_and_create_sriov_server(nova_ep, token, server_name, image_id, key_name, flavor_id,  port_id, availability_zone, security_group_id, host=None):
    server_id= search_server(nova_ep, token, server_name)
    if server_id is None:
        server_url= create_sriov_server(nova_ep, token, server_name, image_id, key_name, flavor_id, port_id, availability_zone, security_group_id, host)
        server_id= get_server_detail(token, server_url)
    logging.debug("Server id: "+server_id)  
    return server_id

'''
Floating Ip
'''
def parse_port_response(data, server_fixed_ip):
    data= data.json()
    for port in data["ports"]:
        if port["fixed_ips"][0]["ip_address"] == server_fixed_ip:
            return port["id"]   

def get_ports(neutron_ep, token, network_id, server_ip):
    response= send_get_request("{}/v2.0/ports?network_id={}".format(neutron_ep, network_id), token)
    logging.info("successfully received ports list ") if response.ok else response.raise_for_status()
    return parse_port_response(response, server_ip)

def create_floating_ip(neutron_ep, token, network_id, subnet_id, server_ip_address, server_port_id):
    payload= {"floatingip": 
             {"floating_network_id":network_id,
             
              "subnet_id": subnet_id,
              "fixed_ip_address": server_ip_address,
               "port_id": server_port_id
              }
             } 
    time.sleep(10)
    response= send_post_request("{}/v2.0/floatingips".format(neutron_ep), token, payload)
    print(response.text)
    logging.info("successfully assigned floating ip to server") if response.ok else response.raise_for_status()
    data= response.json()
    return data["floatingip"]["floating_ip_address"], data["floatingip"]["id"]
def create_floatingip_wo_port(neutron_ep, token, network_id ):
    payload= {
        "floatingip": {
            "floating_network_id": network_id
            }
        }
    response= send_post_request("{}//v2.0/floatingips".format(neutron_ep), token, payload)
    time.sleep(10)
    print(response.text)
    data=response.json()
    logging.info("successfully created floating ip") if response.ok else response.raise_for_status()
    return data["floatingip"]["floating_ip_address"], data["floatingip"]["id"]
def assign_ip_to_port(neutron_ep, token, port_id, floatingip_id ):
    payload= {
        "floatingip": {
            "port_id": port_id
            }
        }
    response= send_put_request("{}/v2.0/floatingips/{}".format(neutron_ep, floatingip_id), token, payload)
    print(response.text)
    time.sleep(10)
    logging.info("successfully assigned floating to port") if response.ok else response.raise_for_status()

def attach_volume_to_server( nova_ep, token, project_id, server_id, volume_id, mount_point):
    payload= {"volumeAttachment": {"volumeId": volume_id}}
    response= requests.post("{}/v2.1/servers/{}/os-volume_attachments".format(nova_ep, server_id), headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    print(response.text)
    logging.info("volume successfully attached to server") if response.ok else response.raise_for_status()

def search_volume(storage_ep, token, volume_name, project_id):
    response= send_get_request("{}/v3/{}/volumes".format(storage_ep, project_id), token)
    print(response.text)
    logging.info("successfully received volume list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "volumes", "name",volume_name, "id")

'''
Volume
'''
def create_volume(storage_ep, token, project_id, volume_name, volume_size, availability_zone=None):
    payload= {"volume":{
                "size": volume_size,
                "project_id":project_id,
                "name": volume_name
                }
            }
    response= requests.post("{}/v3/{}/volumes".format(storage_ep, project_id), headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    logging.debug(response.text)
    print(response.text)
    logging.info("successfully created volume {}".format(volume_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["volume"]["id"]
def upscale_voume(storage_ep, token, project_id, volume_id, volume_size):
    payload= {"os-extend": {"new_size": volume_size}}
    response= requests.post("{}/v3/{}/volumes/{}/action".format(storage_ep, project_id, volume_id), headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    print(response.text)
    if(response.status_code ==202):
        logging.debug(response.text)
        print(response.text)
        logging.info("successfully updated  volume") if response.ok else response.raise_for_status()
        return True
    else:
        return False
def migrate_voume(storage_ep, token, project_id, volume_id):
    payload={
    "os-migrate_volume": {
        "host":"r185-controller-2"
        }
    }
    #payload= {"os-extend": {"new_size": volume_size}}
    response= requests.post("{}/v3/{}/volumes/{}/action".format(storage_ep, project_id, volume_id), headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    print(response.text)
    if(response.status_code ==202):
        logging.debug(response.text)
        print(response.text)
        logging.info("successfully migrated  volume") if response.ok else response.raise_for_status()
        return True
    else:
        return False

def search_and_create_volume(storage_ep, token, project_id, volume_name, volume_size, availability_zone=None):
    volume_id= search_volume(storage_ep, token, volume_name, project_id)
    if volume_id is None:
        volume_id= create_volume(storage_ep, token, project_id, volume_name, volume_size, )
    logging.debug("Volume id: "+volume_id)    
    return volume_id
def check_volume_status(storage_ep, token, volume_id, project_id):
    response = send_get_request("{}/v3/{}/volumes/{}".format(storage_ep, project_id, volume_id), token)
    data= response.json()
    return data["volume"]["status"] if response.ok else response.raise_for_status()

def create_volume_snapshot(storage_ep, token, project_id, volume_id, snapshot_name):
    payload= {"snapshot": {"volume_id": volume_id, 
    "force": "false", 
    "name": snapshot_name }
            }
    response= requests.post("{}/v3/{}/snapshots".format(storage_ep, project_id), headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    logging.debug(response.text)
    print(response.text)
    if(response.status_code == 202):
        logging.info("successfully created snapshot {}".format(snapshot_name)) if response.ok else response.raise_for_status()
        data= response.json()
        return data["snapshot"]["id"]
    else:
        return None

def replicate_volume(storage_ep, token, project_id, volume_name, source_id):
    payload= {"volume":{
                "source_volid": source_id,
                "name": volume_name
                
                }
            }
    response= requests.post("{}/v3/{}/volumes".format(storage_ep, project_id), headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    logging.debug(response.text)
    print(response.text)
    if(response.status_code== 202):
        logging.info("successfully replicated volume {}".format(volume_name)) if response.ok else response.raise_for_status()
        data= response.json()
        return data["volume"]["id"]
    else: 
        return None

def create_volume_from_snapshot(storage_ep, token, project_id, volume_name, snapshot_id):

    payload= {"volume":{
                "snapshot_id": snapshot_id,
                "name": volume_name
                }
            }
    response= requests.post("{}/v3/{}/volumes".format(storage_ep, project_id), headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    logging.debug(response.text)
    print(response.text)
    if(response.status_code== 202):
        logging.info("successfully created volume {}".format(volume_name)) if response.ok else response.raise_for_status()
        data= response.json()
        return data["volume"]["id"]
    else: 
        return None

def find_admin_project_id(keystone_ep, token):
    response= send_get_request("{}/v3/projects".format(keystone_ep), token)
    logging.info("successfully received project details") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "projects", "name", "admin", "id")
 
def get_baremeta_nodes_ip(nova_ep, undercloud_token):
    servers= receive_all_server(nova_ep, undercloud_token)
    server_ip={}
    for server in servers["servers"]:
        server_ip[server["name"]]= server["addresses"]["ctlplane"][0]["addr"]
    return server_ip
def get_compute_host_list(nova_ep, token):
    response= send_get_request("{}/v2.1/os-hosts".format(nova_ep), token)
    logging.info("successfully received host list") if response.ok else response.raise_for_status()
    data= response.json()
    hosts=[]
    for host in data["hosts"]:
        hosts.append(host["host_name"])
    return hosts
def set_quota(nova_ep, token, project_id, vcpus, instances, ram):
    payload= {"quota_set": {
        "instances": instances,
        "cores": vcpus,
        "ram": ram
        }}
    #data=json.dumps(payload)
    response= requests.put("{}/v2.1/os-quota-sets/{}".format(nova_ep, project_id),  headers= {'content-type': "application/json", 'X-Auth-Token': token}, data=json.dumps(payload))
    #response= send_post_request("{}/v2.1/os-quota-sets/{}".format(nova_ep, project_id), token, payload)
    #print(response.text)
    logging.info("successfully updated quota") if response.ok else response.raise_for_status()
    
def get_availability_zones(nova_ep, token):
    response= send_get_request("{}/v2.1/os-aggregates".format(nova_ep), token)
    logging.info("successfully received availibility zones list") if response.ok else response.raise_for_status()
    data= response.json()   
    return data["aggregates"][0]["id"]
def create_availability_zones(nova_ep, token, name):
    payload= {
    "aggregate":
        {
        "name": name,
        "availability_zone": name
        }
    }
    response= send_post_request("{}/v2.1/os-aggregates".format(nova_ep), token, payload)
    logging.info("successfully created availibility zone") if response.ok else response.raise_for_status()
    data= response.json()   
    return data["aggregate"]["id"]

def remove_host_from_zone(nova_ep, token, zone_id, host_name):
    payload= {
    "remove_host": {
        "host": host_name
        }
    }
    response= send_post_request("{}/v2.1/os-aggregates/{}/action".format(nova_ep,zone_id), token, payload)
    logging.info("successfully removed host from availability zones ") if response.ok else response.raise_for_status()
def add_host_to_zone(nova_ep, token, zone_id, host_name):
    payload= {
    "add_host": {
        "host": host_name
        }
    }
    response= send_post_request("{}/v2.1/os-aggregates/{}/action".format(nova_ep,zone_id), token, payload)
    logging.info("successfully added host to availability zones ") if response.ok else response.raise_for_status()
def add_property_availability_zones(nova_ep, token, zone_id):
    payload= {"set_metadata": {"metadata": {"dpdk": "true"}}}
    response= send_post_request("{}/v2.1/os-aggregates/{}/action".format(nova_ep, zone_id), token, payload)
    logging.info("successfully added property availability zone") if response.ok else response.raise_for_status()

#Load Balancer
def create_loadbalancer(loadbal_ep, token, loadbalancer_name, subnet_id):
    #create loadbalancer
    payload= {
        "loadbalancer": {
            "name": loadbalancer_name,
            "vip_subnet_id": subnet_id,
            "admin_state_up": "true"
            }
        }

    response= send_post_request('{}/v2.0/lbaas/loadbalancers'.format(loadbal_ep), token, payload)
    print(response.text)
    logging.info("successfully created loadbalancer {}".format(loadbalancer_name)) if response.ok else response.raise_for_status()
    data=response.json()
    return data['loadbalancer']['id']
def search_loadbalancer(loadbal_ep, token, loadbalancer_name):
    #get list of loadbalancer
    response= send_get_request("{}/v2.0/lbaas/loadbalancers".format(loadbal_ep), token)
    logging.info("successfully received loadbalancer list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "loadbalancers", "name", loadbalancer_name, "id")

def check_loadbalancer_status(loadbal_ep, token, loadbalancer_id):
    response = send_get_request("{}/v2.0/lbaas/loadbalancers/{}".format(loadbal_ep, loadbalancer_id), token)
    print(response.text)
    data= response.json()
    return data["loadbalancer"]["provisioning_status"] if response.ok else response.raise_for_status()
def check_loadbalancer_vipport(loadbal_ep, token, loadbalancer_id):
    response = send_get_request("{}/v2.0/lbaas/loadbalancers/{}".format(loadbal_ep, loadbalancer_id), token)
    print(response.text)
    data= response.json()
    return data["loadbalancer"]["vip_port_id"] if response.ok else response.raise_for_status()

def search_and_create_loadbalancer(loadbal_ep, token, loadbalancer_name, subnet_id):
    loadbalancer_id= search_loadbalancer(loadbal_ep, token, loadbalancer_name)    
    if loadbalancer_id is None:
        loadbalancer_id =create_loadbalancer(loadbal_ep, token, loadbalancer_name, subnet_id )  
    logging.debug("loadbalancer id is: {}".format(loadbalancer_id))
    return loadbalancer_id
#Listener
def create_listener(loadbal_ep, token, listener_name, loadbalancerid, protocol, protocol_port):
    #create loadbalancer
    payload= {
        "listener": {
            "name": listener_name,
            "loadbalancer_id": loadbalancerid,
            "protocol": protocol, 
            "protocol_port": protocol_port,
            "admin_state_up": "true"
            }
        }
    try:
        response= send_post_request('{}/v2.0/lbaas/listeners'.format(loadbal_ep), token, payload)
        print(response.text)
        logging.info("successfully created loadbalancer {}".format(listener_name)) if response.ok else response.raise_for_status()
        data=response.json()
        return data['listener']['id']
    except:
        return "failed"
def search_listener(loadbal_ep, token, listener_name):
    #get list of loadbalancer
    response= send_get_request("{}/v2.0/lbaas/listeners".format(loadbal_ep), token)
    logging.info("successfully received listener list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "listeners", "name", listener_name, "id")

def check_listener_status(loadbal_ep, token, listener_id):
    response = send_get_request("{}/v2.0/lbaas/listeners/{}".format(loadbal_ep, listener_id), token)
    data= response.json()
    return data["listener"]["provisioning_status"] if response.ok else response.raise_for_status()
def search_and_create_listener(loadbal_ep, token, listener_name, loadbalancer_id, protocol, protocol_port):
    listener_id= search_listener(loadbal_ep, token, listener_name)    
    if listener_id is None:
        listener_id =create_listener(loadbal_ep, token, listener_name, loadbalancer_id, protocol, protocol_port)  
    logging.debug("listener id is: {}".format(listener_id))
    return listener_id
#Pool
def create_pool(loadbal_ep, token, pool_name, listenerid, loadbalancerid, protocol, algorithm, session=None):
    #create loadbalancer
    payload= {
        "pool": {
            "name": pool_name,
            "protocol": protocol, 
            "listener_id":listenerid,
            "lb_algorithm": algorithm,
            "protocol": protocol,
            "admin_state_up": "true"
            }
        }
    payload_session= {"session_persistence": 
        {"type": "APP_COOKIE", 
        "cookie_name": "PHPSESSIONID"}
        }
    if session is not None:
        payload= {"pool":{**payload["pool"], **payload_session}}
    try:
        response= send_post_request('{}/v2.0/lbaas/pools'.format(loadbal_ep), token, payload)
        print(response.text)
        logging.info("successfully created loadbalancer {}".format(pool_name)) if response.ok else response.raise_for_status()
        data=response.json()
        return data['pool']['id']
    except:
        return "failed"
def search_pool(loadbal_ep, token, listener_name):
    #get list of loadbalancer
    response= send_get_request("{}/v2.0/lbaas/pools".format(loadbal_ep), token)
    logging.info("successfully received listener list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "pools", "name", listener_name, "id")

def check_pool_status(loadbal_ep, token, listener_id):
    response = send_get_request("{}/v2.0/lbaas/pools/{}".format(loadbal_ep, listener_id), token)
    print(response.text)
    data= response.json()
    return data["pool"]["provisioning_status"] if response.ok else response.raise_for_status()
def search_and_create_pool(loadbal_ep, token, pool_name, listener_id, loadbalancerid, protocol, algorithm):
    pool_id= search_pool(loadbal_ep, token, pool_name)    
    if pool_id is None:
        pool_id =create_pool(loadbal_ep, token,  pool_name, listener_id, loadbalancerid, protocol, algorithm)  
    logging.debug("listener id is: {}".format(listener_id))
    return pool_id
def add_instance_to_pool(loadbal_ep, token, pool_id, ip, subnet_id, protocol_port ):
    payload= {
        "member": {
            "address": ip,
            "subnet_id": subnet_id,
            "protocol_port": protocol_port,
            }
        }
    response= send_post_request("{}/v2.0/lbaas/pools/{}/members".format(loadbal_ep, pool_id), token, payload)
    logging.info("successfully added instance to pool") if response.ok else response.raise_for_status()

def health_monitor_pool(loadbal_ep, token, pool_id, type):
    payload= {
        "healthmonitor": {
            "pool_id": pool_id,
             "delay": 5, 
             "timeout": 10, 
             "max_retries": 4, 
             "type": type, 
             "admin_state_up": "true",
             #"url_path": "/healthcheck"
            }
        }
    try:
        response= send_post_request("{}/v2.0/lbaas/healthmonitors".format(loadbal_ep), token, payload)
        logging.info("successfully added health monitor to pool") if response.ok else response.raise_for_status()
    except:
        return "failed"
def create_loadbalancer_floatingip(neutron_ep, token, network_id ):
    payload= {
        "floatingip": {
            "floating_network_id": network_id
            }
        }
    response= send_post_request("{}//v2.0/floatingips".format(neutron_ep), token, payload)
    print(response.text)
    data=response.json()
    logging.info("successfully created floating ip for load balancer") if response.ok else response.raise_for_status()
    return data["floatingip"]["id"], data["floatingip"]["floating_ip_address"]
def assign_lb_floatingip(neutron_ep, token, port_id, floatingip_id ):
    payload= {
        "floatingip": {
            "port_id": port_id
            }
        }
    response= send_put_request("{}/v2.0/floatingips/{}".format(neutron_ep, floatingip_id), token, payload)
    print(response.text)
    logging.info("successfully assigned floating ip to vip port") if response.ok else response.raise_for_status()
def get_pool_member(loadbal_ep, token, pool_id):
    response = send_get_request("{}/v2.0/lbaas/pools/{}".format(loadbal_ep, pool_id), token)
    print(response.text)
    data= response.json()
    logging.info("successfully assigned member of pool") if response.ok else response.raise_for_status()
    return data["pool"]["members"][0]["id"] 
def down_pool_member(loadbal_ep, token, pool_id, member_id ):
    payload= {
        "member": {
           "admin_state_up": 'false'
            }
        }
    response= send_put_request("{}/v2.0/lbaas/pools/{}/members/{}".format(loadbal_ep, pool_id, member_id), token, payload)
    time.sleep(5)
    print(response.text)
    logging.info("successfully down a member in pool") if response.ok else response.raise_for_status()
def up_pool_member(loadbal_ep, token, pool_id, member_id ):
    time.sleep(5)
    payload= {
        "member": {
           "admin_state_up": 'true'
            }
        }
    response= send_put_request("{}/v2.0/lbaas/pools/{}/members/{}".format(loadbal_ep, pool_id, member_id), token, payload)
    print(response.text)
    time.sleep(5)
    logging.info("successfully up a member in pool") if response.ok else response.raise_for_status()
def disable_loadbalancer(loadbal_ep, token, loadbalancer_id ):
    payload= {
        "loadbalancer": {
           "admin_state_up": 'false'
            }
        }
    response= send_put_request("{}/v2.0/loadbalancers/{}".format(loadbal_ep, loadbalancer_id), token, payload)
    time.sleep(30)
    print(response.text)
    logging.info("successfully disabled loadbalancer") if response.ok else response.raise_for_status()
def enable_loadbalancer(loadbal_ep, token, loadbalancer_id ):
    payload= {
        "loadbalancer": {
           "admin_state_up": 'true'
            }
        }
    response= send_put_request("{}/v2.0/loadbalancers/{}".format(loadbal_ep, loadbalancer_id), token, payload)
    time.sleep(30)
    print(response.text)
    logging.info("successfully disabled loadbalancer") if response.ok else response.raise_for_status()
def check_loadbalancer_operating_status(loadbal_ep, token, loadbalancer_id):
    response = send_get_request("{}/v2.0/lbaas/loadbalancers/{}".format(loadbal_ep, loadbalancer_id), token)
    print(response.text)
    data= response.json()
    return data["loadbalancer"]["operating_status"] if response.ok else response.raise_for_status()

def create_l7policy(loadbal_ep, token, policy_name, listener_id):
    #create loadbalancer
    payload= {
        "l7policy": {
            "name": policy_name,
            "listener_id": listener_id,
            "action": "REDIRECT_TO_URL", 
            "redirect_url": "https://www.example.com/",
            "admin_state_up": "true"
            }
        }
    response= send_post_request('{}/v2.0/lbaas/l7policies'.format(loadbal_ep), token, payload)
    print(response.text)
    logging.info("successfully created l7policy {}".format(policy_name)) if response.ok else response.raise_for_status()

def create_l7policy(loadbal_cdep, token, policy_id):
    #create loadbalancer
    payload= {
        "rule": {
            "compare_type": "STARTS_WITH", 
            "value": "/", 
            "type": "PATH",
            "admin_state_up": "true"
            }
        }
    response= send_post_request('{}/v2.0/lbaas/l7policies/{}/rules'.format(loadbal_ep, policy_id), token, payload)
    print(response.text)
    logging.info("successfully added rule to policy {}".format(policy_id)) if response.ok else response.raise_for_status()
#BArbican
def add_key_to_store(barbican_ep, token, key):
    payload= {"name": "signing-cert", "algorithm": "RSA", "mode": "cbc", "bit_length": 256,
                "secret_type": "certificate", 
                "payload": key,
                "payload_content_type": "application/octet-stream", 
                "payload_content_encoding": "base64"}

    response= send_post_request("{}/v1/secrets/".format(barbican_ep), token, payload)
    key_id= str(response.text)
    key_id= key_id.split("/")
    key_id= key_id[-1]
    key_id= key_id.strip('"}')
    
    print("Key is: "+key_id)
    logging.info("successfully add key to barbican") if response.ok else response.raise_for_status()
    return key_id
def add_symmetric_key_to_store(barbican_ep, token):
    payload= {"type": "key", "meta": {"name": "swift_key", "algorithm": "aes", "bit_length": 256, "payload_content_type": "application/octet-stream", "mode": "ctr"}}


    response= send_post_request("{}/v1/orders/".format(barbican_ep), token, payload)
    key_id= str(response.text)
    key_id= key_id.split("/")
    key_id= key_id[-1]
    key_id= key_id.strip('"}')
    
    print("Key is: "+key_id)
    logging.info("successfully add key to barbican") if response.ok else response.raise_for_status()
    return key_id


def create_barbican_image(nova_ep, token, image_name, container_format, disk_format, image_visibility, image_signature, key_id):
    payload ={
        "container_format": container_format,
        "disk_format":disk_format,
        "name": image_name,
        "visibility":  image_visibility,
        "img_signature": image_signature,
        "img_signature_certificate_uuid": key_id,
        "img_signature_hash_method":"SHA-256",
        "img_signature_key_type": "RSA-PSS"
    }
    response = send_post_request("{}/v2.1/images".format(nova_ep), token, payload)
    logging.info("successfully created image {}".format(image_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["id"]



def create_secret(barbican_ep, token, name, payload):
    key_id=""
    payload= {"name": name, "algorithm": "aes", "mode": "cbc", "bit_length": 256, "secret_type": "opaque" ,
                "payload": payload, 
                "payload_content_type": "text/plain"}

    response= send_post_request("{}/v1/secrets/".format(barbican_ep), token, payload)
    print(response.text)
    print(response.status_code)
    if (response.status_code==201):
        key_id= str(response.text)
        key_id= key_id.split("/")
        key_id= key_id[-1]
        key_id= key_id.strip('"}')
        logging.info("successfully add secret to barbican") if response.ok else response.raise_for_status()
    else:
        logging.info("failed to create secret")
    return key_id
def update_secret(barbican_ep, token, url, data):
    payload= {"data"}
    #payload= bytes("data", 'utf-8')
    #payload= {payload}
    #print(payload)
    response=""
    #payload= {"payload_content_type": "text/plain"}
    try:
       response= requests.put("{}/v1/secrets/".format(barbican_ep), headers= {"Accept":"text/plain", 'X-Auth-Token': token}, data=json.dumps(payload))
    except Exception as e:
        logging.error( "request processing failure ", stack_info=True)
        logging.exception(e)
    #response= send_put_request("{}/v1/secrets/".format(barbican_ep), token, payload)
    print(response)
    if (response.status_code==201):
        logging.info("successfully updated secret to barbican") if response.ok else response.raise_for_status()
        return True
    else:
        logging.info("failed to update secret")
        return False
def get_secret(barbican_ep, token, secret_id):
    response= send_get_request("{}/v1/secrets/{}".format(barbican_ep,secret_id), token)
    print(response.text)
    if response.status_code==200:
        return response.text
    else:
        return None 
def get_key(barbican_ep, token, secret_id):
    response= send_get_request("{}/v1/orders/{}".format(barbican_ep,secret_id), token)
    print(response.text)
    if response.status_code==200:
        return response.text
    else:
        return None 
def get_payload(barbican_ep, token, secret_id):
    response= send_get_request("{}/v1/secrets/{}/payload".format(barbican_ep,secret_id), token)
    print(response.text)
    return response.text

#
#Server Functions
#

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
            return True
        logging.info("Waiting for server to boot")
        time.sleep(30)
        retries=retries+1
        if(retries==5):
            return False
def wait_instance_ssh(ip, settings):
    try:
        remove_key= "ssh-keygen -R {}".format(server1)
        os.system(remove_key)
    except:
        pass
    retries=0
    ssh=False
    while(1):
        try:
            client= paramiko.SSHClient()
            paramiko.AutoAddPolicy()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
            ssh= True
            break
        except Exception as e:
            print(e)
        
            logging.info("Waiting for server to ssh")
            time.sleep(30)
        retries=retries+1
        if(retries==4):
            break
    return ssh
def instance_ssh(server1, settings, command):
    try:
        remove_key= "ssh-keygen -R {}".format(server1)
        os.system(remove_key)
    except:
        pass
    try:
        client= paramiko.SSHClient()
        paramiko.AutoAddPolicy()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server1, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
        logging.info("SSH Session is established")
        logging.info("Running command in a compute node")
        stdin, stdout, stderr = client.exec_command(command)
        logging.info("command {} successfully executed on instance")
        output= stdout.read().decode('ascii')
        error= stderr.read().decode('ascii')
        return output, error
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        client.close()
        logging.info("Connection from client has been closed")  
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
        logging.info("command {} successfully executed on node {}".format(command, host_ip))
        output= stdout.read().decode('ascii')
        error= stderr.read().decode('ascii')
        return output, error
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        ssh_client.close()
        logging.info("Connection from client has been closed") 
    