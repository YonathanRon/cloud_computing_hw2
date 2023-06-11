import hashlib

import boto3
import requests
import os
from datetime import datetime, timedelta
import time
from fastapi import status


class Worker:
    SLEEP_TIME = 3
    MAX_TIME_BETWEEN_TASKS = timedelta(seconds=1200)
    SERVER_PORT = 8001

    def __init__(self):
        self.main_controller_node = str(os.environ.get("MAIN_INSTANCE_IP"))
        self.second_controller_node = str(os.environ.get("SECONDARY_INSTANCE_IP"))

    def start(self):
        last_task_time = datetime.now()
        task_nodes = self.get_task_nodes()

        while datetime.now() - last_task_time <= self.MAX_TIME_BETWEEN_TASKS:
            for node in task_nodes:
                task = self.get_task(node)  # Get task from the task node
                print(f"Took task: {task}")
                if task is not None:
                    print(f"do_work on : {task['buffer'], task['iterations']}")
                    result = self.do_work(task["buffer"], task["iterations"])
                    print(f"result : {result}")
                    self.add_completed_work(node, task["work_id"], result)
                    last_task_time = datetime.now()
                    continue

            time.sleep(self.SLEEP_TIME)

        self.terminated()

    def add_completed_work(self, node: str, work_id: str, result: str):
        try:
            url = f"http://{node}/add_complteted_work"
            data = {
                'work_id': work_id,
                'result': result
            }
            response = requests.post(url, json=data)
            if response.status_code == status.HTTP_200_OK:
                return response.json()
        except Exception as e:
            print(f"Failed to retrieve task from {node}. {e}")
        return None

    def get_task_nodes(self, ):
        nodes = [self.main_controller_node]
        if len(self.second_controller_node) > 0:
            nodes.append(self.second_controller_node)

        return nodes

    def get_task(self, node):
        try:
            response = requests.get(f"http://{node}/get_task", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Failed to retrieve task from {node}. error: {e}")
        return None

    def do_work(self, buffer: str, iterations: int):
        buffer = buffer.encode()  # Encode the buffer string before hashing
        output = hashlib.sha512(buffer).digest()
        for i in range(iterations - 1):
            output = hashlib.sha512(output).digest()
        return str(output)

    def terminated(self):
        # Notify the nodes about termination
        requests.post(f"http://{self.main_controller_node}/worker_down")

        # Terminate the EC2 instances
        ec2 = boto3.client("ec2", region_name="your_region")
        instance_ids = ["instance_id_1", "instance_id_2", ...]  # Replace with your instance IDs
        ec2.terminate_instances(InstanceIds=instance_ids)


if __name__ == "__main__":
    worker = Worker()
    worker.start()
