import os
from typing import List

from ec2_manager import EC2Manager


class workerCreator:
    DEFAULT_REGION = 'eu-west-1'

    def __init__(self):
        self.ec2_manager = EC2Manager(region=self.DEFAULT_REGION)

    def start_new_worker(self, main_ip, secondary_ip):
        setup_file = 'worker_setup.sh'
        env_vars = {"MAIN_INSTANCE_IP": main_ip, "SECONDARY_INSTANCE_IP": secondary_ip}
        self._update_worker_setup_script(setup_file, env_vars)
        instance = self.ec2_manager.create_ec2_instance(setup_file=setup_file)
        print("New worker instance has been created, waiting for it to be ready")
        instance.wait_until_running()
        print("Worker is ready!")
        return instance.id

    def terminate(self, instance_id):
        print(f"Going to terminate instance {instance_id}")
        self.ec2_manager.terminate_ec2_instance(instance_id)

    def _update_worker_setup_script(self, setup_script, env_variables):
        build_setup_file_path = setup_script
        # Read the existing build setup file
        with open(build_setup_file_path, 'r') as file:
            build_setup_content = file.read()

        # Append environment variable assignments to the content
        for variable, value in env_variables.items():
            build_setup_content += f'\nexport {variable}={value}'

        # Write the updated content back to the build setup file
        with open(build_setup_file_path, 'w') as file:
            file.write(build_setup_content)
            file.flush()

        for variable, value in env_variables.items():
            os.environ[variable] = value
