import time
from typing import List

import requests


def check_servers_health(ips: List[str], port: str) -> bool:
    def _check_health(ip):
        try:
            response = requests.get(f"http://{ip}:{port}/health")
            if response.status_code == 200:
                data = response.json()
                if 'status' in data and data['status'] == 'ok':
                    return True
            return False
        except requests.exceptions.RequestException as err:
            print(f"Error: {err}")
            return False

    start_time = time.time()
    timeout = 60 * 5  # 5 minutes
    all_ready = False
    while time.time() - start_time < timeout:
        all_ready = all(_check_health(ip) for ip in ips)
        if all_ready:
            print("All instances are ready.")
            break
        time.sleep(10)  # wait 10 seconds before trying again
    if not all_ready:
        print("Timeout exceeded and not all instances are ready.")
    return all_ready

def post_startup_actions(ips: List[str], port: str):
    try:
        request_template = lambda ip_to, ip1_about: f"http://{ip_to}:{port}/add_sibling/{ip1_about}"
        requests.put(request_template(ips[0], ips[1]))
        requests.put(request_template(ips[1], ips[0]))
        requests.put(f"http://{ips[0]}:{port}/max_workers/3")
        requests.put(f"http://{ips[1]}:{port}/max_workers/2")
    except Exception as ex:
        print("Caught exception {}".format(ex))
