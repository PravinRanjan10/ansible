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

# get volume is to get the volume details
def get_volume(url, vol_id):
    if vol_id != "":
        url = url + vol_id
    res = requests.get(url)
    return res.status_code, res.json()

# To create volume
def create_volume(url, name, snapshot_id, size):
    data = {'name': name, 'snapshotId': snapshot_id, "size": size}
    res = requests.post(url= url, json=data)
    return res.status_code, res.json()

# get volume is to get the volume details
def get_snapshot(url, snap_id):
    if snap_id != "":
        url = url + snap_id
    res = requests.get(url)
    return res.status_code, res.json()

# To create volume
def create_snapshot(url, name, vol_id):
    data = {'name': name, 'volumeId': vol_id}
    res = requests.post(url= url, json=data)
    return res.status_code, res.json()

# To delte the volume
def delete_snapshot(url, snap_id):
    url = url + snap_id
    res = requests.delete(url)
    try:
        return res.status_code, res.json()
    except:
        return "1", "SNAPSHOT IS SUCCESSFULLY DELETED!!"

def opensds_snapshot():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        action=dict(type='str', required=True),
        option=dict(type='str', required=True),
        name=dict(type='str', required=True),
        size=dict(type='int', required=True),
        vol_id=dict(type='str'),
        snap_id=dict(type='str'),
        attach_status=dict(type='str'),
        new=dict(type='bool', required=False, default=False)
    )
    url = "http://127.0.0.1:50040/v1beta/e93b4c0934da416eb9c8d120c5d04d96/block/snapshots/"
    vol_url = "http://127.0.0.1:50040/v1beta/e93b4c0934da416eb9c8d120c5d04d96/block/volumes/"

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
    option = module.params['option']
    vol_id = module.params['vol_id']
    snap_id = module.params['snap_id']
    attach_status = module.params['attach_status']
    action = module.params['action']

    # Driver code to create and delete volume
    if action == "create" and option == "snapshot":
      rc, create_out = create_snapshot(url, name, vol_id)
      # result['create_snapshot'] = create_out
      # result['status_code'] = rc
      if rc == 400:
          result['CREATE_MESSAGE:'] = create_out
      else:
          # Add 2-3 ms to get volume available
          time.sleep(2)
          snapshot_id = create_out['id']
          rc, get_out = get_snapshot(url, snapshot_id)
          if get_out['status'] == "error":
              result['CREATE_MESSAGE:'] = "Snapshot creation fail!!!. Please check the log for more details."

          if get_out['status'] == "available":
              result['CREATE_MESSAGE:'] = "SNAPSHOT IS SUCCESSFULLY CREATED!!!."

    elif action == "delete" and option == "snapshot":
         if snap_id:
             rc, delete_msg = delete_snapshot(url, snap_id)
             result['DELETE_MESSAGE1:'] = delete_msg
         else:
             rc, snapshot_list = get_snapshot(url, "")
             # result['debug_message'] = snapshot_list
             filter = [key  for key  in snapshot_list  if key['name'] == name]
             if len(filter) == 0:
                 result['DELETE_MESSAGE2:'] = "There is no snapshot with the name " + name
             elif len(filter) == 1:
                 snap_id = filter[0]['id']
                 rc, delete_msg = delete_snapshot(url, snap_id)
                 result['DELETE_MESSAGE3:'] = delete_msg
             else:
                 result['DELETE_MESSAGE4:'] = "More than one snapshot found with same name. So we could not delete the snapshot"

    elif action == "create" and  option == "volume_from_snapshot":
        if snap_id:
            rc, create_out = create_volume(vol_url, name, snap_id, size)
            result['create_out'] = create_out
            # Add 2-3 ms to get volume available
            time.sleep(2)

            vol_id = create_out['id']
            rc, get_out = get_volume(vol_url, vol_id)
            if get_out['status'] == "error":
               result['CREATE_MESSAGE:'] = "Volume creation fail!!!. Please check the log for more details."

            if get_out['status'] == "available":
               result['CREATE_MESSAGE:'] = "VOLUME IS SUCCESSFULLY CREATED!!!."

    if module.params['new']:
        result['changed'] = True

    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    module.exit_json(**result)

def main():
    opensds_snapshot()

if __name__ == '__main__':
    main()
