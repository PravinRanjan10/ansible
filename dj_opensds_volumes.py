#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_test1
short_description: This is my test module
version_added: "2.4"
description:
    - "This is my longer description explaining my test module"
options:
    name:
        description:
            - This is the message to send to the test module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false
extends_documentation_fragment:
    - azure
author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_test:
    name: hello world
# pass in a message and have changed true
- name: Test with a message and changed output
  my_test:
    name: hello world
    new: true
# fail the module
- name: Test failure of the module
  my_test:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import time
import json

def get_token(ip):
    url = "https://"+ ip + "/identity/v3/auth/tokens"
    headers = {
        "content-type": "application/json",
        "cache-control": "no-cache",
        "postman-token": "4747fc24-9d09-cd22-0aa8-07119801908a"
    }
    data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "name": "name",
                        "domain": {"name": "Default"},
                        "password": "123"
                    }
                }
            },
            "scope": {
                "project": {
                    "domain": {
                        "name": "Default"
                    },
                    "name": "opensds"
                }
            }
        }
    }
    resp = requests.post(url=url, headers=headers, json=data, verify=False)
    if resp.status_code != 201:
        print("Request for OpenSDS Token failed ", resp.status_code)
        raise Exception('Request for OpenSDS Token failed')

    token = resp.headers['X-Subject-Token']
    return token


# get volume is to get the volume details
def get_volume(url, token, vol_id):
    if vol_id != "":
        url = url + vol_id
    headers = {"x-auth-token": token}

    res = requests.get(url, headers=headers, verify=False)
    return res.status_code, res.json()

# To create volume
def create_volume(url, token, name, size, description,
          availability_zone, status, pool_id, profile_id,
          snapshot_id, attach_status, option):
    data = {"name": "PJ2", "size": 1, "profileId": "opensds-SSD", "availabilityZone": "az"}
    headers = {"x-auth-token": token}

    res = requests.post(url= url, headers=headers, json=data, verify=False)
    return res.status_code, res.json()
# To delte the volume
def delete_volume(url, token, vol_id):
    url = url + vol_id
    headers = {"x-auth-token": token}
    res = requests.delete(url, headers=headers, verify=False)
    try:
       return res.status_code, res.json()
    except:
       return res.status_code, "VOLUME IS SUCCESSFULLY DELETED!!"

def opensds():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        action=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str'),
        size=dict(type='int', required=True),
        output=dict(type='dict', required=True),
        availability_zone=dict(type='str'),
        status=dict(type='str'),
        pool_id=dict(type='str'),
        vol_id=dict(type='str'),
        profile_id=dict(type='str'),
        snapshot_id=dict(type='str'),
        attach_status=dict(type='str'),
        new=dict(type='bool', required=False, default=False)
    )
    #url = "http://127.0.0.1:50040/v1beta/e93b4c0934da416eb9c8d120c5d04d96/block/volumes/"
    url = "https://*****:28818/v1beta/3ca2330f78754dddb72464872b74591c/block/volumes/"

    result = dict(
        changed = False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Variable names based on input parameter
    name = module.params['name']
    size = module.params['size']
    description = module.params['description']
    availability_zone= module.params['availability_zone']
    status = module.params['status']
    pool_id = module.params['pool_id']
    profile_id = module.params['profile_id']
    snapshot_id = module.params['snapshot_id']
    attach_status = module.params['attach_status']
    action = module.params['action']

    # Driver code to create and delete volume
    if action == "create":

      token = get_token("****:****")

      rc, create_out = create_volume(url, token, name, size, description,
                availability_zone, status, pool_id, profile_id,
                snapshot_id, attach_status, "post"
                )
      result['debug_message'] = create_out
      result['rcc'] = rc
      # Add 2-3 ms to get volume available
      time.sleep(2)
      vol_id = create_out['id']
      result['vol_id'] =  vol_id
      rc, get_out = get_volume(url, token, vol_id)
      result['debug_message'] = get_out
      if get_out['status'] == "error":
         result['CREATE_MESSAGE:'] = "Volume creation fail!!!. Please check the log for more details."

      if get_out['status'] == "available":
         result['CREATE_MESSAGE:'] = "VOLUME IS SUCCESSFULLY CREATED!!!."

    elif action == "delete":
        token = get_token("****:***")

        vol_id = module.params['vol_id']
        if vol_id:
            rc, delete_msg = delete_volume(url, token, vol_id)
            result['DELETE_MESSAGE:'] = delete_msg
            result['RETURN_CODE:'] = rc
        else:
            rc, volumes_list = get_volume(url, token, "")
            #result['debug_message'] = volumes_list
            filter = [key  for key  in volumes_list  if key['name'] == name]
            if len(filter) == 0:
                result['DELETE_MESSAGE:'] = "There is no volume with the name " + name
            elif len(filter) == 1:
                vol_id = filter[0]['id']
                rc, delete_msg = delete_volume(url, token, vol_id)
                result['DELETE_MESSAGE:'] = delete_msg
            else:
                result['DELETE_MESSAGE:'] = "More than one volumes found with same name. So we could not delete the volume"

    if module.params['new']:
        result['changed'] = True

    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    module.exit_json(**result)

def main():
    opensds()

if __name__ == '__main__':
    main()
