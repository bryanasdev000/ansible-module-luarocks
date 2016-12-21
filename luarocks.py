#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Rahul AG <r@hul.ag>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re
# Import module snippets
from ansible.module_utils.basic import *

ANSIBLE_METADATA = {
    'status': ['preview'],
    'version': '1.0'
}

DOCUMENTATION = '''
---
module: luarocks
short_description: Manage lua rocks with luarocks
description:
  - Manage lua rocks with luarocks
options:
  executable:
    description:
      - The name of the luarocks executable to use
    required: false
  keep_other_versions:
    description:
      - Keep other versions of the rock
    required: false
    default: no
    choices: [ "yes", "no" ]
  local:
    description:
      - Use the local luarocks tree
    required: false
    default: no
    choices: [ "yes", "no" ]
  name:
    description:
      - The name of a luarocks package to install
    required: true
  state:
    description:
      - The state of the lua rocks
    required: false
    default: present
    choices: [ "present", "absent" ]
  server:
    description:
      - A server URI to fetch rocks and rockspecs from
    required: false
  tree:
    description:
      - The luarocks tree to operate on
    required: false
  version:
    description:
      - The version to be installed
    required: false
'''

EXAMPLES = '''
- name: Install the "luasocket" rock.
  luarocks:
    name: luasocket

- name: Install the "luasocket" rock from a specific server.
  luarocks:
    name: luasocket
    server: http://http://rocks.moonscript.org

- name: Install the "luasocket" rock into your local tree.
  luarocks:
    name: luasocket
    local: yes

- name: Install version 2.0.2 of the "luasocket" rock.
 luarocks:
    name: luasocket
    version: '2.0.2'

- name: Remove the "luasocket" rock.
  luarocks:
    name: luasocket
    state: absent
'''


class Luarocks(object):
    def __init__(self, module, **kwargs):
        self.module = module
        self.executable = kwargs['executable']
        self.name = kwargs['name']
        self.server = kwargs['server']
        self.tree = kwargs['tree']
        self.local = kwargs['local']
        self.keep_other_versions = kwargs['keep_other_versions']
        self.version = kwargs['version']

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = [self.executable]

            if self.local and self.tree:
                self.module.fail_json(msg='cannot set local=True and tree')

            if self.local:
                cmd.append('--local')

            if self.tree:
                cmd.append('--tree={}'.format(self.tree))

            if self.server:
                cmd.append('--server={}'.format(self.server))

            cmd.extend(args)

            if self.keep_other_versions:
                cmd.append('--keep')

            if self.name:
                cmd.append(self.name)

            if self.version:
                cmd.append(self.version)

            rc, out, err = self.module.run_command(cmd, check_rc=check_rc)
            return out
        return ''

    def list(self):
        cmd = ['list', '--porcelain']

        out = self._exec(cmd, run_in_check_mode=True, check_rc=False)
        installed = re.findall(r'^(\S+)\s+\S+\s+installed\s+\S+', out, re.MULTILINE)

        return installed

    def install(self):
        return self._exec(['install'])

    def remove(self):
        return self._exec(['remove'])


def main():
    arg_spec = dict(
        executable=dict(default='luarocks', required=False),
        name=dict(default=None),
        state=dict(default='present', choices=['present', 'absent', ]),
        version=dict(default=None, required=False),
        keep_other_versions=dict(default=False, required=False, type='bool'),
        local=dict(default=False, required=False, type='bool'),
        tree=dict(default=None, required=False, type='path'),
        server=dict(default=None, required=False),
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
    )

    executable = module.params['executable']
    name = module.params['name']
    state = module.params['state']
    version = module.params['version']
    keep_other_versions = module.params['keep_other_versions']
    local = module.params['local']
    tree = module.params['tree']
    server = module.params['server']

    luarocks = Luarocks(
        module,
        executable=executable,
        name=name,
        version=version,
        keep_other_versions=keep_other_versions,
        local=local,
        tree=tree,
        server=server,
    )

    changed = False
    if state == 'present':
        installed = luarocks.list()
        if name not in installed:
            changed = True
            luarocks.install()
    else:  # Absent
        installed = luarocks.list()
        if name in installed:
            changed = True
            luarocks.remove()

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
