from fastapi import FastAPI, Body, status
from fastapi.responses import JSONResponse
import hashlib
import uuid
import uvicorn
import queue

from pip._internal.cli.cmdoptions import timeout

WORK_QUEUE = queue.Queue()
COMPLETED_QUEUE = queue.Queue()
MAX_NUM_OF_WORKERS = 0
NUM_OF_WORKERS = 0
MAX_TASK_TIME_TO_UPLOAD_WORKER = 15 #SEC

OTHER_NODE = None

app = FastAPI()

@app.get("/")
def read_root():
    return {"Welcome to Workers Controller"}


@app.put("/enqueue/{iterations}")
async def enqueue_work(iterations: int, buffer: str = Body(...)) -> JSONResponse:
    # Generate a unique ID for the work item
    work_id = str(uuid.uuid4())

    WORK_QUEUE.put({'work_id': work_id, 'iterations': iterations, 'buffer': buffer, "insert_time": datetime.now()})

    check_if_need_more_workers()

    # Return the ID of the submitted work item
    return JSONResponse(content={"work_id": work_id})


@app.post("/pullCompleted/{top}")
async def pull_completed_work(top: int) -> JSONResponse:
    completed_works = []

    while len(completed_works) < top and (not COMPLETED_QUEUE.empty() or try_approch_other_node("exists_completed_works")):
        if(not COMPLETED_QUEUE.empty()):
            completed_task = COMPLETED_QUEUE.get_nowait()
        else:
            completed_task = try_approch_other_node("get_completed_work_or_none")

        if completed_task is None:
            break

        completed_works.append(completed_task)

    # Return the completed work items
    return JSONResponse(content=completed_works)

def check_if_need_more_workers():
    if NUM_OF_WORKERS < 1:
        start_new_worker() ## TODO: IMPLEMENT
        NUM_OF_WORKERS += 1

    if NUM_OF_WORKERS < MAX_NUM_OF_WORKERS:
        if WORK_QUEUE.empty() and datetime.now() - WORK_QUEUE.queue[0]["insert_time"] > MAX_TASK_TIME_TO_UPLOAD_WORKER:
            start_new_worker()  ## TODO: IMPLEMENT
            NUM_OF_WORKERS += 1
    else:
        if try_approch_other_node("try_get_node_quota"):
            MAX_NUM_OF_WORKERS += 1


@app.post("/add_sibiling/{other_node}")
async def add_sibiling(other_node: str):
    OTHER_NODE = other_node


@app.post("/worker_down")
async def worker_down():
    NUM_OF_WORKERS -= 1

@app.get("/try_get_node_quota")
def try_get_node_quota():
    if NUM_OF_WORKERS < MAX_NUM_OF_WORKERS:
        MAX_NUM_OF_WORKERS -= 1
        return True
    return False

@app.post("/add_complteted_work")
async def add_complteted_work(work_id: str = Body(...), result: str = Body(...)):
    COMPLETED_QUEUE.put({'work_id': work_id, 'result': result})

@app.get("/exists_completed_works")
async def exists_completed_works():
    response = status.HTTP_500_INTERNAL_SERVER_ERROR

    if not COMPLETED_QUEUE.empty():
        response = status.HTTP_200_OK

    return response


@app.get("/get_completed_worke_or_none")
async def get_completed_work_or_none():
    result = None

    if not COMPLETED_QUEUE.empty():
        result = COMPLETED_QUEUE.get()

    return result

@app.get("/get_task")
def get_task():
    result = None

    if not WORK_QUEUE.empty():
        result = WORK_QUEUE.get()

    return result

def try_approch_other_node(endpoint: str):
    if OTHER_NODE is not None :
        response = requests.get(f"http://{OTHER_NODE}/{endpoint}", timeout=5)
        return response.status_code == 200
    return False

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)