import socket
import os
import json
import threading
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

LOGSTASH_HOST = "172.17.0.1"
LOGSTASH_PORT = 5000
HOSTNAME = open("/etc/hostname").read().strip()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL     = "http://10.0.2.2:8000/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

PROMPTS = {
    "/wp-admin":         "Generate a convincing fake WordPress admin login page HTML with username/password fields. Return only raw HTML.",
    "/wp-login.php":     "Generate a convincing fake WordPress login page HTML. Return only raw HTML.",
    "/config.php":       "Generate a fake PHP config file with fake database credentials. Return only file contents.",
    "/.git/config":      "Generate a fake .git/config file with fake remote URLs. Return only file contents.",
    "/admin":            "Generate a fake HTML admin dashboard login page. Return only raw HTML.",
    "/.env":             "Generate a fake .env file with fake API keys and secrets. Return only file contents.",
    "/api/v1/users":     "Generate a fake JSON API response with 5 fake user accounts. Return only valid JSON.",
    "/phpmyadmin":       "Generate a fake phpMyAdmin login page HTML. Return only raw HTML.",
    "/.aws/credentials": "Generate fake AWS credentials file content. Return only file contents.",
}

DEFAULT_PROMPT = "Generate a fake HTML 403 Forbidden error page. Return only raw HTML."

FAKE_DASHBOARD = (
    "<!DOCTYPE html><html><head><title>WordPress Dashboard</title>"
    "<style>"
    "body{font-family:Arial,sans-serif;margin:0;background:#f1f1f1;}"
    "#wpwrap{display:flex;}"
    "#adminmenu{width:160px;background:#23282d;min-height:100vh;padding:10px 0;}"
    "#adminmenu a{display:block;color:#eee;padding:8px 15px;text-decoration:none;font-size:13px;}"
    "#adminmenu a:hover{background:#2b2b2b;color:#00b9eb;}"
    "#wpcontent{flex:1;padding:20px;}"
    ".wrap h1{font-size:23px;color:#23282d;}"
    ".welcome-panel{background:#fff;border:1px solid #e5e5e5;padding:20px;margin-bottom:20px;}"
    ".dashboard-widget{background:#fff;border:1px solid #e5e5e5;padding:15px;margin-bottom:15px;}"
    ".dashboard-widget h3{margin:0 0 10px;font-size:14px;}"
    "table{width:100%;border-collapse:collapse;}"
    "table td,table th{padding:8px;border-bottom:1px solid #eee;font-size:13px;}"
    "table th{background:#f9f9f9;font-weight:bold;}"
    ".button{background:#0085ba;color:#fff;padding:6px 12px;border:none;cursor:pointer;font-size:13px;}"
    "#wpadminbar{background:#23282d;color:#eee;padding:8px 15px;font-size:13px;}"
    "</style></head><body>"
    "<div id='wpadminbar'>Howdy, admin | "
    "<a href='/wp-admin' style='color:#eee'>Dashboard</a> | "
    "<a href='/wp-login.php?action=logout' style='color:#eee'>Log Out</a></div>"
    "<div id='wpwrap'>"
    "<div id='adminmenu'>"
    "<a href='/wp-admin'>Dashboard</a>"
    "<a href='/wp-admin/edit.php'>Posts</a>"
    "<a href='/wp-admin/upload.php'>Media</a>"
    "<a href='/wp-admin/edit.php?post_type=page'>Pages</a>"
    "<a href='/wp-admin/edit-comments.php'>Comments</a>"
    "<a href='/wp-admin/themes.php'>Appearance</a>"
    "<a href='/wp-admin/plugins.php'>Plugins</a>"
    "<a href='/wp-admin/users.php'>Users</a>"
    "<a href='/wp-admin/tools.php'>Tools</a>"
    "<a href='/wp-admin/options-general.php'>Settings</a>"
    "</div>"
    "<div id='wpcontent'><div class='wrap'>"
    "<h1>Dashboard</h1>"
    "<div class='welcome-panel'>"
    "<h2>Welcome to WordPress!</h2>"
    "<p>You are logged in as <strong>admin</strong>.</p>"
    "<button class='button'>Write your first blog post</button>"
    "</div>"
    "<div class='dashboard-widget'><h3>At a Glance</h3>"
    "<table>"
    "<tr><td>Posts</td><td>247</td></tr>"
    "<tr><td>Pages</td><td>18</td></tr>"
    "<tr><td>Comments</td><td>1429</td></tr>"
    "<tr><td>Users</td><td>34</td></tr>"
    "</table></div>"
    "<div class='dashboard-widget'><h3>Recent Activity</h3>"
    "<table>"
    "<tr><th>Time</th><th>Action</th><th>User</th></tr>"
    "<tr><td>2 mins ago</td><td>Published post</td><td>editor1</td></tr>"
    "<tr><td>1 hour ago</td><td>Updated page</td><td>admin</td></tr>"
    "<tr><td>3 hours ago</td><td>New comment</td><td>visitor</td></tr>"
    "</table></div>"
    "</div></div></div></body></html>"
)

FAKE_USERS_PAGE = (
    "<!DOCTYPE html><html><head><title>Users - WordPress</title>"
    "<style>"
    "body{font-family:Arial,sans-serif;background:#f1f1f1;margin:0;}"
    "#wpadminbar{background:#23282d;color:#eee;padding:8px 15px;font-size:13px;}"
    ".wrap{padding:20px;}"
    "h1{font-size:23px;color:#23282d;}"
    "table{width:100%;border-collapse:collapse;background:#fff;}"
    "table td,table th{padding:10px;border-bottom:1px solid #eee;font-size:13px;}"
    "table th{background:#f9f9f9;font-weight:bold;}"
    ".button{background:#0085ba;color:#fff;padding:5px 10px;text-decoration:none;font-size:12px;}"
    "</style></head><body>"
    "<div id='wpadminbar'>WordPress Admin | "
    "<a href='/wp-admin' style='color:#eee'>Dashboard</a></div>"
    "<div class='wrap'><h1>Users "
    "<a class='button' href='/wp-admin/user-new.php'>Add New</a></h1>"
    "<table>"
    "<tr><th>Username</th><th>Name</th><th>Email</th><th>Role</th></tr>"
    "<tr><td>admin</td><td>Site Admin</td><td>admin@corp.local</td><td>Administrator</td></tr>"
    "<tr><td>jsmith</td><td>John Smith</td><td>j.smith@corp.local</td><td>Editor</td></tr>"
    "<tr><td>mwilliams</td><td>Mary Williams</td><td>m.williams@corp.local</td><td>Author</td></tr>"
    "<tr><td>dbrown</td><td>David Brown</td><td>d.brown@corp.local</td><td>Contributor</td></tr>"
    "</table></div></body></html>"
)

FAKE_PLUGINS_PAGE = (
    "<!DOCTYPE html><html><head><title>Plugins - WordPress</title>"
    "<style>"
    "body{font-family:Arial,sans-serif;background:#f1f1f1;margin:0;}"
    "#wpadminbar{background:#23282d;color:#eee;padding:8px 15px;font-size:13px;}"
    ".wrap{padding:20px;}h1{font-size:23px;}"
    "table{width:100%;border-collapse:collapse;background:#fff;}"
    "table td,table th{padding:10px;border-bottom:1px solid #eee;font-size:13px;}"
    ".active{color:green;font-weight:bold;}.inactive{color:red;}"
    "</style></head><body>"
    "<div id='wpadminbar'>WordPress Admin | "
    "<a href='/wp-admin' style='color:#eee'>Dashboard</a></div>"
    "<div class='wrap'><h1>Plugins</h1>"
    "<table>"
    "<tr><th>Plugin</th><th>Version</th><th>Status</th></tr>"
    "<tr><td>Akismet Anti-Spam</td><td>5.3.1</td><td class='active'>Active</td></tr>"
    "<tr><td>WooCommerce</td><td>8.2.1</td><td class='active'>Active</td></tr>"
    "<tr><td>Yoast SEO</td><td>21.5</td><td class='active'>Active</td></tr>"
    "<tr><td>WP Super Cache</td><td>1.9.4</td><td class='inactive'>Inactive</td></tr>"
    "<tr><td>Wordfence Security</td><td>7.10.0</td><td class='active'>Active</td></tr>"
    "</table></div></body></html>"
)

STATIC_TEMPLATES = {
    "/.env": (
        "APP_NAME=CorporatePortal\n"
        "APP_ENV=production\n"
        "APP_KEY=base64:kJ3nV8xZqP2mR7tY9wL4sF6hD1bC5gN0\n"
        "DB_HOST=10.0.1.45\n"
        "DB_DATABASE=corp_production\n"
        "DB_USERNAME=dbadmin\n"
        "DB_PASSWORD=Str0ngP@ssw0rd!2024\n"
        "AWS_ACCESS_KEY_ID=AKIA1234567890EXAMPLE\n"
        "AWS_SECRET_ACCESS_KEY=abcde12345secretkey\n"
    ),
    "/config.php": (
        "<?php\n"
        "define('DB_HOST', '10.0.1.45');\n"
        "define('DB_USER', 'corp_admin');\n"
        "define('DB_PASS', 'C0rp@dm1n2024!');\n"
        "define('DB_NAME', 'corp_production');\n"
        "define('API_KEY', 'sk_live_4xAmPlEkEy123456789');\n"
        "?>"
    ),
    "/.git/config": (
        "[core]\n"
        "    repositoryformatversion = 0\n"
        "[remote \"origin\"]\n"
        "    url = https://github.com/corp-internal/backend.git\n"
        "[branch \"main\"]\n"
        "    remote = origin\n"
    ),
    "/api/v1/users": (
        '{"users":['
        '{"id":1,"email":"admin@corp.local","role":"admin"},'
        '{"id":2,"email":"dev@corp.local","role":"developer"}'
        ']}'
    ),
}

DEFAULT_STATIC = "<html><body><h1>403 Forbidden</h1></body></html>"

TARPIT_ROUTES = {
    "/wp-admin/users.php":   FAKE_USERS_PAGE,
    "/wp-admin/plugins.php": FAKE_PLUGINS_PAGE,
    "/wp-admin/index.php":   FAKE_DASHBOARD,
    "/wp-admin/dashboard":   FAKE_DASHBOARD,
}

def ask_groq(path):
    prompt = PROMPTS.get(path, DEFAULT_PROMPT)
    try:
        payload = json.dumps({
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.9
        }).encode()
        req = urllib.request.Request(
            GROQ_URL, data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {GROQ_API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            content = content.replace("```html","").replace("```json","").replace("```","").strip()
            return content
    except Exception as e:
        print(f"[GROQ ERROR] {e}")
        return None

def get_response(path):
    ai = ask_groq(path)
    if ai:
        return ai
    return STATIC_TEMPLATES.get(path, DEFAULT_STATIC)

def ship_log(event):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((LOGSTASH_HOST, LOGSTASH_PORT))
            s.send((json.dumps(event) + "\n").encode())
    except:
        pass

class HoneypotHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        attacker_ip = self.client_address[0]

        if self.path in TARPIT_ROUTES:
            response_body = TARPIT_ROUTES[self.path]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(response_body.encode())
            event = {
                "@timestamp":  datetime.now(timezone.utc).isoformat(),
                "attacker_ip": attacker_ip,
                "request":     f"GET {self.path} HTTP/1.1",
                "status":      "200",
                "user_agent":  self.headers.get("User-Agent","unknown"),
                "target_node": HOSTNAME,
                "message":     "TARPIT - Attacker browsing fake dashboard",
                "severity":    "critical",
                "event_type":  "TARPIT_BROWSE"
            }
            threading.Thread(target=ship_log, args=(event,)).start()
            return

        event = {
            "@timestamp":  datetime.now(timezone.utc).isoformat(),
            "attacker_ip": attacker_ip,
            "request":     f"GET {self.path} HTTP/1.1",
            "status":      "200",
            "user_agent":  self.headers.get("User-Agent","unknown"),
            "target_node": HOSTNAME,
            "message":     "Unauthorized Web Access",
            "severity":    "critical",
            "event_type":  "PROBE"
        }
        threading.Thread(target=ship_log, args=(event,)).start()

        response_body = get_response(self.path)
        self.send_response(200)
        if self.path in ["/config.php","/.git/config","/.env"]:
            self.send_header("Content-Type","text/plain")
        elif self.path == "/api/v1/users":
            self.send_header("Content-Type","application/json")
        else:
            self.send_header("Content-Type","text/html")
        self.end_headers()
        self.wfile.write(response_body.encode())

    def do_POST(self):
        attacker_ip = self.client_address[0]
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8", errors="ignore")

        try:
            params = urllib.parse.parse_qs(post_data)
            username = params.get("log", params.get("user_login", params.get("username", ["unknown"])))[0]
            password = params.get("pwd", params.get("user_password", params.get("password", ["unknown"])))[0]
        except:
            username = "unknown"
            password = "unknown"

        event = {
            "@timestamp":  datetime.now(timezone.utc).isoformat(),
            "attacker_ip": attacker_ip,
            "request":     f"POST {self.path} HTTP/1.1",
            "status":      "302",
            "user_agent":  self.headers.get("User-Agent","unknown"),
            "target_node": HOSTNAME,
            "message":     f"CREDENTIAL CAPTURED: {username}:{password}",
            "severity":    "critical",
            "event_type":  "CREDENTIAL_CAPTURE",
            "username":    username,
            "password":    password
        }
        threading.Thread(target=ship_log, args=(event,)).start()
        print(f"[TARPIT] Credentials captured: {username}:{password} from {attacker_ip}")

        self.send_response(302)
        self.send_header("Location", "/wp-admin/index.php")
        self.send_header("Set-Cookie", "wordpress_logged_in=admin; Path=/wp-admin")
        self.end_headers()

    def log_message(self, format, *args):
        pass

print(f"[EIDOLON] Tarpit honeypot starting on {HOSTNAME} port 80")
server = HTTPServer(("0.0.0.0", 80), HoneypotHandler)
server.serve_forever()
