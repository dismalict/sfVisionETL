import os
import sys
import json
import time
import mysql.connector

# Resolve config file path relative to script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "db_config.json")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def get_connection(config, db_key):
    db = config["databases"][db_key]
    return mysql.connector.connect(
        host=db["host"],
        user=db["user"],
        password=db["password"],
        database=db["database"]
    )

def run_etl(config):
    try:
        # use sfmysql01 as source, sfmysql03 as destination
        src_conn = get_connection(config, "sfmysql01")
        src_cursor = src_conn.cursor(dictionary=True)

        dst_conn = get_connection(config, "sfmysql03")
        dst_cursor = dst_conn.cursor()

        hosts = [f"sfvis{str(i).zfill(2)}" for i in range(1, 16)]

        for host in hosts:
            # sfvispool
            src_cursor.execute(f"""
                SELECT *
                FROM sfvispool.{host.upper()}
                ORDER BY Timestamp DESC
                LIMIT 1
            """)
            pool_row = src_cursor.fetchone()

            # sfOrinMonitoring
            src_cursor.execute(f"""
                SELECT *
                FROM sfOrinMonitoring.{host}
                ORDER BY time DESC
                LIMIT 1
            """)
            orin_row = src_cursor.fetchone()

            if not pool_row or not orin_row:
                continue

            dst_cursor.execute("""
                INSERT INTO sf_aggregate.host_metrics_history
                (hostname, pool_timestamp, workstation, status, max_people, time_work,
                 orin_id, orin_time, uptime, CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, RAM, SWAP, EMC, GPU,
                 APE, NVDEC, NVJPG, NVJPG1, OFA, SE, VIC, Fan_pwmfan0, Temp_CPU, Temp_CV0,
                 Temp_CV1, Temp_CV2, Temp_GPU, Temp_SOC0, Temp_SOC1, Temp_SOC2, Temp_tj,
                 Power_CPU, Power_CV, Power_GPU, Power_SOC, Power_SYS5v, Power_VDDRQ,
                 Power_tj, Power_TOT, jetson_clocks, nvp_model, disk_available_gb,
                 ip_address, model, jetpack, l4t, nv_power_mode, serial_number, p_number,
                 module, distribution, release, cuda, cudnn, tensorrt, vpi, vulkan, opencv)
                VALUES (%s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s)
            """, (
                host,
                pool_row["Timestamp"], pool_row["WorkStation"], pool_row["Status"],
                pool_row["Max_People"], pool_row["Time_Work"],
                orin_row["id"], orin_row["time"], orin_row["uptime"],
                orin_row["CPU1"], orin_row["CPU2"], orin_row["CPU3"], orin_row["CPU4"],
                orin_row["CPU5"], orin_row["CPU6"], orin_row["RAM"], orin_row["SWAP"],
                orin_row["EMC"], orin_row["GPU"], orin_row["APE"], orin_row["NVDEC"],
                orin_row["NVJPG"], orin_row["NVJPG1"], orin_row["OFA"], orin_row["SE"],
                orin_row["VIC"], orin_row["Fan pwmfan0"], orin_row["Temp CPU"],
                orin_row["Temp CV0"], orin_row["Temp CV1"], orin_row["Temp CV2"],
                orin_row["Temp GPU"], orin_row["Temp SOC0"], orin_row["Temp SOC1"],
                orin_row["Temp SOC2"], orin_row["Temp tj"], orin_row["Power CPU"],
                orin_row["Power CV"], orin_row["Power GPU"], orin_row["Power SOC"],
                orin_row["Power SYS5v"], orin_row["Power VDDRQ"], orin_row["Power tj"],
                orin_row["Power TOT"], orin_row["jetson_clocks"], orin_row["nvp model"],
                orin_row["disk_available_gb"], orin_row["ip_address"], orin_row["model"],
                orin_row["jetpack"], orin_row["l4t"], orin_row["nv_power_mode"],
                orin_row["serial_number"], orin_row["p_number"], orin_row["module"],
                orin_row["distribution"], orin_row["release"], orin_row["cuda"],
                orin_row["cudnn"], orin_row["tensorrt"], orin_row["vpi"],
                orin_row["vulkan"], orin_row["opencv"]
            ))

        # prune older than 7 days
        dst_cursor.execute("""
            DELETE FROM sf_aggregate.host_metrics_history
            WHERE collected_at < NOW() - INTERVAL 7 DAY
        """)
        dst_conn.commit()

        src_cursor.close()
        src_conn.close()
        dst_cursor.close()
        dst_conn.close()
        print("ETL cycle complete (with pruning)", file=sys.stderr)

    except Exception as e:
        print(f"ETL error: {e}", file=sys.stderr)


if __name__ == "__main__":
    config = load_config()
    while True:
        run_etl(config)
        time.sleep(10)
