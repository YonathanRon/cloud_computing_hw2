import time

import boto3
import json
from botocore.exceptions import ClientError

POLICY_DOCUMENT = json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ec2:RunInstances",
                "ec2:DescribeKeyPairs",
                "ec2:DescribeKeyPair",
                "ec2:DescribeSecurityGroups",
                "ec2:CreateSecurityGroup",
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:RevokeSecurityGroupIngress"
            ],
            "Resource": "*"
        }
    ]
})

ROLE_POLICY_DOCUMENT = json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
})

class IAMRoleManager:

    def __init__(self, role_name, policy_name, policy_document=None):
        if policy_document is None:
            policy_document = ROLE_POLICY_DOCUMENT
        self.iam = boto3.client('iam')
        self.role_name = role_name
        self.policy_name = policy_name
        self.policy_document = policy_document

    def create_role(self):
        # Check if role exists
        try:
            get_role_response = self.iam.get_role(RoleName=self.role_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # Role does not exist, so create it
                try:
                    create_role_response = self.iam.create_role(
                        RoleName=self.role_name,
                        AssumeRolePolicyDocument=self.policy_document,
                        Description='Role to allow EC2 instances to manage other EC2 instances'
                    )
                    time.sleep(20)
                    print(f'Created role {self.role_name} response is  {create_role_response}')
                except ClientError as e:
                    print("Unexpected error: %s" % e)
        else:
            print(f"Role {self.role_name} already exists")

    def create_policy(self):
        # Check if policy exists
        try:
            get_policy_response = self.iam.get_policy(
                PolicyArn=f'arn:aws:iam::{self.iam.get_user()["User"]["Arn"].split(":")[4]}:policy/{self.policy_name}')
            print(f"get policy response is {get_policy_response}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                # Policy does not exist, so create it
                try:
                    create_policy_response = self.iam.create_policy(
                        PolicyName=self.policy_name,
                        PolicyDocument=POLICY_DOCUMENT
                    )
                    time.sleep(20)
                    print(f'Created policy {self.policy_name} response is {create_policy_response} ')
                except ClientError as e:
                    print("Unexpected error: %s" % e)
            else:
                print(f"Policy {self.policy_name} already exists")

    def attach_policy_to_role(self):
        # Attach policy to the role
        try:
            attach_role_policy_response = self.iam.attach_role_policy(
                RoleName=self.role_name,
                PolicyArn=f'arn:aws:iam::{self.iam.get_user()["User"]["Arn"].split(":")[4]}:policy/{self.policy_name}'
            )
            time.sleep(15)
            print(f'Attached policy {self.policy_name} to role {self.role_name}  response is {attach_role_policy_response}')
        except ClientError as e:
            print("Unexpected error: %s" % e)

    def get_or_create_instance_profile(self):
        instance_profile_name = self.role_name + "MyInstanceProfile"
        try:
            self.iam.get_instance_profile(InstanceProfileName=instance_profile_name)
        except self.iam.exceptions.NoSuchEntityException:
            # Create the instance profile since it does not exist
            self.iam.create_instance_profile(InstanceProfileName=instance_profile_name)
            # Add the role to the instance profile
            self.iam.add_role_to_instance_profile(InstanceProfileName=instance_profile_name, RoleName=self.role_name)
            time.sleep(10) # Give AWS some time to propagate the changes
            print(f"get intance profile for name {instance_profile_name}, response is {self.iam.get_instance_profile(InstanceProfileName=instance_profile_name)}")
        return instance_profile_name