import requests
import json
import os
import logging
def create_network(network_id,mtu_size,subnet_name,cidr,token):
    ##### Creating Network ########
    payload= {
        "network": {
            "name": network_id,
            "admin_state_up": True,
            "mtu": mtu_size,
            "provider:network_type": "vlan"
            }
        }

    #List Networks
    res = requests.get('http://100.82.39.60:9696/v2.0/networks',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    #print(res.text)

    #res= json.loads(res.text)
    #print(json.dumps(res, indent=1))
    data= res.json()
    flag=0
    for sd in (data["networks"]):
        if network_id in (sd["name"]):
            net_id=sd["id"]
            #print(net_id)
            print("        Network"+ (sd["name"]) +" already exists")
            flag= flag + 1

    if flag == 0:
         #creating network through api
        res = requests.post('http://100.82.39.60:9696/v2.0/networks',
                            headers={'content-type': 'application/json',
                                'X-Auth-Token': token},
                            data=json.dumps(payload))
        print((network_id) +" Successfully created")
        if res.ok:
            print("Successfully Created Network "+network_name)
        else :
            res.raise_for_status()

    ### Creating subnet ####
    payload= {
        "subnet": {
            "name": subnet_name,
            "network_id": net_id,
            "ip_version": 4,
            "cidr": cidr
            }
        }

    #List Subnets
    res = requests.get('http://100.82.39.60:9696/v2.0/subnets',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})

    data= res.json()
    flag=0
    for sd in (data["subnets"]):
        if subnet_name in (sd["name"]):
            print("        Subnet"+ (sd["name"]) +" already exists")
            flag= flag + 1

    if flag == 0:
         #creating Subnet through api
        res = requests.post('http://100.82.39.60:9696/v2.0/subnets',
                            headers={'content-type': 'application/json',
                                'X-Auth-Token': token},
                            data=json.dumps(payload))
        print("            " (subnet_name) +" Successfully created")
        if res.ok:
            print("Successfully Created Subnet  "+ (subnet_name))
        else :
            res.raise_for_status()



def image_verify(image,token):
    # Get Images
    res = requests.get('http://100.82.39.60:9292/v2/images',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})

    # List Images
    data= res.json()
    flag=0
    for sd in (data["images"]):
        if image in (sd["name"]):
            print("        image",(sd["name"]) +" already exists")



def flavor_verify(flavor,token):
    # Get Images
    res = requests.get('http://100.82.39.60:8774/v2/flavors',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})

    # List Images
    print(res.text)
    data= res.json()
    flag=0
    for sd in (data["flavors"]):
        if flavor in (sd["name"]):
            print("        flavor",(sd["name"]) +" already exists")



def create_keypair(key_name,fingerprint,key_type,public_key,user_id,token):
    payload= {
        "keypair": {
            "fingerprint": fingerprint,
            "name": key_name,
        #    "type": key_type,
        #    "public_key": public_key,
        #    "user_id": user_id
            }
        }

    res = requests.post('http://100.82.39.60:8774/v2.0/os-keypairs',
                            headers={'content-type': 'application/json',
                                'X-Auth-Token': token},
                            data=json.dumps(payload))

    print((key_name) +" Successfully created")
    if res.ok:
        print("Successfully Created Network "+key_name)
    else :
        res.raise_for_status()

    ####  Volume creation
def create_volume(vol_name,Vol_size,project_id,token):
    payload= {
        "volume": {
            "name": vol_name,
            "size": Vol_size
            }
        }
    url= "http://100.82.39.60:8776/v3/"+ project_id +"/volumes"
    res = requests.get(url,
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    #print(res.text)

    data= res.json()
    flag=0
    for sd in (data["volumes"]):
        if vol_name in (sd["name"]):
            print("        volume",(sd["name"]) +" already exists")
            flag=flag+1

    if flag == 0:
        res = requests.post(url,
                                headers={'content-type': 'application/json',
                                    'X-Auth-Token': token},
                                data=json.dumps(payload))

    print((vol_name) +" Successfully created")
    if res.ok:
        print("Successfully Created Network "+vol_name)
    else :
        res.raise_for_status()


def attach_volume(instance_name,vol_name,project_id,token):
    mountpoint= "/dev/vdb"

    res = requests.get('http://100.82.39.60:8774/v2.1/servers',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    #print(res.text)
    data=res.json()
    for sd in (data["servers"]):
        if instance_name in (sd["name"]):
            inst_id =sd["id"]


    url= "http://100.82.39.60:8776/v3/"+ project_id +"/volumes"
    res = requests.get(url,
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})



    data= res.json()
    for sd in (data["volumes"]):
        if vol_name in (sd["name"]):
            vol_id=sd["id"]

            payload= {"volumeAttachment": {"volumeId": vol_id}}
        #    POST http://100.82.39.60:8774/v2.1/servers/b6562df0-859e-4e31-8ce3-2f743a46c8d9/os-volume_attachments
            url= "http://100.82.39.60:8774/v2.1/servers/"+ inst_id +"/os-volume_attachments"

            res = requests.post(url,
                            headers={'content-type': 'application/json',
                                    'X-Auth-Token': token},
                                     data=json.dumps(payload))
            if res.ok:
                print("Successfully attach "+ (vol_name) +"Volume with instance"+ (instance_name))

            else :
                res.raise_for_status()


def find_admin_project_id(token):
    res = requests.get('http://100.82.39.60:5000/v3/projects',
                headers={'content-type': 'application/json',
                    'X-Auth-Token': token})
    #print(res.text)
    data= res.json()
    flag=0
    for sd in (data["projects"]):
        if "admin" in (sd["name"]):
            return (sd["id"])

def delete_volume(vol_name,project_id,token):
    payload= {
        "volume": {
            "name": vol_name
            }
        }
    url= "http://100.82.39.60:8776/v3/"+ project_id +"/volumes"
    res = requests.get(url,
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})

    data= res.json()
    flag=0
    for sd in (data["volumes"]):
        if vol_name in (sd["name"]):
            vol_id=sd["id"]
            url= "http://100.82.39.60:8776/v3/"+ project_id +"/volumes/"+ vol_id
            res = requests.delete(url,
                            headers={'content-type': 'application/json',
                                    'X-Auth-Token': token})
            if res.ok:
                print("Successfully Delete Volume "+vol_name)
            else:
                res.raise_for_status()

def create_security_group(security_group_name,token):
    payload= {
    "security_group": {
        "name": security_group_name,
        "description": "description"
    }
    }

    res = requests.post('http://192.168.24.132:9696/v2.0/security-groups',
                  headers={'content-type': 'application/json',
                            'X-Auth-Token':  token   },
                data= json.dumps(payload)
                   )

    if res.ok:
        print("Successfully Created Security Group "+security_group_name)
    else :
        res.raise_for_status()

    data= res.json()
    return data["security_group"]["id"]


#Add SSH Rule
def add_icmp_rule(security_group_id,token):

    payload= {"security_group_rule":{
            "direction": "ingress",
            "ethertype":"IPv4",
            "direction": "ingress",
            "remote_ip_prefix": "0.0.0.0/0",
            "protocol": "icmp",
            "security_group_id": security_group_id
        }
    }

    res = requests.post('http://192.168.24.132:9696/v2.0/security-group-rules',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                data= json.dumps(payload)
                )
    if res.ok:
        print("Successfully added ICMP rule to Security Group ")
    else :
        res.raise_for_status()

def add_ssh_rule(security_group_id,token):

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


    res = requests.post('http://192.168.24.132:9696/v2.0/security-group-rules',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                data= json.dumps(payload)
                )
    if res.ok:
        print("Successfully added SSH rule to Security Group ")
    else :
        res.raise_for_status()

# Create Flavor
def create_flavor():
    payload={
        "flavor": {
            "name": flavor_name,
            "ram":  flavor_ram,
            "vcpus": flavor_vcpu,
            "disk": flavor_disk,
            "rxtx_factor" : flavor_rxtx_factor,
            "os-flavor-access:is_public": "true"
        }
    }

    res = requests.post(nova_ep+'/flavors',
                    headers={'content-type': 'application/json',
                             'User-Agent': 'python-novaclient',
                             'X-Auth-Token':  token   },
                    data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Flavor "+ flavor_name)
    else :
        res.raise_for_status()
    data= res.json()
    return data['flavor']['id']

def flavor_for_numaandhuge(flavor_name,token,vcpu):
    payload={
        "flavor": {
            "name": flavor_name,
            "ram":  "4096",
            "vcpus": vcpu,
            "disk": "40",
            "rxtx_factor" : "2.0",
            "os-flavor-access:is_public": "true",
            "extra_specs": {
                "hw:numa_nodes": "1",
                "hw:cpu_policy": "dedicated",
                "hw:cpu_thread_policy": "require",
                "hw:mem_page_size": "large",
                "quota:cpu_quota": "10000",
                "quota:cpu_period": "20000",
                "hw:cpu_policy": "dedicated",
                "hw:cpu_thread_policy": "require",
                "hw:numa_nodes": "1"
            }
        }
    }

    res = requests.post(nova_ep+'/flavors',
                headers={'content-type': 'application/json',
                         'User-Agent': 'python-novaclient',
                         'X-Auth-Token':  token   },
                data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Flavor "+ flavor_name)
    else :
        res.raise_for_status()
    data= res.json()


#Keypair
def create_keypair(keypair_name,token):

    payload={"keypair":
        {"type": "ssh",
        "name": keypair_name
        }
        }

    res = requests.post(nova_ep+'/os-keypairs',
                  headers={'Accept': 'application/json' ,  'User-Agent': 'python-novaclient' ,
                           'OpenStack-API-Version': 'compute 2.60' , 'X-OpenStack-Nova-API-Version': '2.60' ,
                           'X-Auth-Token': token , 'Content-Type': 'application/json'},
                  data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Keypair")
    else :
        res.raise_for_status()
    data= res.json()
    return data["keypair"]["public_key"]

def create_server(server_name, image, keypair_name, flavor,  network, security_group,token):
    payload= {"server": {"name": server_name, "imageRef": image,
 "key_name": keypair_name, "flavorRef": flavor_id,
 "max_count": 1, "min_count": 1, "networks": [{"uuid": network}],
 "security_groups": [{"name": security_group}]}}
    res = requests.post(nova_ep+ '/servers',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))

    if res.ok:
        print("Successfully Created Server "+ server_name)
    else :
        res.raise_for_status()

    data= res.json()
    server_url= data["server"]["links"][0]["href"]
    res = requests.get(server_url,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if res.ok:
        print("Successfully Received Server Details")
    else :
        res.raise_for_status()
    data= res.json()
    return data["server"]["id"]

def check_server_status(server,token):
    res = requests.get(nova_ep+ '/servers/'+server,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if not res.ok:
        res.raise_for_status()
    data= res.json()
    return data["server"]["OS-EXT-STS:vm_state"]

def get_server_ip(server, network,token):
    res = requests.get(nova_ep+ '/servers/'+server,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if not res.ok:
        res.raise_for_status()
    data= res.json()
    for networks in data["server"]["addresses"][str(network)]:
        if networks["OS-EXT-IPS:type"] == "fixed":
            return networks["addr"]
def get_server_floating_ip(server, network,token):
    ip=""
    res = requests.get(nova_ep+ '/servers/'+server,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if not res.ok:
        res.raise_for_status()
    data= res.json()
    for networks in data["server"]["addresses"][str(network)]:
        if networks["OS-EXT-IPS:type"] == "floating":
            ip= networks["addr"]
    return ip

def get_ports(network_id, server_ip):
    res = requests.get(neutron_ep+ '/v2.0/ports?network_id='+network_id,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   }
                  )
    if res.ok:
        print("Successfully Received Ports List ")
    else :
        res.raise_for_status()
    data= res.json()
    for port in data["ports"]:
        if port["fixed_ips"][0]["ip_address"] == server_ip:
            return port["id"]

def create_floating_ip(network_id, subnet_id, server_ip_address, server_port_id,token):
    payload= {"floatingip":
             {"floating_network_id": network_id,
              "subnet_id": subnet_id,
              "fixed_ip_address": server_ip_address,
               "port_id": server_port_id
              }
             }
    res = requests.post(neutron_ep+'/v2.0/floatingips',
                    headers={'content-type': 'application/json',
                             'User-Agent': 'python-novaclient',
                             'X-Auth-Token':  token   },
                    data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Floating IP ")
    else :
        res.raise_for_status()
    data= res.json()
    return data["floatingip"]["floating_ip_address"]

##############################################################################################3
def create_external_network(network_name):
    payload={"network":
        {"name": network_name,
        "admin_state_up":" true",
        "router:external": "true",
        "provider:network_type": "flat",
        "provider:physical_network": "datacentre",
        }
        }


    res = requests.post(neutron_ep+'/v2.0/networks',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))

    if res.ok:
        print("Successfully Created External Network "+network_name)
    else :
        res.raise_for_status()

    data= res.json()
    return data['network']['id']

def create_external_subnet(subnet_name, network_id, cidr, gateway, pool_start, pool_end):
    payload= {"subnet":
              {"network_id": network_id,
              "ip_version": 4,
              "cidr": cidr,
               "name": subnet_name,
               "enable_dhcp": "true",
               "gateway_ip": gateway,
               "allocation_pools": [{"start": pool_start, "end": pool_end}]
              }
              }


    res = requests.post(neutron_ep +  '/v2.0/subnets',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if res.ok:
        print("Successfully Created External Subnet "+subnet_name)
    else :
        res.raise_for_status()


# Create Router

def create_router(router_name):
    payload={"router":
        {"name": router_name,
        "admin_state_up":" true",
        }
        }


    res = requests.post(neutron_ep+'/v2.0/routers',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))

    if res.ok:
        print("Successfully Created Router "+router_name)
    else :
        res.raise_for_status()

    data= res.json()
    return data['router']['id']

def add_router_interface(router_id, subnet_id, subnet_name):
    payload={"subnet_id": subnet_id,
        }

    res = requests.put(neutron_ep +  '/v2.0/routers/'+router_id+"/add_router_interface",
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if res.ok:
        print("Successfully Added Subnet "+subnet_name+" to Router")
    else:
        res.raise_for_status()

def set_router_gateway(router_id, network_id, router_name):
    payload={"router": {"external_gateway_info": {"network_id": network_id}}}

    res = requests.put(neutron_ep +  '/v2.0/routers/'+router_id,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if res.ok:
        print("Successfully Added GAteway to Router "+router_name)
    else:
        res.raise_for_status()
