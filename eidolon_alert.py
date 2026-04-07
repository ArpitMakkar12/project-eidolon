import time
import smtplib
import json
import urllib.request
import sys
import os
sys.path.insert(0, "/home/arpit/eidolon-swarm")
from threat_intel import get_ip_intel
from attack_classifier import classify_attack, format_classification
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Config ─────────────────────────────────────────────────────────────────
ES_URL           = "http://127.0.0.1:9200"
INDEX            = "eidolon-honeypot-*"
SENDER           = os.getenv("SENDER")
RECEIVER         = os.getenv("RECEIVER")
APP_PASS         = os.getenv("APP_PASS")
ATTACK_LOG       = "/var/log/eidolon-attacks.log"
CHECK_INTERVAL   = 60
QUERY_WINDOW     = 120
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_URL     = "http://10.0.2.2:8000/telegram"
DISCORD_WEBHOOK  = os.getenv("DISCORD_WEBHOOK")

def query_es():
    try:
        since = (datetime.now(timezone.utc) - timedelta(seconds=QUERY_WINDOW)).isoformat()
        query = json.dumps({
            "query": {"range": {"@timestamp": {"gte": since}}},
            "size": 100
        }).encode()
        req = urllib.request.Request(
            f"{ES_URL}/{INDEX}/_search",
            data=query,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [h["_source"] for h in data.get("hits", {}).get("hits", [])]
    except Exception as e:
        print(f"[ES ERROR] {e}")
        return []

def ban_ip(ip):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ATTACK_LOG, "a") as f:
            f.write(f"{timestamp} ATTACKER_IP={ip}\n")
        print(f"[FAIL2BAN] Logged IP for banning: {ip}")
    except Exception as e:
        print(f"[FAIL2BAN ERROR] {e}")

def send_telegram(events, intel_map, class_map):
    try:
        ips   = list(set(e.get("attacker_ip","unknown") for e in events))
        nodes = list(set(e.get("target_node","unknown") for e in events))

        for ip in ips:
            intel  = intel_map.get(ip, {})
            attack = class_map.get(ip, {})
            flag   = intel.get("country_flag","🌐")
            score  = intel.get("abuse_score", 0)
            level  = intel.get("threat_level","UNKNOWN")
            tor    = "YES ⚠️" if intel.get("is_tor") else "No"
            threat_emoji = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(level,"🟢")
            atk_emoji    = attack.get("emoji","❓")
            atk_type     = attack.get("type","UNKNOWN")
            atk_risk     = attack.get("risk","UNKNOWN")
            atk_conf     = attack.get("confidence",0)
            atk_desc     = attack.get("description","")
            atk_action   = attack.get("action","")
            risk_emoji   = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(atk_risk,"⚪")

            msg = f"""🚨 *PROJECT EIDOLON BREACH ALERT*

🕐 *Time:* `{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC`
📊 *Events:* {len(events)} attacks detected
🖥️ *Nodes Hit:* {len(nodes)} honeypots breached

━━━━━━━━━━━━━━━━━━━
{atk_emoji} *ATTACK CLASSIFICATION*
━━━━━━━━━━━━━━━━━━━
🏷️ *Type:* `{atk_type}`
{risk_emoji} *Risk Level:* {atk_risk}
📈 *Confidence:* {atk_conf}%
📋 *Description:* {atk_desc}
⚡ *Action:* {atk_action}

━━━━━━━━━━━━━━━━━━━
🔍 *ATTACKER INTELLIGENCE*
━━━━━━━━━━━━━━━━━━━
🌐 *IP:* `{ip}`
{flag} *Location:* {intel.get("city","Unknown")}, {intel.get("country","Unknown")}
🏢 *Org:* {intel.get("org", intel.get("isp","Unknown"))}
{threat_emoji} *Abuse Score:* {score}/100
🧅 *Tor Node:* {tor}
📋 *Reports:* {intel.get("total_reports",0)} in 90 days

━━━━━━━━━━━━━━━━━━━
📌 *RECENT HITS*
━━━━━━━━━━━━━━━━━━━"""

            for e in events[:3]:
                msg += f"""
🖥️ `{e.get("target_node","?")}` → `{e.get("request","?")}`"""

            msg += f"""

━━━━━━━━━━━━━━━━━━━
🛡️ *Action Taken:* IP banned 24h via Fail2Ban
📊 *Dashboard:* http://127.0.0.1:5601"""

            payload = json.dumps({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown"
            }).encode()

            req = urllib.request.Request(
                f"{TELEGRAM_URL}/sendMessage",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[TELEGRAM] Alert sent for IP {ip}")

    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")

def send_discord(events, intel_map, class_map):
    try:
        ips   = list(set(e.get("attacker_ip","unknown") for e in events))
        nodes = list(set(e.get("target_node","unknown") for e in events))
        reqs  = list(set(e.get("request","unknown") for e in events))

        for ip in ips:
            intel  = intel_map.get(ip, {})
            attack = class_map.get(ip, {})
            flag   = intel.get("country_flag","🌐")
            score  = intel.get("abuse_score", 0)
            level  = intel.get("threat_level","UNKNOWN")
            tor    = "YES ⚠️" if intel.get("is_tor") else "No"
            atk_emoji  = attack.get("emoji","❓")
            atk_type   = attack.get("type","UNKNOWN")
            atk_risk   = attack.get("risk","UNKNOWN")
            atk_conf   = attack.get("confidence",0)
            atk_desc   = attack.get("description","")
            atk_action = attack.get("action","")
            atk_stats  = attack.get("stats",{})

            color_map = {"CRITICAL":15158332,"HIGH":15105570,"MEDIUM":16776960,"LOW":3066993}
            color = color_map.get(level, 3066993)

            threat_emoji = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(level,"🟢")
            risk_emoji   = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(atk_risk,"⚪")

            recent = ""
            for e in events[:5]:
                recent += f"• `{e.get('target_node','?')}` → `{e.get('request','?')}`\n"

            fields = [
                {"name": f"{atk_emoji} Attack Type", "value": f"`{atk_type}`", "inline": True},
                {"name": f"{risk_emoji} Risk Level", "value": atk_risk, "inline": True},
                {"name": "📈 Confidence", "value": f"{atk_conf}%", "inline": True},
                {"name": "📋 Description", "value": atk_desc, "inline": False},
                {"name": "⚡ Recommended Action", "value": atk_action, "inline": False},
                {"name": "━━━━━━━━━━━━━━━━━━━", "value": "**ATTACKER INTELLIGENCE**", "inline": False},
                {"name": f"{flag} Location", "value": f"{intel.get('city','Unknown')}, {intel.get('country','Unknown')}", "inline": True},
                {"name": "🌐 IP Address", "value": f"`{ip}`", "inline": True},
                {"name": f"{threat_emoji} Abuse Score", "value": f"{score}/100", "inline": True},
                {"name": "🏢 Organisation", "value": intel.get("org", intel.get("isp","Unknown")), "inline": True},
                {"name": "🧅 Tor Exit Node", "value": tor, "inline": True},
                {"name": "📋 Reports (90d)", "value": str(intel.get("total_reports",0)), "inline": True},
                {"name": "━━━━━━━━━━━━━━━━━━━", "value": "**ATTACK STATISTICS**", "inline": False},
                {"name": "📊 Total Events", "value": str(len(events)), "inline": True},
                {"name": "🖥️ Nodes Hit", "value": str(len(nodes)), "inline": True},
                {"name": "🔗 Unique Paths", "value": str(atk_stats.get("unique_paths",0)), "inline": True},
                {"name": "📌 Recent Hits", "value": recent or "None", "inline": False},
                {"name": "🛡️ Action Taken", "value": "IP banned for 24 hours via Fail2Ban", "inline": False},
            ]

            embed = {
                "title": f"🚨 EIDOLON BREACH — {atk_emoji} {atk_type}",
                "description": f"**{len(events)} attacks** across **{len(nodes)} honeypots** | `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`",
                "color": color,
                "fields": fields,
                "footer": {"text": "Project Eidolon — AI Cyber Deception System"}
            }

            payload = json.dumps({"embeds": [embed]}).encode()
            req = urllib.request.Request(
                DISCORD_WEBHOOK,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[DISCORD] Alert sent for IP {ip}")

    except Exception as e:
        print(f"[DISCORD ERROR] {e}")

def send_email(events, intel_map, class_map):
    try:
        ips   = list(set(e.get("attacker_ip","unknown") for e in events))
        nodes = list(set(e.get("target_node","unknown") for e in events))
        reqs  = list(set(e.get("request","unknown") for e in events))

        body = f"""
╔══════════════════════════════════════════════════╗
║        🚨 PROJECT EIDOLON BREACH ALERT 🚨         ║
╚══════════════════════════════════════════════════╝

Time         : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC
Total Events : {len(events)} attacks detected
Nodes Hit    : {len(nodes)} honeypots breached
Action Taken : IPs banned via Fail2Ban for 24 hours
"""
        for ip in ips:
            intel  = intel_map.get(ip, {})
            attack = class_map.get(ip, {})
            flag   = intel.get("country_flag","🌐")
            score  = intel.get("abuse_score", 0)
            level  = intel.get("threat_level","UNKNOWN")
            tor    = "YES ⚠️" if intel.get("is_tor") else "No"
            threat_emoji = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(level,"🟢")
            risk_emoji   = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}.get(attack.get("risk","LOW"),"⚪")

            body += f"""
══════════════════════════════════════════════════
  {attack.get("emoji","❓")} ATTACK CLASSIFICATION
══════════════════════════════════════════════════
  Type         : {attack.get("type","UNKNOWN")}
  Risk Level   : {risk_emoji} {attack.get("risk","UNKNOWN")}
  Confidence   : {attack.get("confidence",0)}%
  Description  : {attack.get("description","")}
  Action       : {attack.get("action","")}

══════════════════════════════════════════════════
  🔍 ATTACKER INTELLIGENCE
══════════════════════════════════════════════════
  IP Address   : {ip}
  Location     : {flag} {intel.get("city","Unknown")}, {intel.get("country","Unknown")}
  Organisation : {intel.get("org", intel.get("isp","Unknown"))}
  Abuse Score  : {score}/100 {threat_emoji}
  Threat Level : {level}
  Tor Exit Node: {tor}
  Reports      : {intel.get("total_reports",0)} in last 90 days
"""
        body += """
══════════════════════════════════════════════════
  📌 RECENT EVENTS
══════════════════════════════════════════════════
"""
        for e in events[:5]:
            ip    = e.get("attacker_ip","unknown")
            intel = intel_map.get(ip,{})
            flag  = intel.get("country_flag","🌐")
            body += f"""
  Node      : {e.get("target_node","unknown")}
  Attacker  : {flag} {ip}
  Request   : {e.get("request","unknown")}
  Agent     : {e.get("user_agent","unknown")}
  Time      : {e.get("@timestamp","unknown")}
  ────────────────────────────────────────────
"""
        msg = MIMEMultipart()
        msg["Subject"] = f"🚨 EIDOLON: {len(events)} attacks | {list(class_map.values())[0].get('emoji','🔴')} {list(class_map.values())[0].get('type','UNKNOWN')} detected"
        msg["From"]    = SENDER
        msg["To"]      = RECEIVER
        msg.attach(MIMEText(body,"plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER, APP_PASS)
            smtp.send_message(msg)
        print(f"[EMAIL] Alert sent — {len(events)} events")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

def main():
    print("[EIDOLON] Alert engine — Email + Telegram + Discord + Classification")
    banned_ips = set()

    while True:
        events = query_es()
        if events:
            new_ips = set()
            for event in events:
                ip = event.get("attacker_ip","")
                if ip and ip not in banned_ips:
                    new_ips.add(ip)

            if new_ips:
                print(f"[ALERT] {len(events)} attacks from {len(new_ips)} new IPs!")

                # Get threat intel + classify for each IP
                intel_map = {}
                class_map = {}

                for ip in new_ips:
                    # Threat intel
                    print(f"[INTEL] Looking up {ip}...")
                    intel_map[ip] = get_ip_intel(ip)
                    print(f"[INTEL] {ip} → {intel_map[ip].get('country','?')} | Score: {intel_map[ip].get('abuse_score',0)}/100")

                    # Classify attack
                    ip_events = [e for e in events if e.get("attacker_ip") == ip]
                    class_map[ip] = classify_attack(ip_events)
                    atk = class_map[ip]
                    print(f"[CLASSIFY] {ip} → {atk['emoji']} {atk['type']} | Risk: {atk['risk']} | Confidence: {atk['confidence']}%")

                # Ban IPs
                for ip in new_ips:
                    ban_ip(ip)
                    banned_ips.add(ip)

                # Send all alerts
                send_telegram(events, intel_map, class_map)
                send_discord(events, intel_map, class_map)
                send_email(events, intel_map, class_map)

            else:
                print(f"[{datetime.now().strftime("%H:%M:%S")}] Known attackers monitored")
        else:
            print(f"[{datetime.now().strftime("%H:%M:%S")}] Grid secure")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
