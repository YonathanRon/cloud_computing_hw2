from ec2_manager import EC2Manager
from role_policy_manager import IAMRoleManager

#
# print(f"2 EC2 instance were created with IP 1 {ip1} 2 {ip2}")
role_name = 'EC2ManagementRole'
policy_name = 'EC2ManagementPolicy'

iam_manager = IAMRoleManager(role_name, policy_name)
iam_manager.create_role()
iam_manager.create_policy()
iam_manager.attach_policy_to_role()

manager = EC2Manager(role_name=iam_manager.get_or_create_instance_profile())

print("Creating instance 1.. ")
instance1 = manager.create_ec2_instance(setup_file='node_server_setup.sh')
manager.adjust_security_inbound()
ip1 = manager.get_public_ip(instance1)

print("Creating instance 2..")
instance2 = manager.create_ec2_instance(setup_file='node_server_setup.sh')
manager.adjust_security_inbound()
ip2 = manager.get_public_ip(instance2)

