import os.path

import boto3


class EC2Manager:
    IMAGE_ID = 'ami-00aa9d3df94c6c354'
    INSTANCE_TYPE = 't2.micro'
    KEY_NAME = 'WorkerManagerNode'
    SECURITY_GROUP_NAME = 'HW2_sg'

    def __init__(self, role_name = ''):
        self.ec2_client = boto3.client('ec2')
        self.ec2_resource = boto3.resource('ec2')
        self.role_name = role_name
        self.security_group_id = None
        self.key_pair_exists = None

    def get_or_create_security_group(self):
        if self.security_group_id:
            print("security_group_id already exist here {}".format(self.security_group_id))
            return self.security_group_id
        try:
            response = self.ec2_client.describe_security_groups(GroupNames=[self.SECURITY_GROUP_NAME])
            security_group_id = response['SecurityGroups'][0]['GroupId']
            print(f"Security group {self.SECURITY_GROUP_NAME} already exists with ID {security_group_id}")

        except self.ec2_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
                print(f"Creating security group {self.SECURITY_GROUP_NAME}...")
                response = self.ec2_client.create_security_group(
                    GroupName=self.SECURITY_GROUP_NAME,
                    Description='Security group for HW2 workers balancing project'
                )
                security_group_id = response['GroupId']
                print(f"Security group {self.SECURITY_GROUP_NAME} created with ID {security_group_id}")
            else:
                raise e
        self.security_group_id = security_group_id
        return security_group_id

    def get_user_data(self, setup_file):
        if setup_file and os.path.exists(setup_file):
            try:
                with open(setup_file, 'r') as f:
                    user_data = f.read()
            except Exception as ex:
                print(f'Failed to load setup file {setup_file} {ex}')
                user_data = None
            return user_data

    def check_or_create_key(self):
        if self.key_pair_exists:
            return self.key_pair_exists
        try:
            existing_key_pairs = \
                self.ec2_client.describe_key_pairs(Filters=[{'Name': 'key-name', 'Values': [self.KEY_NAME]}])[
                    'KeyPairs']
            if len(existing_key_pairs) > 0:
                # The key pair already exists, so just use it
                key_name = existing_key_pairs[0]['KeyName']
            else:
                key_pair_response = self.ec2_client.create_key_pair(KeyName=self.KEY_NAME)
                key_name = key_pair_response['KeyName']
        except self.ec2_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
                print(f'Going to create key name - {self.KEY_NAME}')
                # The key pair doesn't exist yet, so create a new one
                key_pair_response = self.ec2_client.create_key_pair(KeyName=self.KEY_NAME)
                key_name = key_pair_response['KeyName']
            else:
                raise e
        self.key_pair_exists = key_name
        return key_name

    def create_ec2_instance(self, setup_file=''):
        # make sure the security group and key pair exist
        if not self.security_group_id:
            self.get_or_create_security_group()
        if not self.key_pair_exists:
            self.check_or_create_key()
        user_data = self.get_user_data(setup_file) if setup_file else ''
        instance = None
        try:
            print("Creating ec2 instance with IMAGE ID {} INSTANCE TYPE {}".format(self.IMAGE_ID, self.INSTANCE_TYPE))
            instance = self.ec2_resource.create_instances(
                ImageId=self.IMAGE_ID,
                InstanceType=self.INSTANCE_TYPE,
                KeyName=self.check_or_create_key(),
                MinCount=1,
                MaxCount=1,
                IamInstanceProfile={
                    'Name': self.role_name
                },
                SecurityGroupIds=[self.get_or_create_security_group()],
                UserData=user_data
            )
        except Exception as ex:
            print("Cought error when trying to run instance {}".format(ex))
        instance = instance[0]
        return instance

    def adjust_security_inbound(self):
        security_group_id = self.get_or_create_security_group()
        desired_ports = [8001, 22]
        try:
            response = self.ec2_client.describe_security_groups(GroupIds=[security_group_id])
            existing_rules = response['SecurityGroups'][0]['IpPermissions']
            for port in desired_ports:
                if any([rule['IpProtocol'] == 'tcp' and rule['FromPort'] == port and rule['ToPort'] == port and \
                        {'CidrIp': '0.0.0.0/0'} in rule['IpRanges'] for rule in existing_rules]):
                    print(f"Inbound rule for port {port} already exists.")
                    continue
                else:
                    print(f"Inbound rule for port {port} not exists, going to add it")
                    # add inbound rule to security group
                    response = self.ec2_client.authorize_security_group_ingress(
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

    def get_public_ip(self, instance):
        instance.wait_until_running()
        instance.reload()
        return instance.public_ip_address
