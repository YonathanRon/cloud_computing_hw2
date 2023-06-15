import os
import re
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
        # instance.wait_until_running()
        print("Worker is ready!")
        return instance.id

    def terminate(self, instance_id):
        print(f"Going to terminate instance {instance_id}")
        self.ec2_manager.terminate_ec2_instance(instance_id)

    def _update_worker_setup_script(self,  main_ip, secondary_ip):
        # Read the original script
        setup_file = 'worker_setup.sh'
        with open(setup_file, 'r') as file:
            script = file.read()

        # Perform the replacements
        script = re.sub(r'\{main_ip\}', main_ip, script)
        script = re.sub(r'\{secondary_ip\}', secondary_ip, script)

        # Write the new script to a new file
        with open(setup_file, 'w') as file:
            file.write(script)

        print('Bash file updated successfully.')

#
# if __name__ == '__main__':
#     wc = WorkerCreator()
#     wc._update_worker_setup_script('123', '1234')