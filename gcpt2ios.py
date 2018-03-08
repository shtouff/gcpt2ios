#!/usr/bin/env python3

from enum import Enum
import os
import re

import click
import napalm


PROJECT_REGEX = re.compile(r'^(?P<project_name>[a-zA-Z0-9-]+)-(?P<project_id>[0-9a-fA-F]{8})-0$')


config = {
    'routers': {
        'vpn-01': {
            'fqdn': 'vpn-01.par-4.r.blbl.cr',
            'napalm_driver': 'ios',
            'login': 'shtouff',
            'password': '**********',
        }
    }
}


@click.command()
@click.argument('router_name')
@click.argument('bgp_local_asn')
@click.argument('bgp_local_ip')
@click.argument('bgp_peer_asn')
@click.argument('bgp_peer_ip')
@click.argument('ip_cidr_range')
@click.argument('suffix')
@click.argument('shared_secret')
@click.argument('vpn_local')
@click.argument('vpn_peer')
def gcpt2ios(
        router_name,
        bgp_local_asn,
        bgp_local_ip,
        bgp_peer_asn,
        bgp_peer_ip,
        ip_cidr_range,
        suffix,
        shared_secret,
        vpn_local,
        vpn_peer
):
    router = config['routers'][router_name]
    driver = napalm.get_network_driver(router['napalm_driver'])
    device = driver(hostname=router['fqdn'], username=router['login'], password=router['password'])

    device.open()
    ifaces = device.get_interfaces()

    m = PROJECT_REGEX.match(suffix)
    project_name = m.group('project_name')
    new_project_id = m.group('project_id')

    iface_names = [x for x in ifaces.keys() if ifaces[x]['description'].find(project_name) != -1]
    assert len(iface_names) == 1
    iface_name = iface_names[0]

    matched_words = [m for m in map(lambda w: PROJECT_REGEX.match(w), ifaces[iface_name]['description'].split(' ')) if m is not None]
    assert len(matched_words) == 1
    old_project_id = matched_words[0].group('project_id')

    device.load_template('no-crypto-keyring', template_path=os.getcwd() + '/jinja2', project_name='pipo', old_project_id='88776655')

    diff = device.compare_config()
    print(diff)

    device.commit_config()
    device.close()


if __name__ == '__main__':
    gcpt2ios()
