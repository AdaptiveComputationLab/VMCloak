#!/usr/bin/env python
# Copyright (C) 2014 Jurriaan Bremer.
# This file is part of VMCloak - http://www.vmcloak.org/.
# See the file 'docs/LICENSE.txt' for copying permission.

from ConfigParser import ConfigParser
import json
import logging
import os

from lib.rand import random_string


log = logging.getLogger(__name__)


def configure_winnt_sif(path, args):
    values = {
        'PRODUCTKEY': args.serial_key,
        'COMPUTERNAME': random_string(8, 16),
        'FULLNAME': '%s %s' % (random_string(4, 8), random_string(4, 10)),
        'ORGANIZATION': '',
        'WORKGROUP': random_string(4, 8),
        'KBLAYOUT': args.keyboard_layout,
    }

    buf = open(path, 'rb').read()
    for key, value in values.items():
        buf = buf.replace('@%s@' % key, value)
    return buf


class Configuration(object):
    def __init__(self):
        self.conf = {}

    def _process_value(self, value):
        if isinstance(value, str) and value.startswith('~'):
            return os.getenv('HOME') + value[1:]
        if value in ('true', 'True', 'on', 'yes', 'enable'):
            return True
        if value in ('false', 'False', 'off', 'no', 'disable'):
            return False
        return value

    def from_args(self, args):
        for key, value in args._get_kwargs():
            if key not in self.conf or value:
                self.conf[key] = self._process_value(value)

    def from_file(self, path):
        p = ConfigParser()
        p.read(path)
        for key in p.options('vmcloak'):
            self.conf[key.replace('-', '_')] = \
                self._process_value(p.get('vmcloak', key))

    def from_defaults(self, defaults):
        for key, value in defaults.items():
            if self.conf[key] is None:
                self.conf[key] = value

    def __getattr__(self, key):
        return self.conf[key]


def vboxmanage_path(s):
    if os.path.isfile(s.vboxmanage):
        return s.vboxmanage

    if not s.cuckoo:
        print '[-] Please provide your Cuckoo root directory.'
        print '[-] Or provide the path to the VBoxManage executable.'
        exit(1)

    conf_path = os.path.join(s.cuckoo, 'conf', 'virtualbox.conf')

    try:
        from lib.cuckoo.common.config import Config
        vboxmanage = Config(conf_path).virtualbox.path
    except:
        log.error('Unable to locate VBoxManage path, please '
                  'configure conf/virtualbox.conf properly.')
        exit(1)

    if not os.path.isfile(vboxmanage):
        log.error('The configured VBoxManage path in Cuckoo does not '
                  'exist, please configure $CUCKOO/conf/virtualbox.conf '
                  'properly.')
        exit(1)

    return vboxmanage


def load_hwconf(profile, dirpath='hwconf'):
    ret = {}

    if profile is not None:
        files = ['%s.json' % profile]
    else:
        files = os.listdir(dirpath)

    for fname in files:
        if not fname.endswith('.json'):
            continue

        conf = json.load(open(os.path.join(dirpath, fname), 'rb'))
        for key, value in conf.items():
            if key not in ret:
                ret[key] = []

            if isinstance(value, list):
                ret[key].extend(value)
            else:
                ret[key].append(value)

    return ret
