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