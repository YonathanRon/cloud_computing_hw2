from fastapi import FastAPI, Body, status
from fastapi.responses import JSONResponse
import os
import hashlib
import uuid
import uvicorn
import queue
from datetime import datetime, timedelta
import requests
from create_worker import *

from pip._internal.cli.cmdoptions import timeout

from ec2_manager import EC2Manager
def get_public_ip():
    url = "http://checkip.amazonaws.com"
    response = requests.get(url)
    public_ip = response.text.strip()
    return public_ip


class WorkerController:
    MAX_NUM_OF_WORKERS = int(os.environ.get("MAX_NUM_OF_WORKERS", 5))
    MAX_TASK_TIME_TO_UPLOAD_WORKER = timedelta(seconds=15)  # Use timedelta for time comparison

    def __init__(self):
        self.work_queue = queue.Queue()
        self.completed_work = queue.Queue()
        self.active_workers = []
        self.my_ip = get_public_ip()
        self.other_node_ip = ""
        self.app = FastAPI()
        self.worker_creator = workerCreator()

        @self.app.get("/")
        def read_root():
            return {"Welcome to Workers Controller"}

        @self.app.put("/enqueue/{iterations}")
        async def enqueue_work(iterations: int, buffer: str = Body(...)) -> JSONResponse:
            return self.enqueue_work(iterations, buffer)

        @self.app.post("/pullCompleted/{top}")
        async def pull_completed_work(top: int) -> JSONResponse:
            return self.pull_completed_work(top)

        @self.app.get("/health")
        def read_health():
            return {"status": "ok"}

        @self.app.put("/add_sibling/{other_node}")
        async def add_sibling(other_node: str):
            return self.add_sibling(other_node)

        @self.app.post("/set_max_workers/{max_workers}")
        async def set_max_workers(max_workers: int):
            self.MAX_NUM_OF_WORKERS = max_workers

        @self.app.post("/worker_down/{instance_id}")
        async def worker_down(instance_id : str):
            self.terminate_worker(instance_id)
            self.active_workers.remove(instance_id)

        @self.app.get("/try_get_node_quota")
        async def try_get_node_quota():
            return self.try_get_node_quota()

        @self.app.post("/add_complteted_work")
        async def add_complteted_work(work_id: str = Body(...), result: str = Body(...)):
            self.completed_work.put({'work_id': work_id, 'result': result})

        @self.app.get("/exists_completed_works")
        async def exists_completed_works():
            return self.exists_completed_works()

        @self.app.get("/get_completed_work_or_none")
        async def get_completed_work_or_none():
            return self.get_completed_work_or_none()

        @self.app.get("/get_task")
        def get_task():
            return self.get_task()

    def add_sibling(self, other_node: str):
        self.other_node_ip = other_node
        print(f"Adding sibling ip {other_node}")
        return JSONResponse(content={}, status_code=status.HTTP_200_OK)

    def get_completed_work_or_none(self):
        result = None

        if not self.completed_work.empty():
            result = self.completed_work.get()

        return result

    def get_task(self):
        result = None

        if not self.work_queue.empty():
            result = self.work_queue.get()

        return result

    def exists_completed_works(self):
        content = False

        if not self.completed_work.empty():
            content = True

        return JSONResponse(content=content, status_code=status.HTTP_200_OK)

    def pull_completed_work(self, top: int) -> JSONResponse:
        completed_works = []

        while len(completed_works) < top and (
                not self.completed_work.empty() or self.exists_completed_works_from_other_node()):
            if not self.completed_work.empty():
                completed_task = self.completed_work.get_nowait()
                print(f"pulled completed task: {completed_task}")
            else:
                completed_task = self.get_completed_work_or_none_from_other_node()
                print(f"pulled completed task from other node: {completed_task}")

            if completed_task is None:
                break

            completed_works.append(completed_task)

        return JSONResponse(content=completed_works, status_code=status.HTTP_200_OK)

    def exists_completed_works_from_other_node(self):
        response = self.try_approach_other_node("exists_completed_works")
        return response is not None

    def check_if_need_more_workers(self):
        # No active workers. and I can have one!!! :-)
        if len(self.active_workers) < 1 and len(self.active_workers) < self.MAX_NUM_OF_WORKERS:
            instance_id = self.worker_creator.start_new_worker(self.my_ip, self.other_node_ip)
            self.active_workers.append(instance_id)
            print(f"Increase worker: {len(self.active_workers)}")
        # I have worker for my new job
        elif self.work_queue.qsize() <= len(self.active_workers):
            print(f"There are enough workers to handle the tasks")
            return

        elif len(self.active_workers) < self.MAX_NUM_OF_WORKERS:
            if not self.work_queue.empty() and \
                    datetime.now() - datetime.strptime(self.work_queue.queue[0]["insert_time"], "%Y-%m-%d %H:%M:%S.%f") \
                    >= self.MAX_TASK_TIME_TO_UPLOAD_WORKER:
                instance_id = self.worker_creator.start_new_worker(self.my_ip, self.other_node_ip)
                self.active_workers.append(instance_id)
                print(f"Increase worker: {self.active_workers}")
            else:
                print(f"not enough time since last increasing")
        else:
            print(f"not enough time since last increasing")
            # I need to do job, but I don't have resources
            if self.try_get_node_quota_from_other_node():
                self.MAX_NUM_OF_WORKERS += 1
                instance_id = self.worker_creator.start_new_worker(self.my_ip, self.other_node_ip)
                self.active_workers.append(instance_id)
                print(f"Take worker from different manager: {self.MAX_NUM_OF_WORKERS}")
            else:
                print(f"try_approach_other_node Did not succeeded ")

    def try_get_node_quota_from_other_node(self):
        response = self.try_approach_other_node("try_get_node_quota")

        return response is not None

    def terminate_worker(self, worker_id):
        self.worker_creator.terminate(worker_id)

    def enqueue_work(self, iterations: int, buffer: str) -> JSONResponse:
        # Generate a unique ID for the work item
        work_id = str(uuid.uuid4())

        self.work_queue.put(
            {'work_id': work_id, 'iterations': iterations, 'buffer': buffer, "insert_time": str(datetime.now())})

        self.check_if_need_more_workers()

        # Return the ID of the submitted work item
        return JSONResponse(content={"work_id": work_id})

    def try_get_node_quota(self):
        if len(self.active_workers) < self.MAX_NUM_OF_WORKERS:
            self.MAX_NUM_OF_WORKERS -= 1
            print(f"After giving one worker: MAX_NUM_OF_WORKERS: {self.MAX_NUM_OF_WORKERS}")
            return JSONResponse(content={}, status_code=status.HTTP_200_OK)
        return JSONResponse(content={}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_completed_work_or_none_from_other_node(self):
        return self.try_approach_other_node("get_completed_work_or_none")

    def try_approach_other_node(self, endpoint: str):
        try:
            if len(self.other_node_ip) > 0:
                print(f"http://{self.other_node_ip}/{endpoint}")
                response = requests.get(f"http://{self.other_node_ip}/{endpoint}", timeout=5)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Cant reach to other node {e}")
        return None


if __name__ == "__main__":
    ip = "0.0.0.0"
    port = 8001

    # Create the first WorkerController instance with the first IP address
    workerController = WorkerController()
    uvicorn.run(workerController.app, host=ip, port=port)
