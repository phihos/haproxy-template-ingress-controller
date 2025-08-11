import sys
import os
import atexit
import signal
import coverage

# Initialize coverage with explicit data file location
data_file = "/app/.coverage"
cov = coverage.Coverage(source=["haproxy_template_ic"], data_file=data_file)
cov.start()


# Ensure coverage is saved on exit
def save_coverage():
    try:
        print(f"Saving coverage data to {data_file}", file=sys.stderr)
        cov.stop()
        cov.save()
        print("Coverage data saved successfully", file=sys.stderr)
    except Exception as e:
        print(f"Failed to save coverage: {e}", file=sys.stderr)


atexit.register(save_coverage)


# Handle signals gracefully
def signal_handler(signum, frame):
    print(f"Received signal {signum}, saving coverage and exiting", file=sys.stderr)
    save_coverage()
    sys.exit(0)


def save_signal_handler(signum, frame):
    print(f"Received signal {signum}, saving coverage but continuing", file=sys.stderr)
    save_coverage()


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGUSR1, save_signal_handler)

# Import and run the main module
os.chdir("/app")
sys.path.insert(0, "/app/lib/python3.13/site-packages")
from haproxy_template_ic.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
