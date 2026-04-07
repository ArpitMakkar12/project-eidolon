import time
import socket
import json
import os
import re
import subprocess
from datetime import datetime, timezone

LOGSTASH_HOST = "172.17.0.1"
LOGSTASH_PORT = 5000
LOG_FILE = "/tmp/nginx_access.log"
HOSTNAME = open("/etc/hostname").read().strip()

def parse_nginx_log(line):
    pattern = r'(\S+) - (\S+) \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+) "([^"]*)" "([^"]*)"'
    match = re.match(pattern, line)
    if match:
        return {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "attacker_ip": match.group(1),
            "request": f"{match.group(4)} {match.group(5)} {match.group(6)}",
            "status": match.group(7),
            "user_agent": match.group(10),
            "target_node": HOSTNAME,
            "message": "Unauthorized Web Access",
            "severity": "critical"
        }
    return None

def ship_log(event):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((LOGSTASH_HOST, LOGSTASH_PORT))
            s.send((json.dumps(event) + "\n").encode())
    except:
        pass

# Wait for nginx to start
time.sleep(5)

# Use tail -f to follow the log file
proc = subprocess.Popen(
    ["tail", "-f", "-n", "0", LOG_FILE],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True
)

for line in proc.stdout:
    line = line.strip()
    if line:
        event = parse_nginx_log(line)
        if event:
            ship_log(event)
