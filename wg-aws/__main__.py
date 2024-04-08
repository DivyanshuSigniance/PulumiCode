import pulumi
from pulumi_aws import ec2
import pulumi_aws as aws


wg_server_security_group_a = ec2.SecurityGroup("wg-server-sg-a",
    vpc_id = "vpc-023ba954d5f915fcb",
    description="Allow inbound WireGuard traffic",
    ingress=[
        {
            "protocol": "udp",
            "from_port": 51820,
            "to_port": 51820,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],  
        }
    ],
    egress=[
        {
            "protocol": "-1",  
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ]
)
existing_eip_allocation_id = "52.6.54.217"

wg_server_instance_a = ec2.Instance("wg-server-a",
    instance_type="t3.micro",
    vpc_security_group_ids=[wg_server_security_group_a.id],
    subnet_id = "subnet-006076103fef351f1",
    ami="ami-080e1f13689e07408",
    key_name="revdau-pulumi-key",
    tags={
        "Name": "WireguardVPN"  
    },
    user_data=pulumi.Output.all(wg_server_security_group_a.id).apply(lambda args: f"""#!/bin/bash
    # Install WireGuard
    apt-get update && apt-get install -y wireguard
    sudo sysctl -w net.ipv4.ip_forward=1 
                                                                     
    # Configure WireGuard
    echo "[Interface]
    PrivateKey = 2KpsKhZ6/eQTArj1h3GnqrtO9LnDvm4aGc2imLNUQG8=
    Address = 192.168.49.14/32,  10.92.112.1/32, 10.110.174.125/32, 10.0.2.5/32, 192.168.49.5/32, 192.168.49.7/32
    ListenPort = 51820

    [Peer]
    PublicKey = aEaH+9SnjdrgjqeFcBnpb5fyGbqREBhFbMpf1tJQHV0=
    AllowedIPs =  192.168.49.0/24
    Endpoint = 115.110.201.147:51820
                                                                     
    [Peer]
    PublicKey = izcycGRg+9zVoF9fSzjYaKwjzc7ESWTmKuUXuZ7ZZjM=
    AllowedIPs = 10.0.0.0/16
    Endpoint = 4.227.169.126:51820" > /etc/wireguard/wg0.conf

    # Start WireGuard
    sudo systemctl enable wg-quick@wg0
    sudo systemctl start wg-quick@wg0
    """)
)
eip_association = aws.ec2.EipAssociation("wg-server-eip-association-a",
    instance_id=wg_server_instance_a.id,
    allocation_id= "eipalloc-06373163bff4be5a5"
)


