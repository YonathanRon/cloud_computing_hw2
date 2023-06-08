import hashlib
import time
import redis

SLEEP_TIME = 3

TASKS_QUEUE = 'work_tasks'
COMPLETED_TASKS_QUEUE = 'completed_tasks'


def do_work(buffer, iterations):
    output = hashlib.sha512(buffer).digest()
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
    return output


# get redis cerdentials from config sys package
# Initialize Redis connection
redis_credentials = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': 'your_password',
    'decode_responses': True
}

# Inialize redis connection from queue cerdentials => redis_connection
redis_connection = redis.Redis(**redis_credentials)

while True:

    # Dequeue work task from the working queue from redis connection
    work_unit = redis_connection.lpop(TASKS_QUEUE)

    if work_unit is not None and work_unit['status'] == 'pending':
        result = do_work(work_unit['buffer'], work_unit['iterations'])
        print(f"result is: {result}")

        # push result into completed queue.
        # Enequeue work completed task to the completed task.
        redis_connection.rpush(COMPLETED_TASKS_QUEUE, {'work_id': work_unit['work_id'], 'result': result})

    else:
        time.sleep(SLEEP_TIME)




