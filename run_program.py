# create two ec2 instance. one is Node1, and other is Node 2.
# Wait till two instances are alive
# get the Public Ip of each.
# call the API to update the "other" parameter IP.
import boto3

from create_ec2_instance import create_ec2_instance_full
from ec2_manager import EC2Manager

manager = EC2Manager(setup_file='setup.sh')

print("Creating instance 1")
instance1 = manager.create_ec2_instance()  # this will create the security group and key pair if they don't exist, and launch the instance
manager.adjust_security_inbound()
ip1 = manager.get_public_ip(instance1)

print("Creating Node instance 2")
instance2 = manager.create_ec2_instance()
manager.adjust_security_inbound()
ip2 = manager.get_public_ip(instance2)

print(f"2 EC2 instance were created with IP 1 {ip1} 2 {ip2}")