from faker import Faker
import subprocess
import random
import string

fake = Faker()

def generate_fake_aws_key():
    # AWS Access Keys always start with AKIA
    key_id = "AKIA" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    secret = ''.join(random.choices(string.ascii_letters + string.digits + '/+', k=40))
    return key_id, secret

def inject_honeytoken(container_name):
    key_id, secret = generate_fake_aws_key()
    region = random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])
    
    aws_creds = f"""[default]
aws_access_key_id = {key_id}
aws_secret_access_key = {secret}
region = {region}
"""
    # Create .aws directory and drop credentials
    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', 'mkdir -p /root/.aws'],
        capture_output=True)

    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', f'echo "{aws_creds}" > /root/.aws/credentials'],
        capture_output=True)

    # Also drop a fake SSH private key as extra bait
    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', 'mkdir -p /root/.ssh'],
        capture_output=True)

    fake_ssh = f"""-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA{fake.md5()}{fake.md5()}{fake.md5()}
{fake.md5()}{fake.md5()}{fake.md5()}{fake.md5()}
-----END RSA PRIVATE KEY-----"""

    subprocess.run(['docker', 'exec', container_name,
        'sh', '-c', f'echo \'{fake_ssh}\' > /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa'],
        capture_output=True)

    print(f"🪤 {container_name} → AWS Key: {key_id} | Region: {region}")

# Get all decoy containers
result = subprocess.run(
    ['docker', 'ps', '--filter', 'name=eidolon-stack_web-farm-decoy',
     '--format', '{{.Names}}'],
    capture_output=True, text=True
)

containers = result.stdout.strip().split('\n')
containers = [c for c in containers if c]

print(f"🪤 Planting honeytokens in {len(containers)} nodes...\n")

for container in containers:
    inject_honeytoken(container)

print(f"\n✅ Honeytokens planted in all {len(containers)} nodes!")
print("If an attacker steals and uses these keys, AWS CloudTrail will log the attempt.")
