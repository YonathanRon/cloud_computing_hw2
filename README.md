# Project Readme: Scalable Task Manager
### Overview
This project presents a scalable task manager designed to balance and distribute tasks across a cluster of workers. It uses FastAPI to manage task distribution, completion status, and worker scaling based on demand. The application utilizes two identical servers on separate AWS EC2 instances.

### Configuration
Before running the application, make sure you have your AWS credentials configured as environment variables. These include:

* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_DEFAULT_REGION

You may set them up using the following commands:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=your_region
```

Also, the maximum number of workers that a server can manage is specified by the MAX_NUM_OF_WORKERS environment variable. The default value is 5. This limit can be adjusted based on system resources and the nature of the tasks.


Ensure you have the necessary dependencies installed. If not, install them with:

```bash
./init_setup.sh
```
Then, you can run the application with the command:

```bash
python3 run_program.py
```
This script will do the following:

1. Create an IAM role and policy for EC2 management.
2. Create two EC2 instances.
3. Retrieve and print the public IP addresses of the instances.
4. Wait for the servers to be ready (sleeps for 2 minutes).
5. Check the health of the servers.
6. Perform post-startup actions (set max workers, etc.).


When running the script, you'll see output like this:

```bash
Creating instance 1..
Creating instance 2..
######################################################################
2 EC2 instance were created with IP 1 [xx.xx.xx.xx] 2 [yy.yy.yy.yy]
######################################################################
Waiting for servers to be up and ready.....
Our EC2 instances are ready :-)
Where xx.xx.xx.xx and yy.yy.yy.yy are the public IP addresses of your EC2 instances.
```

## Important Note
Please ensure that you have the necessary permissions to create and manage EC2 instances and IAM roles in your AWS account.

## NODES SERVERS - API Endpoints
This application provides several API endpoints for managing tasks and workers. Below is the list of available endpoints:

#### PUT /enqueue?iterations=num
This endpoint is used to submit a task to the server. The body of the request should contain the data for the task. The response will be the ID of the task, which can be used later to check the status of the task.

#### POST /pullCompleted?top=num
This endpoint is used to retrieve the most recently completed tasks. The top query parameter specifies the maximum number of tasks to retrieve. The response will be a list of the completed tasks, including their final results and IDs.

#### POST /worker_down/{instance_id}
Workers use this endpoint to notify the server when they have terminated. The body of the request should include the ID of the worker.

#### GET /try_get_node_quota
This endpoint allows the server to ask the other server for additional workers if it has reached its maximum worker limit but still has tasks in the queue.


## Auto scaling in our project:
In this WorkerController, auto-scaling is achieved through a set of rules defined in the check_if_need_more_workers method, 
which is invoked every time a new task is enqueued. 
The number of workers that can be created is limited by the MAX_NUM_OF_WORKERS (default to 5 if not provided).

The auto-scaling logic operates as follows:

1. If there are no active workers and the limit of maximum workers (MAX_NUM_OF_WORKERS) is not reached, a new worker is created and added to the active_workers list.

2. If the number of tasks in the work_queue is less than or equal to the number of active_workers, no action is taken, indicating there are sufficient workers to handle the current tasks.

3. If the number of active_workers is less than MAX_NUM_OF_WORKERS and there is a task in the work_queue that has been waiting for more than 15 seconds, a new worker is created and added to the active_workers list.

4. If the active_workers count has reached MAX_NUM_OF_WORKERS and there are tasks in the work_queue, the server tries to borrow a worker quota from the other server (other_node_ip) by invoking try_get_node_quota_from_other_node method. If successful, MAX_NUM_OF_WORKERS is increased by 1 and a new worker is created and added to the active_workers list.

Auto-scaling in this context is essentially creating more worker instances when the demand 
(number of tasks in the queue) exceeds the current worker count, 
while also ensuring the count of workers does not exceed a specified maximum limit. 
If that limit is reached, it can potentially be increased by borrowing a worker quota from another node, providing an additional layer of flexibility and scalability to the system.

In the case where a worker is terminated (worker_down endpoint), 
the corresponding worker is removed from the active_workers list, 
allowing new workers to be created when needed.

The overall design ensures the worker nodes scale automatically based on the demand 
(number of tasks in queue), maximizing the system's responsiveness and efficiency.