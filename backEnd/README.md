

# sfVisionETL

ETL pipeline for aggregating **SFVIS host metrics** from multiple MySQL databases into a centralized historical database for monitoring, analysis, and visualization.  

The pipeline collects the **latest row every 10 seconds** from:  
- `sfvispool.SFVIS01-15`  
- `sfOrinMonitoring.sfvis01-15`  

and stores the data into an **aggregated table** on `sfmysql03.sf.local`.  

It includes pruning logic to retain **1 week of data (~907k rows)**, making it graph-ready for long-term monitoring without overgrowth.

---

## 🚀 Features

- Collects workstation and monitoring metrics from 15 hosts (SFVIS01–SFVIS15)  
- Unified schema combining both `sfvispool` and `sfOrinMonitoring` tables  
- Historical storage with automatic pruning (keep 7 days of rows)  
- Config-driven: easily swap database credentials via JSON file  
- Runs continuously as a **systemd service** (auto-restarts on failure)  
- Deployment script for easy installation and updates  

---

## 📂 Repository Structure



sfVisionETL/
│
├── visionETL.py # Main ETL script (service entry point)
├── README.md # Project documentation
├── .gitattributes # Git attributes
│
└── backEnd/ # Backend + deployment resources
├── createdb.sql # (future) schema creation script
├── db_config.json # Config file for DB credentials
├── deploy_etl.sh # Deployment + installer script
└── etlService.service # Example systemd unit file


---

## ⚙️ Installation & Deployment

1. Clone the repo:  
   ```bash
   git clone https://github.com/<youruser>/sfVisionETL.git
   cd sfVisionETL


Run the deployment script:

chmod +x backEnd/deploy_etl.sh
./backEnd/deploy_etl.sh


This will:

Install dependencies (python3, pip, mysql-connector-python, git)

Copy visionETL.py to /home/administrator/etl_scripts/

Copy db_config.json to Desktop

Set up and enable the systemd service

Verify service status:

systemctl status etlService.service


Check logs in real time:

journalctl -u etlService.service -f

🛠 Configuration

All database connection info is stored in:

/home/administrator/Desktop/db_config.json

Example:

{
  "sfmysql01": {
    "host": "sfmysql01.sf.local",
    "user": "dbuser",
    "password": "dbpass",
    "database": "sfvispool"
  },
  "sfmysql03": {
    "host": "sfmysql03.sf.local",
    "user": "dbuser",
    "password": "dbpass",
    "database": "sfVisionAggregate"
  },
  "otherDB1": {
    "host": "otherdb.local",
    "user": "user",
    "password": "pass",
    "database": "somedb"
  },
  "otherDB2": {
    "host": "anotherdb.local",
    "user": "user",
    "password": "pass",
    "database": "anotherdb"
  }
}

📊 Data Retention

ETL runs every 10 seconds

Historical table prunes automatically to ~907,000 rows (≈ 7 days of data)

Designed for lightweight analytics & dashboards

🔧 Useful Commands

Restart service:

sudo systemctl restart etlService.service


Stop service:

sudo systemctl stop etlService.service


Force prune history manually (from MySQL):

DELETE FROM sfVisionAggregate.aggregated_host_metrics
ORDER BY timestamp ASC
LIMIT 1000;

📈 Future Plans

Optional Grafana/Prometheus integration for visual dashboards

Alerting hooks for downtime/abnormal metrics

Dockerized deployment for portability

👨‍💻 Author

Maintained by Mason Snyder