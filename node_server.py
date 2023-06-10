import os
import uuid
import datetime
import requests
import queue

import uvicorn
from fastapi import FastAPI, Body, status
from fastapi.responses import JSONResponse


class WorkerController:
    MAX_NUM_OF_WORKERS = int(os.environ.get("MAX_NUM_OF_WORKERS", 5))
    MAX_TASK_TIME_TO_UPLOAD_WORKER = 15

    def __init__(self):
        self.work_queue = queue.Queue()
        self.completed_work = queue.Queue()
        self.active_workers = 0
        self.other_node_ip = None
        self.app = FastAPI()

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

        @self.app.post("/add_sibling/{other_node}")
        async def add_sibling(other_node: str):
            self.other_node_ip = other_node
            print(f"Adding sibling ip {other_node}")

        @self.app.post("/worker_down")
        async def worker_down():
            self.active_workers -= 1

        @self.app.get("/try_get_node_quota")
        def try_get_node_quota():
            return self.try_get_node_quota()

        @self.app.post("/add_completed_work")
        async def add_completed_work(work_id: str = Body(...), result: str = Body(...)):
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

    def enqueue_work(self, iterations, buffer):
        work_id = str(uuid.uuid4())

        self.work_queue.put(
            {'work_id': work_id, 'iterations': iterations, 'buffer': buffer, "insert_time": datetime.datetime.now()})

        self.check_if_need_more_workers()

        return JSONResponse(content={"work_id": work_id})

    def check_if_need_more_workers(self):
        if not self.active_workers:
            # start_new_worker() ## TODO: IMPLEMENT
            self.active_workers += 1
        # Check if we have work that is waiting more than 15 sec (MAX_TASK_TIME_TO_UPLOAD_WORKER)
        if not self.work_queue.empty() and \
                datetime.datetime.now() - self.work_queue.queue[0][
            "insert_time"] >= self.MAX_TASK_TIME_TO_UPLOAD_WORKER:
            # if this server has available resource, start use it
            if self.active_workers < self.MAX_NUM_OF_WORKERS:
                self.active_workers += 1
            # If this server has no available resource, ask from second server
            else:
                if self.try_approch_other_node("try_get_node_quota"):
                    self.MAX_NUM_OF_WORKERS += 1
            # start_new_worker()  ## TODO: IMPLEMENT

    # ...
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

    def try_approch_other_node(self, endpoint: str):
        if self.other_node_ip is not None:
            response = requests.get(f"http://{self.other_node_ip}/{endpoint}", timeout=5)
            return response.status_code == 200
        return False

    def exists_completed_works(self):
        response = status.HTTP_500_INTERNAL_SERVER_ERROR

        if not self.completed_work.empty():
            response = status.HTTP_200_OK

        return response

    def try_get_node_quota(self):
        if self.active_workers < self.MAX_NUM_OF_WORKERS:
            self.MAX_NUM_OF_WORKERS -= 1
            return True
        return False

    def pull_completed_work(self, top):
        completed_works = []

        while len(completed_works) < top and (
                not self.completed_work.empty() or self.try_approch_other_node("exists_completed_works")):
            if not self.completed_work.empty():
                completed_task = self.completed_work.get_nowait()
            else:
                completed_task = self.try_approch_other_node("get_completed_work_or_none")

            if completed_task is None:
                break

            completed_works.append(completed_task)

        # Return the completed work items
        return JSONResponse(content=completed_works)


if __name__ == "__main__":
    worker_controller = WorkerController()
    uvicorn.run(worker_controller.app, host="0.0.0.0", port=8001)
