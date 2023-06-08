from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
import hashlib
import uuid
import uvicorn
import redis

TASKS_QUEUE = 'work_tasks'
COMPLETED_TASKS_QUEUE = 'completed_tasks'

# Initialize Redis connection
redis_credentials = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': 'your_password',
    'decode_responses': True
}

app = FastAPI()

@app.get("/")
def read_root():
    return {"Welcome to Workers Controller"}


@app.put("/enqueue/{iterations}")
async def enqueue_work(iterations: int, buffer: str = Body(...)) -> JSONResponse:
    # Generate a unique ID for the work item
    work_id = str(uuid.uuid4())

    redis_connection = redis.Redis(**redis_credentials)
    redis_connection.rpush(TASKS_QUEUE, {'work_id': work_id, 'iterations': iterations, 'buffer': buffer, status: 'pending'})

    # Return the ID of the submitted work item
    return JSONResponse(content={"work_id": work_id})


@app.post("/pullCompleted/{top}")
async def pull_completed_work(top: int) -> JSONResponse:
    completed_works = []

    # Iterate over the work items in reverse order

    redis_connection = redis.Redis(**redis_credentials)

    while True:
        completed_task = redis_connection.lpop(COMPLETED_TASKS_QUEUE)
        if completed_task is None:
            break

        completed_works.append({'work_id': completed_task['work_id'],
                'result': completed_task['result']})

    # Return the completed work items
    return JSONResponse(content=completed_work)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)