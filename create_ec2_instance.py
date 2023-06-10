import boto3
import time

IMAGE_ID = 'ami-00aa9d3df94c6c354'
INSTANCE_TYPE = 't2.micro'
SETUP_FILE = 'setup.sh'
# Create an EC2 client

ec2_client = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')


# Get the default VPC ID
def get_security_group_id():
    sg_name = 'HW2_sg'

    try:
        response = ec2_client.describe_security_groups(GroupNames=[sg_name])
        security_group_id = response['SecurityGroups'][0]['GroupId']
        print(f"Security group {sg_name} already exists with ID {security_group_id}")

    except ec2_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
            print(f"Creating security group {sg_name}...")
            response = ec2_client.create_security_group(
                GroupName=sg_name,
                Description='Security group for HW2 workers balancing project'
            )
            security_group_id = response['GroupId']
            print(f"Security group {sg_name} created with ID {security_group_id}")
        else:
            raise e
    return security_group_id


def get_user_data(setup_file_path=SETUP_FILE):
    if setup_file_path:
        try:
            with open(setup_file_path, 'r') as f:
                user_data = f.read()
        except Exception as ex:
            print(f'Failed to load setup file {setup_file_path} {ex}')
            user_data = None
        return user_data


def create_key(key_name='WorkerManagerNode'):
    try:
        existing_key_pairs = ec2_client.describe_key_pairs(Filters=[{'Name': 'key-name', 'Values': [key_name]}])['KeyPairs']
        if len(existing_key_pairs) > 0:
            # The key pair already exists, so just use it
            key_name = existing_key_pairs[0]['KeyName']
        else:
            key_pair_response = ec2_client.create_key_pair(KeyName=key_name)
            key_name = key_pair_response['KeyName']
    except ec2_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
            print(f'Going to create key name - {key_name}')
            # The key pair doesn't exist yet, so create a new one
            key_pair_response = ec2_client.create_key_pair(KeyName=key_name)
            key_name = key_pair_response['KeyName']
        else:
            raise e
    return key_name


def create_e2c_instance():
    # Launch the new instance
    instance = None
    try:
        print("Creating ec2 instance with IMAGE ID {} INSTANCE TYPE {}".format(IMAGE_ID, INSTANCE_TYPE))
        instance = ec2_resource.create_instances(
            ImageId=IMAGE_ID,
            InstanceType=INSTANCE_TYPE,
            KeyName=create_key(),
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[get_security_group_id()],
            UserData=get_user_data()
        )
    except Exception as ex:
        print("Cought error when trying to run instance {}".format(ex))
    return instance[0]


def adjust_security_inbound():
    security_group_id = get_security_group_id()
    desired_ports = [8000, 22]
    try:
        response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
        existing_rules = response['SecurityGroups'][0]['IpPermissions']
        for port in desired_ports:
            if any([rule['IpProtocol'] == 'tcp' and rule['FromPort'] == port and rule['ToPort'] == port and \
                    {'CidrIp': '0.0.0.0/0'} in rule['IpRanges'] for rule in existing_rules]):
                print(f"Inbound rule for port {port} already exists.")
                continue
            else:
                print(f"Inbound rule for port {port} not exists, going to add it")
                # add inbound rule to security group
                response = ec2_client.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': port,
                            'ToPort': port,
                            'IpRanges': [
                                {
                                    'CidrIp': '0.0.0.0/0'
                                },
                            ]
                        },
                    ]
                )
                print(response)
    except Exception as ex:
        print("OUI! Something went wrong {}".format(ex))

def get_public_ip(instance):
    instance.wait_until_running()
    instance.reload()
    return instance.public_ip_address


def create_ec2_instance_full(name="node"):
    instance = create_e2c_instance()
    adjust_security_inbound()
    instance.wait_until_running()
    instance.reload()
    print(instance.public_ip_address)

    # instance_id = create_response['Instances'][0]['InstanceId']


# Print the ID of the new instance
# print(f'Created instance with ID: {instance_id}')

# Wait for the instance to be ready to use
# print("Waiting for the instance to be ready...")
# time.sleep(30)  # Wait for 30 seconds for the instance to fully initialize

# print(f"Instance {instance_id} is now ready to use.")
