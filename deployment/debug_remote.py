import paramiko
import sys

DROPLET_IP = "161.35.132.145"
USER = "root"

def check_logs(password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"🔌 Connecting to {DROPLET_IP}...")
        client.connect(DROPLET_IP, username=USER, password=password)
        
        print("🔍 Fetching logs for clawdbot_vps...")
        stdin, stdout, stderr = client.exec_command("docker logs --tail 50 clawdbot_vps")
        
        print("\n" + "="*40)
        print(stdout.read().decode())
        print(stderr.read().decode())
        print("="*40 + "\n")
        
        # Also check if it's running
        stdin, stdout, stderr = client.exec_command("docker ps -a | grep clawdbot_vps")
        print("🐋 Container Status:")
        print(stdout.read().decode())

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    pwd = sys.argv[1] if len(sys.argv) > 1 else input("Password: ")
    check_logs(pwd)
