#!/bin/bash
set -e

# === CONFIG ===
USER="administrator"
HOME_DIR="/home/$USER"
REPO_URL="https://github.com/dismalict/sfVisionETL.git"
REPO_DIR="$HOME_DIR/sfVisionETL"
TARGET_DIR="$HOME_DIR/etl_scripts"
SERVICE_NAME="etlService.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
LOG_FILE="/var/log/etlService.log"

echo "=== Updating and installing dependencies ==="
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y git python3 python3-pip mysql-client python3-mysql.connector

# === Clone or update repo ===
if [ -d "$REPO_DIR/.git" ]; then
    echo "=== Repo exists, pulling latest changes ==="
    cd $REPO_DIR
    git reset --hard
    git pull origin main || git pull origin master
else
    echo "=== Cloning fresh repo ==="
    git clone $REPO_URL $REPO_DIR
fi

# === Copy ETL files to deployment dir ===
echo "=== Copying ETL files to $TARGET_DIR ==="
sudo mkdir -p $TARGET_DIR
sudo cp -r $REPO_DIR/backEnd/* $TARGET_DIR/
sudo cp $REPO_DIR/visionETL.py $TARGET_DIR/
sudo chown -R $USER:$USER $TARGET_DIR

# === Log file setup ===
echo "=== Creating log file $LOG_FILE ==="
sudo touch $LOG_FILE
sudo chown $USER:$USER $LOG_FILE

# === Service setup ===
echo "=== Deploying systemd service ==="
sudo cp $REPO_DIR/backEnd/$SERVICE_NAME $SERVICE_PATH
sudo systemctl daemon-reexec
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "=== Deployment complete ==="
echo "Check service:   sudo systemctl status $SERVICE_NAME"
echo "View logs:       tail -f $LOG_FILE"
