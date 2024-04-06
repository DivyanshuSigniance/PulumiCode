import pulumi
from pulumi_azure_native import resources, network, compute
from pulumi_azure_native.resources import ResourceGroup

# Create Azure Resource Group
resource_group = ResourceGroup('rg')

# Create Virtual Network
virtual_network = network.VirtualNetwork('vnet',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    address_space={'address_prefixes': ['10.0.0.0/16']}
)

# Create Public Subnet
public_subnet = network.Subnet('public-subnet',
    resource_group_name=resource_group.name,
    virtual_network_name=virtual_network.name,
    address_prefix='10.0.1.0/24'
)

# Create Private Subnet
private_subnet = network.Subnet('private-subnet',
    resource_group_name=resource_group.name,
    virtual_network_name=virtual_network.name,
    address_prefix='10.0.2.0/24'
)

# Create Public IP Address for WireGuard Server
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


# Create Network Interface for WireGuard Server
network_interface_wg = network.NetworkInterface('nic-wg',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    ip_configurations=[{
        'name': 'ipconfig-wg',
        'subnet': {'id': public_subnet.id},
        'public_ip_address': {'id': public_ip_wg.id}
    }]
)

# Create Virtual Machine for WireGuard Server
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

# Connect to the VM and execute the WireGuard installation script
def execute_script_on_vm(vm: compute.VirtualMachine, script: str):
    pulumi.runtime.run_in_stack(lambda: pulumi.log.info(f"Executing script on VM '{vm.name}'"))
    pulumi.runtime.run_in_stack(lambda: pulumi.log.info(script))
    # Replace this part with your code to execute script on the VM

# Install WireGuard
wireguard_script = """#!/bin/bash
# Install WireGuard
sudo apt-get update && apt-get install -y wireguard
sudo sysctl -w net.ipv4.ip_forward=1 

# Configure WireGuard
echo "[Interface]
PrivateKey = qBJ0mKuFN6nGtmE0B+QcEYzKPO805ZlUXEwgfWoerno=
Address = 10.0.2.4/32
ListenPort = 51820
[Peer]
PublicKey = izcycGRg+9zVoF9fSzjYaKwjzc7ESWTmKuUXuZ7ZZjM=
AllowedIPs = 10.0.2.4/32, 172.31.49.96/32, 172.31.49.215/32, 172.31.14.237/32
Endpoint = 3.238.8.173:51820" > /etc/wireguard/wg0.conf

# Start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
"""

# Apply WireGuard installation script on the VM
execute_script_on_vm(vm_wg, wireguard_script)

# Output public IP of the WireGuard Server
pulumi.export('public_ip_wg', public_ip_wg.ip_address)
