import requests
import time
from ec2_manager import EC2Manager
from role_policy_manager import IAMRoleManager

#
#
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

print(f"2 EC2 instance were created with IP 1 {ip1} 2 {ip2}")

#### WAIT FOR SERVERS TO BE READY BEFORE START WORKING ####


ips = [ip1, ip2]  # replace with actual IPs


def check_health(ip):
    try:
        response = requests.get(f"http://{ip}:8001/health")
        if response.status_code == 200:
            data = response.json()
            if 'status' in data and data['status'] == 'ok':
                return True
        return False
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
        return False


start_time = time.time()
timeout = 300  # 5 minutes
all_ready = False

while time.time() - start_time < timeout:
    all_ready = all(check_health(ip) for ip in ips)
    if all_ready:
        break
    time.sleep(10)  # wait 10 seconds before trying again

if all_ready:
    print("All instances are ready.")
else:
    print("Timeout exceeded and not all instances are ready.")
