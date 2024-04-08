import pulumi
from pulumi_azure_native import resources, network, compute
from pulumi_azure_native.resources import ResourceGroup


resource_group = ResourceGroup('rg')

name,
virtual_network = network.VirtualNetwork('vnet',
    resource_group_name=resource_group.
    location=resource_group.location,
    address_space={'address_prefixes': ['10.0.0.0/16']}
)


public_subnet = network.Subnet('public-subnet',
    resource_group_name=resource_group.name,
    virtual_network_name=virtual_network.name,
    address_prefix='10.0.1.0/24'
)


private_subnet = network.Subnet('private-subnet',
    resource_group_name=resource_group.name,
    virtual_network_name=virtual_network.name,
    address_prefix='10.0.2.0/24'
)


public_ip_wg = network.PublicIPAddress('publicip-wg',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    public_ip_allocation_method='Static'
)

nsg_wg = network.NetworkSecurityGroup('nsg-wg',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    security_rules=[
        {
            'name': 'WireGuardRule',
            'direction': 'Inbound',
            'access': 'Allow',
            'protocol': 'Udp',
            'source_port_range': '*',
            'destination_port_range': '51820',
            'source_address_prefix': '*',
            'destination_address_prefix': '*',
            'priority': 100
        },
        {
            'name': 'SSHRule',
            'direction': 'Inbound',
            'access': 'Allow',
            'protocol': 'Tcp',
            'source_port_range': '*',
            'destination_port_range': '22',
            'source_address_prefix': '*',
            'destination_address_prefix': '*',
            'priority': 101
        },
        {
            'name': 'AllowAllOutbound',
            'direction': 'Outbound',
            'access': 'Allow',
            'protocol': '*',
            'source_port_range': '*',
            'destination_port_range': '*',
            'source_address_prefix': '*',
            'destination_address_prefix': '*',
            'priority': 1000
        }
    ]
)



network_interface_wg = network.NetworkInterface('nic-wg',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    ip_configurations=[{
        'name': 'ipconfig-wg',
        'subnet': {'id': public_subnet.id},
        'public_ip_address': {'id': public_ip_wg.id}
    }]
)


vm_wg = compute.VirtualMachine('vm-wg',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    hardware_profile={'vm_size': 'Standard_B1s'},
    os_profile={
        'computer_name': 'wg-server',
        'admin_username': 'azureuser',
        'admin_password': pulumi.Output.secret('YourPassword123!')
    },
    network_profile={
        'network_interfaces': [{'id': network_interface_wg.id}]
    },
    storage_profile={
        'image_reference': {
            'publisher': 'Canonical',
            'offer': 'UbuntuServer',
            'sku': '18.04-LTS',
            'version': 'latest'
        }
    }
)


def execute_script_on_vm(vm: compute.VirtualMachine, script: str):
    pulumi.runtime.run_in_stack(lambda: pulumi.log.info(f"Executing script on VM '{vm.name}'"))
    pulumi.runtime.run_in_stack(lambda: pulumi.log.info(script))
    # Replace this part with your code to execute script on the VM


wireguard_script = """#!/bin/bash
# Install WireGuard
sudo apt-get update && apt-get install -y wireguard
sudo apt  install awscli -y
sudo sysctl -w net.ipv4.ip_forward=1 

# Configure WireGuard
echo "[Interface]
PrivateKey = qBJ0mKuFN6nGtmE0B+QcEYzKPO805ZlUXEwgfWoerno=
Address = 10.0.2.5/32, 10.92.112.1/32, 10.110.174.125/32, 192.168.49.5/32, 192.168.49.7/32
ListenPort = 51820
[Peer]
PublicKey = aEaH+9SnjdrgjqeFcBnpb5fyGbqREBhFbMpf1tJQHV0=
AllowedIPs = 10.0.0.0/16
Endpoint = 115.110.201.147:51820
[Peer]
PublicKey = izcycGRg+9zVoF9fSzjYaKwjzc7ESWTmKuUXuZ7ZZjM=
AllowedIPs = 192.168.49.0/24
Endpoint = 52.6.54.217:51820" > /etc/wireguard/wg0.conf

# Start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
"""

execute_script_on_vm(vm_wg, wireguard_script)

pulumi.export('public_ip_wg', public_ip_wg.ip_address)
