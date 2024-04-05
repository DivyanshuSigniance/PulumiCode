import pulumi
import pulumi_azure as azure
import pulumi_azure_native as azure_native

# Create Azure Resource Group
resource_group = azure.core.ResourceGroup('rg')

# Create Virtual Network
virtual_network = azure_native.network.VirtualNetwork('vnet',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    address_space={'address_prefixes': ['10.0.0.0/16']}
)

# Create Public Subnet
public_subnet = azure_native.network.Subnet('public-subnet',
    resource_group_name=resource_group.name,
    virtual_network_name=virtual_network.name,
    address_prefix='10.0.1.0/24'
)

# Create Private Subnet
private_subnet = azure_native.network.Subnet('private-subnet',
    resource_group_name=resource_group.name,
    virtual_network_name=virtual_network.name,
    address_prefix='10.0.2.0/24'
)

# Create Public IP Address for WireGuard Server
public_ip_wg = azure_native.network.PublicIPAddress('publicip-wg',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    public_ip_allocation_method='Static'
)

# Create Network Interface for WireGuard Server
network_interface_wg = azure_native.network.NetworkInterface('nic-wg',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    ip_configurations=[{
        'name': 'ipconfig-wg',
        'subnet': {'id': public_subnet.id},
        'public_ip_address': {'id': public_ip_wg.id}
    }]
)

# Create Virtual Machine for WireGuard Server
vm_wg = azure_native.compute.VirtualMachine('vm-wg',
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
            'sku': '16.04-LTS',
            'version': 'latest'
        }
    }
)

# Create Virtual Machine for Private Subnet
vm_private = azure_native.compute.VirtualMachine('vm-private',
    resource_group_name=resource_group.name,
    location=resource_group.location,
    hardware_profile={'vm_size': 'Standard_B1s'},
    os_profile={
        'computer_name': 'vm-private',
        'admin_username': 'azureuser',
        'admin_password': pulumi.Output.secret('YourPassword123!')
    },
    network_profile={
        'network_interfaces': [{
            'id': azure_native.network.NetworkInterface("nic-vm-private",
                resource_group_name=resource_group.name,
                location=resource_group.location,
                ip_configurations=[{
                    'name': 'ipconfig-vm-private',
                    'subnet': {'id': private_subnet.id}
                }]
            ).id
        }]
    },
    storage_profile={
        'image_reference': {
            'publisher': 'Canonical',
            'offer': 'UbuntuServer',
            'sku': '16.04-LTS',
            'version': 'latest'
        }
    }
)

# Install WireGuard
wireguard_script = """#!/bin/bash
# Install WireGuard
apt-get update && apt-get install -y wireguard
sudo sysctl -w net.ipv4.ip_forward=1 

# Configure WireGuard
# Add your WireGuard configuration here

# Start WireGuard
# Add commands to start WireGuard
"""

# Apply WireGuard installation script as VM extension
extension = azure_native.compute.VirtualMachineExtension('vmextension-wg',
    resource_group_name=resource_group.name,
    virtual_machine_name=vm_wg.name,
    publisher='Microsoft.Azure.Extensions',
    type='CustomScript',
    type_handler_version='2.1',
    settings={
        'script': wireguard_script
    },
    protected_settings={}
)

# Output public IP of the WireGuard Server
pulumi.export('public_ip_wg', public_ip_wg.ip_address)
