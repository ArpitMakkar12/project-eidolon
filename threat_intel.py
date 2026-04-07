import urllib.request
import json
import time
import os

headers = {
	"Key": ABUSEIPDB_KEY,
	"Accept": "application/json"
}

ABUSEIPDB_KEY = os.getenv("ABUSEIPDB_KEY")
IPINFO_TOKEN  = os.getenv("IPINFO_TOKEN")

# Cache to avoid repeated API calls for same IP
_cache = {}

def get_ip_intel(ip):
    # Skip private/localhost IPs
    if ip.startswith("127.") or ip.startswith("10.") or \
       ip.startswith("172.") or ip.startswith("192.168."):
        return {
            "ip": ip,
            "country": "Internal Network",
            "country_flag": "🏠",
            "city": "localhost",
            "org": "Internal",
            "abuse_score": 0,
            "is_tor": False,
            "is_malicious": False,
            "threat_level": "LOW",
            "known_for": "Internal traffic"
        }

    # Return cached result if available
    if ip in _cache:
        return _cache[ip]

    result = {
        "ip": ip,
        "country": "Unknown",
        "country_flag": "🌐",
        "city": "Unknown",
        "org": "Unknown",
        "abuse_score": 0,
        "is_tor": False,
        "is_malicious": False,
        "threat_level": "LOW",
        "known_for": "Unknown"
    }

    # ── IPInfo geolocation ─────────────────────────────────────────
    try:
        url = f"https://ipinfo.io/{ip}?token={IPINFO_TOKEN}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            result["country"] = data.get("country", "Unknown")
            result["city"]    = data.get("city", "Unknown")
            result["org"]     = data.get("org", "Unknown")
            result["region"]  = data.get("region", "Unknown")

            # Add country flag emoji
            country = data.get("country", "")
            if len(country) == 2:
                flag = chr(ord(country[0]) + 127397) + \
                       chr(ord(country[1]) + 127397)
                result["country_flag"] = flag
    except Exception as e:
        print(f"[IPINFO ERROR] {e}")

    # ── AbuseIPDB threat intel ─────────────────────────────────────
    try:
        url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90&verbose"
        req = urllib.request.Request(url, headers={
            "Key": ABUSEIPDB_KEY,
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read()).get("data", {})
            score = data.get("abuseConfidenceScore", 0)
            result["abuse_score"]    = score
            result["is_tor"]         = data.get("isTor", False)
            result["total_reports"]  = data.get("totalReports", 0)
            result["last_reported"]  = data.get("lastReportedAt", "Never")
            result["isp"]            = data.get("isp", "Unknown")
            result["usage_type"]     = data.get("usageType", "Unknown")

            # Set threat level
            if score >= 80:
                result["threat_level"]  = "CRITICAL"
                result["is_malicious"]  = True
            elif score >= 50:
                result["threat_level"]  = "HIGH"
                result["is_malicious"]  = True
            elif score >= 20:
                result["threat_level"]  = "MEDIUM"
                result["is_malicious"]  = False
            else:
                result["threat_level"]  = "LOW"
                result["is_malicious"]  = False

            # Known for
            categories = data.get("reports", [])
            if categories:
                result["known_for"] = f"{len(categories)} reports in last 90 days"
            
            if result["is_tor"]:
                result["known_for"] += " | Tor Exit Node"

    except Exception as e:
        print(f"[ABUSEIPDB ERROR] {e}")

    # Cache result
    _cache[ip] = result
    return result

def format_intel_report(intel):
    flag   = intel.get("country_flag", "🌐")
    score  = intel.get("abuse_score", 0)
    level  = intel.get("threat_level", "LOW")
    tor    = "YES ⚠️" if intel.get("is_tor") else "No"

    threat_emoji = {
        "CRITICAL": "🔴",
        "HIGH":     "🟠",
        "MEDIUM":   "🟡",
        "LOW":      "🟢"
    }.get(level, "🟢")

    return f"""
  IP Address   : {intel.get("ip")}
  Location     : {flag} {intel.get("city")}, {intel.get("country")}
  Organisation : {intel.get("org", intel.get("isp", "Unknown"))}
  Abuse Score  : {score}/100 {threat_emoji}
  Threat Level : {level}
  Tor Exit Node: {tor}
  Known For    : {intel.get("known_for", "No reports")}
  Reports      : {intel.get("total_reports", 0)} reports in last 90 days"""

if __name__ == "__main__":
    # Test with a known malicious IP
    print("Testing threat intelligence...")
    print("\nTest 1 — Known malicious IP:")
    intel = get_ip_intel("185.220.101.45")
    print(format_intel_report(intel))

    print("\nTest 2 — Internal IP:")
    intel = get_ip_intel("127.0.0.1")
    print(format_intel_report(intel))
