import time
import sys
import os
import json
import logging
import traceback
from datetime import datetime
import io
from contextlib import redirect_stdout, redirect_stderr

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
# Map to DEV_ETL root
etl_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
python_dir = os.path.join(etl_root, "python")
modules_dir = os.path.join(python_dir, "modules")

# Add to sys.path
sys.path.insert(0, python_dir)
sys.path.insert(0, modules_dir)

# Import Database
import database

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("worker")

def process_job(job):
    job_id = job['id']
    params = json.loads(job['params'])
    sistemas = params.get('sistemas', [])
    
    logger.info(f"Processing Job #{job_id}: {sistemas}")
    database.update_job_status(job_id, 'running')
    database.append_log(job_id, f"Job started at {datetime.now()}")
    
    # Capture Output
    log_capture = io.StringIO()
    
    # Custom logger to write to both stdout and DB
    class StreamLogger:
        def write(self, message):
            if message.strip():
                print(message.strip()) # Console
                database.append_log(job_id, message.strip()) # DB
        def flush(self):
            pass

    sl = StreamLogger()
    
    try:
        # Load Credentials
        config_path = os.path.join(etl_root, "config", "credentials.json")
        with open(config_path, 'r') as f:
            credentials = json.load(f)

        # Execute Systems
        with redirect_stdout(sl), redirect_stderr(sl):
            for sistema in sistemas:
                print(f"=== Starting System: {sistema} ===")
                
                if sistema == 'maps':
                    from modules.maps_download_consolidado import run_maps_completo
                    creds = credentials["maps"]
                    paths = credentials["paths"]
                    
                    # Prepare arguments
                    data_inicial = params.get('data_inicial')
                    data_final = params.get('data_final')
                    
                    # Map params
                    # (Simplified for testing - logic from main.py adapted)
                    run_maps_completo(
                        creds["url"],
                        paths.get("maps", ""),
                        paths.get("pdf", ""),
                        paths.get("maps", ""),
                        creds["username"],
                        creds["password"],
                        data_inicial,
                        data_final,
                        True, True, True, True, [] # Default flags
                    )
                
                elif sistema == 'amplis': # or amplis_reag
                     print("Amplis implementation placeholder - direct import")
                     # from amplis_V02 import run_amplis
                     # ... implementation ...
                
                else:
                    print(f"System {sistema} not yet implemented in V2 Worker directly. Fallback needed?")
                    # Here we could implement other systems
                
                print(f"=== Finished System: {sistema} ===")
        
        database.update_job_status(job_id, 'completed')
        logger.info(f"Job #{job_id} Completed")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        database.update_job_status(job_id, 'error', error=str(e))
        database.append_log(job_id, error_msg)

def main():
    logger.info("Worker started. Waiting for jobs...")
    database.init_db()
    
    while True:
        try:
            job = database.get_pending_job()
            if job:
                process_job(job)
            else:
                time.sleep(2) # Wait before polling again
        except KeyboardInterrupt:
            logger.info("Worker stopped")
            break
        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
