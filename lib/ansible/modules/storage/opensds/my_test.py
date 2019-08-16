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


def create_volume(url, name, size, option):
    if option == "get":
        res = requests.get(url)
        print ("res==:",res.json())
        return res.json()
    if option == "post":
        data = {'name': name, 'size': size}
        url = "http://127.0.0.1:50040/v1beta/e93b4c0934da416eb9c8d120c5d04d96/block/volumes/"
        # data = {'name':'pravin_test',
        #         'description':'This is just for test',
        #         'size': 1}
        res = requests.post(url= url, json=data)
        print ("res==:",res.json())
        return res.json()

def run_module():
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
        profile_id=dict(type='str'),
        snapshot_id=dict(type='str'),
        attach_status=dict(type='str'),
        new=dict(type='bool', required=False, default=False)
    )
    url = "http://127.0.0.1:50040/v1beta/e93b4c0934da416eb9c8d120c5d04d96/block/volumes/"

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    facts = {}
    facts['test_vol'] = {'peers': "peers", 'volumes': "volumes", 'quotas': "quotas"}
    result = dict(
        changed=False,
        original_message='',
        message=[],
        size = 1,
        output={}
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # if module.check_mode:
    #     module.exit_json(**result)
    #
    # if response.status_code >= 500:
    #     print('[!] [{0}] Server Error'.format(response.status_code))
    #     return None
    # elif response.status_code == 404:
    #     print('[!] [{0}] URL not found: [{1}]'.format(response.status_code,api_url))
    #     return None
    # elif response.status_code == 401:
    #     print('[!] [{0}] Authentication Failed'.format(response.status_code))
    #     return None
    # elif response.status_code == 400:
    #     print('[!] [{0}] Bad Request'.format(response.status_code))
    #     return None
    # elif response.status_code >= 300:
    #     print('[!] [{0}] Unexpected Redirect'.format(response.status_code))
    #     return None
    # elif response.status_code == 200:
    #     ssh_keys = json.loads(response.content.decode('utf-8'))
    #     return ssh_keys
    # else:
    #     print('[?] Unexpected Error: [HTTP {0}]: Content: {1}'.format(response.status_code, response.content))
    # return None

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['message'] = create_volume(url, module.params['name'], module.params['size'], "post")
    result['output'] = facts
    result['size'] = module.params['size']

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if module.params['new']:
        result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
