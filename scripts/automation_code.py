import requests
import json
import os

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