#!/usr/bin/env python3
"""
Project Eidolon — Attack Pattern Recognition Engine
Automatically classifies attacks based on behaviour patterns
"""

from datetime import datetime, timezone
import json

# ── URL Categories ─────────────────────────────────────────────────────────
WORDPRESS_PATHS = [
    "/wp-admin", "/wp-login.php", "/wp-content", "/wp-includes",
    "/xmlrpc.php", "/wp-json", "/wp-config.php"
]

DATABASE_PATHS = [
    "/phpmyadmin", "/pma", "/mysql", "/adminer",
    "/db", "/database", "/sql"
]

CONFIG_PATHS = [
    "/.env", "/config.php", "/config.yml", "/config.json",
    "/.git/config", "/web.config", "/app.config"
]

CLOUD_PATHS = [
    "/.aws/credentials", "/.aws/config",
    "/metadata/v1", "/latest/meta-data"
]

API_PATHS = [
    "/api/v1/users", "/api/v1/admin", "/api",
    "/graphql", "/swagger", "/actuator"
]

SHELL_PATHS = [
    "/shell", "/cmd", "/exec", "/system",
    "/cgi-bin", "/.php", "/eval"
]

RECON_PATHS = [
    "/robots.txt", "/sitemap.xml", "/.well-known",
    "/security.txt", "/humans.txt"
]

# ── Classifier ─────────────────────────────────────────────────────────────
def classify_attack(events_for_ip):
    """
    Classify attack type based on behaviour patterns
    Returns classification dict with type, confidence, description
    """
    if not events_for_ip:
        return {"type": "UNKNOWN", "confidence": 0, "description": "No data"}

    # Extract data
    requests     = [e.get("request", "") for e in events_for_ip]
    timestamps   = [e.get("@timestamp", "") for e in events_for_ip]
    user_agents  = list(set(e.get("user_agent", "") for e in events_for_ip))
    nodes_hit    = list(set(e.get("target_node", "") for e in events_for_ip))
    total_events = len(events_for_ip)

    # Extract URL paths
    paths = []
    for r in requests:
        parts = r.split(" ")
        if len(parts) >= 2:
            paths.append(parts[1])

    # ── Pattern scores ─────────────────────────────────────────────────────
    scores = {
        "AUTOMATED_SCANNER":    0,
        "WORDPRESS_ATTACK":     0,
        "DATABASE_ATTACK":      0,
        "CREDENTIAL_STUFFER":   0,
        "CLOUD_HUNTER":         0,
        "API_SCANNER":          0,
        "VULNERABILITY_SCANNER":0,
        "RECONNAISSANCE":       0,
        "TARGETED_ATTACK":      0,
    }

    # Score: Automated scanner
    if total_events >= 10:
        scores["AUTOMATED_SCANNER"] += 30
    if len(nodes_hit) >= 5:
        scores["AUTOMATED_SCANNER"] += 30
    if len(user_agents) == 1 and "wget" in user_agents[0].lower():
        scores["AUTOMATED_SCANNER"] += 20
    if len(set(paths)) >= 5:
        scores["AUTOMATED_SCANNER"] += 20

    # Score: WordPress attack
    wp_hits = sum(1 for p in paths if any(wp in p for wp in WORDPRESS_PATHS))
    if wp_hits > 0:
        scores["WORDPRESS_ATTACK"] += min(wp_hits * 25, 100)

    # Score: Database attack
    db_hits = sum(1 for p in paths if any(db in p for db in DATABASE_PATHS))
    if db_hits > 0:
        scores["DATABASE_ATTACK"] += min(db_hits * 25, 100)

    # Score: Credential stuffer
    login_hits = sum(1 for p in paths if any(x in p for x in
                    ["/wp-admin", "/wp-login", "/admin", "/login",
                     "/signin", "/auth", "/phpmyadmin"]))
    if login_hits >= 3:
        scores["CREDENTIAL_STUFFER"] += 60
    if len(set(paths)) <= 3 and login_hits >= 2:
        scores["CREDENTIAL_STUFFER"] += 40

    # Score: Cloud hunter
    cloud_hits = sum(1 for p in paths if any(c in p for c in CLOUD_PATHS))
    if cloud_hits > 0:
        scores["CLOUD_HUNTER"] += min(cloud_hits * 40, 100)

    # Score: API scanner
    api_hits = sum(1 for p in paths if any(a in p for a in API_PATHS))
    if api_hits > 0:
        scores["API_SCANNER"] += min(api_hits * 30, 100)

    # Score: Vulnerability scanner
    shell_hits = sum(1 for p in paths if any(s in p for s in SHELL_PATHS))
    config_hits = sum(1 for p in paths if any(c in p for c in CONFIG_PATHS))
    if shell_hits > 0:
        scores["VULNERABILITY_SCANNER"] += min(shell_hits * 35, 100)
    if config_hits >= 2:
        scores["VULNERABILITY_SCANNER"] += 40

    # Score: Reconnaissance
    recon_hits = sum(1 for p in paths if any(r in p for r in RECON_PATHS))
    if recon_hits > 0:
        scores["RECONNAISSANCE"] += min(recon_hits * 40, 100)
    if len(set(paths)) >= 8:
        scores["RECONNAISSANCE"] += 30

    # Score: Targeted attack
    if len(nodes_hit) <= 2 and total_events >= 5:
        scores["TARGETED_ATTACK"] += 40
    if len(set(paths)) >= 5 and len(nodes_hit) <= 3:
        scores["TARGETED_ATTACK"] += 40

    # ── Get top classification ─────────────────────────────────────────────
    top_type = max(scores, key=scores.get)
    top_score = scores[top_type]

    # If score too low — unknown
    if top_score < 20:
        top_type = "RECONNAISSANCE"
        top_score = 20

    # ── Descriptions ───────────────────────────────────────────────────────
    descriptions = {
        "AUTOMATED_SCANNER": {
            "desc": "Automated tool scanning for vulnerabilities across multiple targets",
            "risk": "MEDIUM",
            "emoji": "🤖",
            "action": "Bot detected — likely Masscan, Shodan, or similar scanner"
        },
        "WORDPRESS_ATTACK": {
            "desc": "Targeting WordPress admin panels and login pages",
            "risk": "HIGH",
            "emoji": "🎯",
            "action": "WordPress brute force or exploitation attempt"
        },
        "DATABASE_ATTACK": {
            "desc": "Attempting to access database management interfaces",
            "risk": "CRITICAL",
            "emoji": "🗄️",
            "action": "Database takeover attempt — phpMyAdmin/MySQL targeted"
        },
        "CREDENTIAL_STUFFER": {
            "desc": "Repeatedly targeting login endpoints with credentials",
            "risk": "HIGH",
            "emoji": "🔑",
            "action": "Credential stuffing attack — using leaked password lists"
        },
        "CLOUD_HUNTER": {
            "desc": "Hunting for exposed cloud credentials and metadata",
            "risk": "CRITICAL",
            "emoji": "☁️",
            "action": "Cloud credential theft attempt — AWS keys targeted"
        },
        "API_SCANNER": {
            "desc": "Scanning for exposed API endpoints and documentation",
            "risk": "HIGH",
            "emoji": "🔌",
            "action": "API enumeration — looking for unprotected endpoints"
        },
        "VULNERABILITY_SCANNER": {
            "desc": "Probing for known vulnerabilities and misconfigurations",
            "risk": "HIGH",
            "emoji": "🔍",
            "action": "CVE exploitation attempt or config file exposure"
        },
        "RECONNAISSANCE": {
            "desc": "Gathering information about target systems",
            "risk": "LOW",
            "emoji": "👁️",
            "action": "Initial reconnaissance — mapping the network"
        },
        "TARGETED_ATTACK": {
            "desc": "Focused attack on specific systems — possibly human attacker",
            "risk": "CRITICAL",
            "emoji": "⚠️",
            "action": "Manual targeted attack — human attacker suspected"
        },
    }

    info = descriptions.get(top_type, {
        "desc": "Unknown attack pattern",
        "risk": "MEDIUM",
        "emoji": "❓",
        "action": "Monitor closely"
    })

    return {
        "type":        top_type,
        "confidence":  min(top_score, 100),
        "description": info["desc"],
        "risk":        info["risk"],
        "emoji":       info["emoji"],
        "action":      info["action"],
        "stats": {
            "total_events":  total_events,
            "nodes_hit":     len(nodes_hit),
            "unique_paths":  len(set(paths)),
            "user_agents":   user_agents,
            "paths_probed":  list(set(paths))[:10]
        },
        "all_scores": scores
    }

def format_classification(ip, classification):
    """Format classification for display"""
    emoji  = classification.get("emoji","❓")
    ctype  = classification.get("type","UNKNOWN")
    risk   = classification.get("risk","UNKNOWN")
    conf   = classification.get("confidence",0)
    desc   = classification.get("description","")
    action = classification.get("action","")
    stats  = classification.get("stats",{})

    risk_emoji = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(risk,"⚪")

    return f"""
{emoji} ATTACK CLASSIFICATION
  IP           : {ip}
  Type         : {ctype}
  Risk Level   : {risk_emoji} {risk}
  Confidence   : {conf}%
  Description  : {desc}
  Action       : {action}
  Stats:
    Total Events : {stats.get("total_events",0)}
    Nodes Hit    : {stats.get("nodes_hit",0)}
    Unique Paths : {stats.get("unique_paths",0)}
    Paths Probed : {", ".join(stats.get("paths_probed",[])[:5])}"""

# ── Test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Attack Pattern Recognition...\n")

    # Test 1 — WordPress attack
    test_events_wp = [
        {"request": "GET /wp-admin HTTP/1.1", "target_node": "Node-1",
         "user_agent": "Mozilla/5.0", "@timestamp": "2026-04-04T10:00:00Z"},
        {"request": "GET /wp-login.php HTTP/1.1", "target_node": "Node-1",
         "user_agent": "Mozilla/5.0", "@timestamp": "2026-04-04T10:00:01Z"},
        {"request": "GET /wp-admin HTTP/1.1", "target_node": "Node-2",
         "user_agent": "Mozilla/5.0", "@timestamp": "2026-04-04T10:00:02Z"},
        {"request": "POST /wp-login.php HTTP/1.1", "target_node": "Node-1",
         "user_agent": "Mozilla/5.0", "@timestamp": "2026-04-04T10:00:03Z"},
    ]

    result = classify_attack(test_events_wp)
    print(format_classification("192.168.1.100", result))

    print("\n" + "="*50)

    # Test 2 — Cloud hunter
    test_events_cloud = [
        {"request": "GET /.aws/credentials HTTP/1.1", "target_node": "Node-5",
         "user_agent": "curl/7.68.0", "@timestamp": "2026-04-04T10:01:00Z"},
        {"request": "GET /.env HTTP/1.1", "target_node": "Node-5",
         "user_agent": "curl/7.68.0", "@timestamp": "2026-04-04T10:01:01Z"},
        {"request": "GET /config.php HTTP/1.1", "target_node": "Node-5",
         "user_agent": "curl/7.68.0", "@timestamp": "2026-04-04T10:01:02Z"},
    ]

    result2 = classify_attack(test_events_cloud)
    print(format_classification("10.0.0.55", result2))

    print("\n✅ Attack classifier working!")
