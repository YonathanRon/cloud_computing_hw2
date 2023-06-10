import hashlib
import time
from datetime import datetime

SLEEP_TIME = 3
MAX_TIME_BETWEEN_TASKS = 120
MAIN_NODE = None
SECOND_NODE = None


def do_work(buffer, iterations):
    output = hashlib.sha512(buffer).digest()
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
    return output


last_task_time = datetime.now()
task_nodes = get_task_nodes()

while datetime.now() - last_task_time <= MAX_TIME_BETWEEN_TASKS:
    for node in task_nodes:
        task = get_task(node)  # Get task from the task node
        if(task is not None):
            result = do_work(task["buffer"], task["iterations"])
            add_completed_work(node, task["work_id"], result)
            last_task_time = datetime.now()
            continue

    time.sleep(SLEEP_TIME)

terminated()

def get_task_nodes():
    nodes = [MAIN_NODE]
    if SECOND_NODE is not None:
        nodes.append(SECOND_NODE)

    return nodes

def get_task(node):
    response = requests.get(f"http://{node}/get_task")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve task from {node}.")
        return None


def terminated():
    # Notify the nodes about termination
    requests.post(f"http://{MAIN_NODE}/worker_down")

    # Terminate the EC2 instances
    ec2 = boto3.client("ec2", region_name="your_region")
    instance_ids = ["instance_id_1", "instance_id_2", ...]  # Replace with your instance IDs
    ec2.terminate_instances(InstanceIds=instance_ids)






