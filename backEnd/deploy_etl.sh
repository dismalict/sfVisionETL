#!/bin/bash
set -e

# Variables
USER="administrator"
HOME_DIR="/home/$USER"
TARGET_DIR="$HOME_DIR/etl_scripts"
SERVICE_NAME="etlService.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
LOG_FILE="/var/log/etlService.log"

echo "=== Updating and installing dependencies ==="
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip mysql-client

echo "=== Installing Python MySQL connector ==="
pip3 install --upgrade mysql-connector-python

echo "=== Copying ETL files to $TARGET_DIR ==="
sudo mkdir -p $TARGET_DIR
sudo cp -r ./backEnd/* $TARGET_DIR/
sudo cp visionETL.py $TARGET_DIR/
sudo chown -R $USER:$USER $TARGET_DIR

echo "=== Creating log file $LOG_FILE ==="
sudo touch $LOG_FILE
sudo chown $USER:$USER $LOG_FILE

echo "=== Deploying systemd service ==="
sudo cp ./backEnd/$SERVICE_NAME $SERVICE_PATH
sudo systemctl daemon-reexec
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "=== Deployment complete ==="
echo "Check status:    sudo systemctl status $SERVICE_NAME"
echo "Follow logs:     tail -f $LOG_FILE"
