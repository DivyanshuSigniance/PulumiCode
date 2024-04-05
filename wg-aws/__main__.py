import pulumi
from pulumi_aws import ec2
import pulumi_aws as aws


wg_server_security_group_a = ec2.SecurityGroup("wg-server-sg-a",
    vpc_id = "vpc-04a2c766b89e457e8",
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


wg_server_instance_a = ec2.Instance("wg-server-a",
    instance_type="t2.micro",
    vpc_security_group_ids=[wg_server_security_group_a.id],
    subnet_id = " subnet-0001a995c2b8a486c",
    ami="ami-080e1f13689e07408",
    key_name="pulumi",
    user_data=pulumi.Output.all(wg_server_security_group_a.id).apply(lambda args: f"""#!/bin/bash
    # Install WireGuard
    apt-get update && apt-get install -y wireguard
    sudo sysctl -w net.ipv4.ip_forward=1 
                                                                     
    # Configure WireGuard
    echo "[Interface]
    PrivateKey = 2KpsKhZ6/eQTArj1h3GnqrtO9LnDvm4aGc2imLNUQG8=
    Address = 172.31.49.96/32, 172.31.49.215/32
    ListenPort = 51820
                                                                     
    [Peer]
    PublicKey = Y2yC6BlL5+F2xwFoWZLdNLKFhwwkwa7Hr3gNXLJFU3Q=
    AllowedIPs =  10.0.1.13/32" > /etc/wireguard/wg0.conf

    # Start WireGuard
    sudo systemctl enable wg-quick@wg0
    sudo systemctl start wg-quick@wg0
    """)
)


