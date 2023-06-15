#!/bin/bash
# Clone your application from Git
cd /home/ubuntu
git clone https://github.com/YonathanRon/cloud_computing_hw2.git

sudo apt-get update -y
sudo apt-get upgrade -y

# Update system packages
sudo apt install python3-pip -y
pip3 install --upgrade pip

# Install necessary packages
pip3 install fastapi
pip3 install requests
pip3 install uvicorn
pip3 install boto3


## Change to your application directory
cd cloud_computing_hw2
#
source nodes_ips.sh

## Start the FastAPI server
python3 worker.py


