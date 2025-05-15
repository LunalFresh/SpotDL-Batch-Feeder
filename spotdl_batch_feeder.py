import os
import subprocess
import time
import sys
import json
from pathlib import Path
import multiprocessing

# ====== CONFIGURATION ======
CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
INPUT_FILE = config.get("input_file", "spotdl_list.txt")
DOWNLOAD_DIR = config.get("download_dir", str(Path.home() / "Music" / "SpotDL-Downloads"))
THREAD_COUNT = config.get("thread_count", 3)
CHECK_INTERVAL = config.get("check_interval", 1)
SPOTDL_TIMEOUT = config.get("spotdl_timeout", 120)
COOKIES_FILE = config.get("cookies_file", "cookies.txt")
OUTPUT_TEMPLATE = os.path.join(DOWNLOAD_DIR, "{artist} - {title}")

# ====== CORE WORKER FUNCTION ======
def worker(
    tid, q, stop_event,
    processed_count, downloaded_count, skipped_count, failed_urls_list, lock
):
    while not stop_event.is_set():
        try:
            url = q.get_nowait()
        except Exception:
            break

        print(f"[Process {tid}] ⏳ Processing: {url}")
        cmd = [
            "spotdl", "download", url,
            "--threads", "1",
            "--max-retries", "10",
            "--output", OUTPUT_TEMPLATE,
            "--overwrite", "skip",
            "--scan-for-songs",
            "--log-level", "DEBUG",
            "--cookie-file", COOKIES_FILE
        ]
        print(f"[Process {tid}] ▶ Running: {' '.join(cmd)}")

        log_buffer = ""
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            start = time.time()

            while True:
                if stop_event.is_set():
                    proc.terminate()
                    break

                line = proc.stdout.readline()
                if line:
                    print(f"[Process {tid}] {line.rstrip()}")
                    log_buffer += line

                if proc.poll() is not None:
                    rest = proc.stdout.read()
                    if rest:
                        print(f"[Process {tid}] {rest.rstrip()}")
                        log_buffer += rest
                    break

                if time.time() - start > SPOTDL_TIMEOUT:
                    proc.kill()
                    print(f"[Process {tid}] ⏰ Timeout after {SPOTDL_TIMEOUT}s")
                    log_buffer += f"TIMEOUT after {SPOTDL_TIMEOUT}s\n"
                    break

            proc.wait()
            return_code = proc.returncode

        except Exception as e:
            log_buffer += f"EXCEPTION: {e}\n"
            return_code = -999

        with lock:
            with open("track_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"\n\n==== {url} ====\n")
                log_file.write(log_buffer)

        is_skipped    = ("Skipping" in log_buffer or "already exists" in log_buffer)
        is_downloaded = ("Downloaded" in log_buffer or (return_code == 0 and not is_skipped))
        is_failed     = not is_skipped and not is_downloaded

        with lock:
            processed_count.value += 1
            if is_skipped:
                skipped_count.value += 1
            elif is_downloaded:
                downloaded_count.value += 1
            else:
                failed_urls_list.append(url)

        if is_skipped:
            print(f"[Process {tid}] ⏭️ Skipped")
        elif is_downloaded:
            print(f"[Process {tid}] ✅ Downloaded")
        else:
            print(f"[Process {tid}] ❌ Failed")
            with lock:
                with open("failed_tracks.txt", "a", encoding="utf-8") as f:
                    f.write(url + "\n")

        time.sleep(CHECK_INTERVAL)

# ====== UTILS ======
def load_urls(q):
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if url.startswith("http"):
                q.put(url)

def print_summary(processed_count, downloaded_count, skipped_count, failed_urls_list):
    print("\n📊 Summary")
    print(f"  Processed:  {processed_count.value}")
    print(f"  Downloaded: {downloaded_count.value}")
    print(f"  Skipped:    {skipped_count.value}")
    print(f"  Failed:     {len(failed_urls_list)}")

def terminate_all_processes(processes):
    for p in processes:
        if p.is_alive():
            p.terminate()

# ====== MAIN EXECUTION ======
if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    open("failed_tracks.txt", "w").close()

    with multiprocessing.Manager() as manager:
        q = manager.Queue()
        stop_event = manager.Event()
        lock = manager.Lock()
        processed_count = manager.Value('i', 0)
        downloaded_count = manager.Value('i', 0)
        skipped_count = manager.Value('i', 0)
        failed_urls_list = manager.list()

        print("📦 Loading playlist URLs...")
        load_urls(q)

        try:
            processes = []
            for i in range(THREAD_COUNT):
                p = multiprocessing.Process(
                    target=worker,
                    args=(i+1, q, stop_event,
                          processed_count, downloaded_count, skipped_count, failed_urls_list, lock)
                )
                processes.append(p)
                p.start()
                time.sleep(1)

            for p in processes:
                p.join()

            print_summary(processed_count, downloaded_count, skipped_count, failed_urls_list)

            # Retry pass for failed URLs
            if not stop_event.is_set() and failed_urls_list:
                n = len(failed_urls_list)
                print(f"\n🔁 Retrying {n} failed track{'s' if n!=1 else ''}...\n")
                open("failed_tracks.txt", "w").close()

                retry_q = manager.Queue()
                for url in failed_urls_list:
                    retry_q.put(url)
                failed_urls_list[:] = []

                q = retry_q

                processes = []
                for i in range(THREAD_COUNT):
                    p = multiprocessing.Process(
                        target=worker,
                        args=(i+1, q, stop_event,
                              processed_count, downloaded_count, skipped_count, failed_urls_list, lock)
                    )
                    processes.append(p)
                    p.start()
                    time.sleep(1)

                for p in processes:
                    p.join()

                print_summary(processed_count, downloaded_count, skipped_count, failed_urls_list)

            print("\n🎉 Done — all tracks processed.")

        except KeyboardInterrupt:
            print("\n🛑 Ctrl+C received — stopping script immediately.")
            stop_event.set()
            terminate_all_processes(processes)
            sys.exit(0)
