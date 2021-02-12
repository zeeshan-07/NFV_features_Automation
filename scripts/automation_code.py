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
            print("        Network",(sd["name"]) +" already exists")
            flag= flag + 1
        
    if flag == 0:
         #creating network through api
        res = requests.post('http://100.82.39.60:9696/v2.0/networks',
                            headers={'content-type': 'application/json',
                                'X-Auth-Token': token},
                            data=json.dumps(payload))
        print("            " (network_id) +" Successfully created")
        if res.ok:
            print("Successfully Created Network "+network_name)
        else :
            res.raise_for_status()
    
    ### Creating subnet ####
    print("Network Id: ")
    print(network_id)
    payload= {
        "subnet": {
            "name": subnet_name,
            "network_id": "8a220741-cfc4-4718-888c-461ae5461e3d", 
            "ip_version": 4, 
            "cidr": cidr 
            }
        }

    res = requests.post('http://100.82.39.60:9696/v2.0/subnets',
                        headers={'content-type': 'application/json',
                             'X-Auth-Token':  token},
                        data=json.dumps(payload))

    if res.ok:
        print("Successfully Created Subnet "+subnet_name)
    else :
        res.raise_for_status()

    data= res.json()



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
        "type": key_type,
        "public_key": public_key,
        "user_id": user_id
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

################# Main function ##############
def main():
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
 
#    create_keypair(data_info["key_name"],data_info["fingerprint"],data_info["key_type"],data_info["public_key"],data_info["key_user_id"],token)
#    flavor_verify(data_info["flavor"],token)    
#    image_verify(data_info["image"],token)
    network_1_id= create_network(data_info["network_1"],data_info["mtu"],data_info["subnet_name"],data_info["cidr"],token)

main()



