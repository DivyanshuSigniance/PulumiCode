import pulumi
from pulumi_aws import ec2
import pulumi_aws as aws


wg_server_security_group_a = ec2.SecurityGroup("wg-server-sg-a",
    vpc_id = "vpc-01c0abc6916d60e8d",
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

existing_eip_allocation_id = "35.167.23.102"


wg_server_instance_a = ec2.Instance("wg-server-a",
    instance_type="t2.micro",
    vpc_security_group_ids=[wg_server_security_group_a.id],
    subnet_id = "subnet-0fe452d1c795a5248",
    ami="ami-08116b9957a259459",
    key_name="poc-polumi",
    user_data=pulumi.Output.all(wg_server_security_group_a.id).apply(lambda args: f"""#!/bin/bash
    # Install WireGuard
    apt-get update && apt-get install -y wireguard
    sudo sysctl -w net.ipv4.ip_forward=1                                                                

    # Configure WireGuard
    echo "[Interface]
    PrivateKey = qBJ0mKuFN6nGtmE0B+QcEYzKPO805ZlUXEwgfWoerno=
    Address = 10.0.1.13/32
    ListenPort = 51820
                                                                     
    [Peer]
    PublicKey = izcycGRg+9zVoF9fSzjYaKwjzc7ESWTmKuUXuZ7ZZjM=
    AllowedIPs = 10.0.1.13/32, 172.31.49.96/32, 172.31.49.215/32
    Endpoint = 44.203.17.253:51820" > /etc/wireguard/wg0.conf

    # Start WireGuard
    sudo systemctl enable wg-quick@wg0
    sudo systemctl start wg-quick@wg0
    """)
)
eip_association = aws.ec2.EipAssociation("wg-server-eip-association-a",
    instance_id=wg_server_instance_a.id,
    allocation_id= "eipalloc-0ddc2b1a2cef8761e"
)



