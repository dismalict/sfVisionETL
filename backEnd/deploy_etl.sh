#!/bin/bash
set -e

# ----------------------------
# Configuration
# ----------------------------
USER_HOME="/home/Administrator"
SCRIPT_DIR="$USER_HOME/etl_scripts"
SCRIPT_NAME="visionETL.py"
CONFIG_PATH="$USER_HOME/Desktop/db_config.json"
SERVICE_NAME="etlService.service"

# ----------------------------
# 1. Update & install packages
# ----------------------------
echo "Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

echo "Installing Python3, pip, MySQL connector..."
sudo apt install -y python3 python3-pip mysql-client

# Install mysql-connector-python via pip
python3 -m pip install --upgrade pip
python3 -m pip install mysql-connector-python

# ----------------------------
# 2. Create directories
# ----------------------------
echo "Creating ETL directories..."
mkdir -p "$SCRIPT_DIR"

# ----------------------------
# 3. Copy ETL script
# ----------------------------
echo "Deploying ETL Python script..."
cat > "$SCRIPT_DIR/$SCRIPT_NAME" << 'EOF'
# ----------------------------
# Paste the full Python ETL script here
# Make sure it matches the final version we made with pruning and config file loading
# ----------------------------
EOF

chmod +x "$SCRIPT_DIR/$SCRIPT_NAME"
chown -R Administrator:Administrator "$SCRIPT_DIR"

# ----------------------------
# 4. Deploy config file
# ----------------------------
echo "Deploying DB config..."
cat > "$CONFIG_PATH" << 'EOF'
{
  "databases": {
    "sfmysql01": {
      "host": "sfmysql01.sf.local",
      "user": "etl_user",
      "password": "SuperSecretPassword",
      "database": null
    },
    "sfmysql02": {
      "host": "sfmysql02.sf.local",
      "user": "etl_user",
      "password": "AnotherPassword",
      "database": null
    },
    "sfmysql03": {
      "host": "sfmysql03.sf.local",
      "user": "etl_user",
      "password": "YetAnotherPassword",
      "database": "sf_aggregate"
    },
    "sfmysql04": {
      "host": "sfmysql04.sf.local",
      "user": "etl_user",
      "password": "DifferentPassword",
      "database": null
    }
  }
}
EOF

chmod 600 "$CONFIG_PATH"
chown Administrator:Administrator "$CONFIG_PATH"

# ----------------------------
# 5. Create systemd service
# ----------------------------
echo "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME > /dev/null << EOF
[Unit]
Description=ETL Host Metrics Collector
After=network.target mysql.service

[Service]
Type=simple
User=Administrator
Group=Administrator
ExecStart=/usr/bin/python3 $SCRIPT_DIR/$SCRIPT_NAME
WorkingDirectory=$SCRIPT_DIR
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

# ----------------------------
# 6. Enable & start service
# ----------------------------
echo "Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Deployment complete! Check logs with:"
echo "journalctl -u $SERVICE_NAME -f"
