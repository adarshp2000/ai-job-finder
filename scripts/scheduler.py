import time
import subprocess

CRAWL_INTERVAL = 300  

def run_command(cmd):
    print(f"\nRunning: {cmd}")
    subprocess.run(cmd, shell=True)


def main():
    print("Job Finder Scheduler started")

    while True:
        try:
            print("\n--- Running crawler ---")
            run_command("python -m scripts.crawl_and_store")

            print("\n--- Checking for matches ---")
            run_command("python -m scripts.alert_new_matches")

        except Exception as e:
            print("Scheduler error:", e)

        print(f"\nSleeping for {CRAWL_INTERVAL} seconds...\n")
        time.sleep(CRAWL_INTERVAL)


if __name__ == "__main__":
    main()