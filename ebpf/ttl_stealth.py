#!/usr/bin/env python3
"""
Project Eidolon — eBPF Network Stealth
Makes each honeypot container appear as a different
physical machine by manipulating TTL values per container
"""

import subprocess
import os
import time
import json
from datetime import datetime

# TTL values for different OS fingerprints
TTL_PROFILES = [
    64,   # Linux
    128,  # Windows
    255,  # Cisco/Network device
    60,   # macOS older
    64,   # Linux (repeated for variety)
    128,  # Windows Server
    255,  # FreeBSD
    64,   # Ubuntu
    128,  # Windows 10
    255,  # Router
]

def get_container_interfaces():
    """Get all veth interfaces connected to honeypot containers"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=eidolon-stack_web-farm-decoy",
             "--format", "{{.ID}}"],
            capture_output=True, text=True
        )
        container_ids = result.stdout.strip().split('\n')
        container_ids = [c for c in container_ids if c]

        interfaces = []
        for i, cid in enumerate(container_ids):
            try:
                # Get the veth interface for this container
                result = subprocess.run(
                    ["docker", "inspect", cid,
                     "--format", "{{.State.Pid}}"],
                    capture_output=True, text=True
                )
                pid = result.stdout.strip()
                if pid and pid != "0":
                    interfaces.append({
                        "container_id": cid[:12],
                        "pid": pid,
                        "ttl": TTL_PROFILES[i % len(TTL_PROFILES)],
                        "index": i
                    })
            except Exception as e:
                print(f"[WARN] Could not get interface for {cid[:12]}: {e}")

        return interfaces
    except Exception as e:
        print(f"[ERROR] {e}")
        return []

def apply_ttl_to_container(container_info):
    """Apply unique TTL to a container using nsenter"""
    pid = container_info["pid"]
    ttl = container_info["ttl"]
    cid = container_info["container_id"]

    try:
        # Set TTL inside container network namespace
        cmd = [
            "sudo", "nsenter", "-t", pid, "-n",
            "sysctl", "-w", f"net.ipv4.ip_default_ttl={ttl}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[eBPF] Container {cid} → TTL={ttl} applied ✅")
            return True
        else:
            print(f"[eBPF] Container {cid} → TTL={ttl} failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] Container {cid}: {e}")
        return False

def apply_mac_randomization(container_info):
    """Give each container a unique MAC address"""
    pid = container_info["pid"]
    cid = container_info["container_id"]
    idx = container_info["index"]

    try:
        # Generate unique MAC based on container index
        mac = f"02:00:00:00:{idx//256:02x}:{idx%256:02x}"

        cmd = [
            "sudo", "nsenter", "-t", pid, "-n",
            "ip", "link", "set", "eth0", "address", mac
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[eBPF] Container {cid} → MAC={mac} applied ✅")
            return True
        else:
            print(f"[eBPF] Container {cid} → MAC failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] MAC for {cid}: {e}")
        return False

def main():
    print("=" * 55)
    print("  Project Eidolon — eBPF Network Stealth Engine")
    print("=" * 55)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting stealth application...")

    # Get all container interfaces
    print("\n[eBPF] Discovering honeypot containers...")
    containers = get_container_interfaces()
    print(f"[eBPF] Found {len(containers)} containers\n")

    if not containers:
        print("[ERROR] No containers found! Is the swarm running?")
        return

    # Apply TTL and MAC to each container
    ttl_success = 0
    mac_success = 0

    for container in containers:
        if apply_ttl_to_container(container):
            ttl_success += 1
        if apply_mac_randomization(container):
            mac_success += 1

    print(f"\n[eBPF] Results:")
    print(f"  TTL applied : {ttl_success}/{len(containers)} containers")
    print(f"  MAC applied : {mac_success}/{len(containers)} containers")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "containers_processed": len(containers),
        "ttl_success": ttl_success,
        "mac_success": mac_success,
        "profiles": [
            {
                "container": c["container_id"],
                "ttl": c["ttl"],
                "pid": c["pid"]
            }
            for c in containers
        ]
    }

    with open("/home/arpit/eidolon-swarm/ebpf/stealth_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[eBPF] Report saved to ebpf/stealth_report.json")
    print(f"[eBPF] Network stealth active — containers look like different machines!")
    print("=" * 55)

if __name__ == "__main__":
    main()
