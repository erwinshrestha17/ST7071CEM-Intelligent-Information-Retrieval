# scheduler.py

import schedule
import time
import subprocess


def run_script(script_name):
    """Helper function to run a python script and return its exit code."""
    print(f"--- Running {script_name} ---")
    try:
        # The `check=True` argument will raise CalledProcessError on non-zero exit codes.
        result = subprocess.run(["python", script_name], check=True, capture_output=True, text=True)
        print(f"--- Finished {script_name} successfully ---")
        return 0  # Success
    except subprocess.CalledProcessError as e:
        print(f"--- Error running {script_name}: {e} ---")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return e.returncode  # Failure


def update_job():
    """Defines the sequential job of crawling and then indexing."""
    print("Starting weekly update job...")

    # Run crawler and check if it was successful
    crawler_exit_code = run_script("crawler.py")

    if crawler_exit_code == 0:
        # Only run the indexer if the crawler succeeded
        run_script("indexer.py")
    else:
        print("Crawler failed. Skipping indexing to preserve the last good index.")

    print("Weekly update job finished.")

# Schedule the job to run every week on Monday at 3 AM
schedule.every().week.do(update_job)
# For testing, you can run it more frequently:
# schedule.every(1).minutes.do(update_job)

print("Scheduler started. Waiting for the scheduled time to run the job...")
# Initial run so you don't have to wait a week
update_job()

while True:
    schedule.run_pending()
    time.sleep(1)