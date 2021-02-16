import requests
import json
import os
import sys
from automation_code import *

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
    
    if args[0] == 'ceph' :
        print(args[1] +" Feature validation with ceph")
    else:
        print("Please pass atleat 2 arg")

    #create_volume(data_info["vol_name1"],data_info["vol_size1"],admin_id,token)
    #attach_volume("myserver","vdn",admin_id,token)
    #delete_volume(data_info["vol_name1"],admin_id,token)
    #create_keypair(data_info["key_name"],data_info["fingerprint"],data_info["key_type"],data_info["public_key"],data_info["key_user_id"],token)
    #flavor_verify(data_info["flavor"],token)
   
        
#    image_verify(data_info["image"],token)
#   network_1_id= create_network(data_info["network_1"],data_info["mtu"],data_info["subnet_name"],data_info["cidr"],token)

main(sys.argv[1:])

