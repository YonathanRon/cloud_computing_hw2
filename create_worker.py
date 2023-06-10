import os
from typing import List

from ec2_manager import EC2Manager

DEFAULT_REGION = 'eu-west-1'


def start_new_worker(main_ip, secondary_ip):
    setup_file = 'worker_setup.sh'
    ec2_manager = EC2Manager(region=DEFAULT_REGION)
    env_vars = {"MAIN_INSTANCE_IP": main_ip, "SECONDARY_INSTANCE_IP": secondary_ip}
    _update_worker_setup_script(setup_file, env_vars)
    instance = ec2_manager.create_ec2_instance(setup_file=setup_file)
    print(f"New worker instance has born, waiting for it to be ready")
    instance.wait_until_running()
    print(f"Worker is ready!!!!")


def _update_worker_setup_script(setup_script, env_variables):
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
