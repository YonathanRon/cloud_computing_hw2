import os
from typing import List

from ec2_manager import EC2Manager


class WorkerCreator:
    DEFAULT_REGION = 'eu-west-1'

    def __init__(self):
        self.ec2_manager = EC2Manager(region=self.DEFAULT_REGION)

    def start_new_worker(self, main_ip, secondary_ip):
        setup_file = 'worker_setup.sh'
        self._update_worker_setup_script(main_ip, secondary_ip)
        instance = self.ec2_manager.create_ec2_instance(setup_file=setup_file)
        print("New worker instance has been created, waiting for it to be ready")
        instance.wait_until_running()
        print("Worker is ready!")
        return instance.id

    def terminate(self, instance_id):
        print(f"Going to terminate instance {instance_id}")
        self.ec2_manager.terminate_ec2_instance(instance_id)

    def _update_worker_setup_script(self,  main_ip, secondary_ip):
        bash_content = f'''
        #!/bin/bash
        export MAIN_INSTANCE_IP="{main_ip}"
        export SECONDARY_INSTANCE_IP="{secondary_ip}"
        '''

        with open("nodes_ips.sh", 'w') as file:
            file.write(bash_content)
            file.flush()

        print('Bash file updated successfully.')
