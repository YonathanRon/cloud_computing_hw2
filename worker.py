import hashlib

import boto3
import requests
import os
from datetime import datetime, timedelta
import time
from fastapi import status

def get_instance_id():
    url = 'http://169.254.169.254/latest/meta-data/instance-id'
    response = requests.get(url)
    instance_id = response.text
    return instance_id


class Worker:
    SLEEP_TIME = 3
    MAX_TIME_BETWEEN_TASKS = timedelta(seconds=1200)
    SERVER_PORT = 8001

    def __init__(self):
        try:
            self.main_controller_node = str(os.environ.get("MAIN_INSTANCE_IP", ""))
            self.second_controller_node = str(os.environ.get("MAIN_INSTANCE_IP", ""))
        except Exception as ex:
            print(f"Failed to init nodes ips {ex}")

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
            url = f"http://{node}:{self.SERVER_PORT}/add_completed_work"
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

    def get_task_nodes(self):
        nodes = [self.main_controller_node]
        if self.second_controller_node :
            nodes.append(self.second_controller_node)

        return nodes

    def get_task(self, node):
        try:
            response = requests.get(f"http://{node}:{self.SERVER_PORT}/get_task", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Failed to retrieve task from {node}:{self.SERVER_PORT}. error: {e}")
        return None

    def do_work(self, buffer: str, iterations: int):
        buffer = buffer.encode()  # Encode the buffer string before hashing
        output = hashlib.sha512(buffer).digest()
        for i in range(iterations - 1):
            output = hashlib.sha512(output).digest()
        return str(output)

    def terminated(self):
        # Notify the nodes about termination
        data = {
            'instance_id': get_instance_id()
        }
        try:
            requests.post(f"http://{self.main_controller_node}:{self.SERVER_PORT}/worker_down", json=data)
        except Exception as ex:
            print(f"Oh, we failed {ex}")

if __name__ == "__main__":
    worker = Worker()
    worker.start()

