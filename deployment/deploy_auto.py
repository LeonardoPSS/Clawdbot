import paramiko
import os
import sys
import zipfile
import tempfile
import shutil
import time
from scp import SCPClient

# Configuration
DROPLET_IP = "161.35.132.145"
REMOTE_USER = "root"
REMOTE_DIR = "/root/nexara"
ZIP_NAME = "nexara_deploy.zip"

def create_zip_package():
    """Creates a deployment zip package excluding unnecessary files."""
    print("📦 Packaging Nexara for cloud deployment...")
    
    project_root = os.getcwd()
    # Handle running from deployment subdir
    if os.path.basename(project_root) == "deployment":
        project_root = os.path.dirname(project_root)
        
    excludes = {'.git', '.venv', '__pycache__', '.idea', '.vscode', 'node_modules', 'logs', 'data', 'deploy_auto.py', 'browser_profile'}
    
    # Create temp dir for clean zip
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, ZIP_NAME)
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_root):
                # Filter directories
                dirs[:] = [d for d in dirs if d not in excludes]
                
                for file in files:
                    if file == ZIP_NAME or file.endswith('.zip') or file.endswith('.pyc'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, project_root)
                    
                    # More exclusion checks
                    if any(x in rel_path.split(os.sep) for x in excludes):
                        continue
                        
                    print(f"  Adding: {rel_path}")
                    zipf.write(file_path, rel_path)
        
        return zip_path, temp_dir
    except Exception as e:
        print(f"❌ Zip Error: {e}")
        return None, temp_dir

def deploy(password):
    print(f"🚀 Starting deployment to {DROPLET_IP}...")
    
    # 1. Create Zip
    local_zip, temp_dir = create_zip_package()
    if not local_zip:
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 2. Connect
        print("🔑 Connecting to server...")
        ssh.connect(DROPLET_IP, username=REMOTE_USER, password=password)
        
        # 3. Upload
        print("☁️ Uploading code...")
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_zip, f"/root/{ZIP_NAME}")
        
        # 4. Configure & Launch
        print("⚙️ Configuring server and launching Docker...")
        
        commands = [
            # Check file
            f"ls -la /root/{ZIP_NAME}",
            
            # Install deps if missing
            "apt-get update && apt-get install -y unzip docker-compose || echo 'Deps installed'",
            
            # Setup directories
            f"mkdir -p {REMOTE_DIR}",
            f"mv /root/{ZIP_NAME} {REMOTE_DIR}/",
            f"cd {REMOTE_DIR} && unzip -o {ZIP_NAME}",
            f"rm {REMOTE_DIR}/{ZIP_NAME}",
            
            # Docker setup
            f"cd {REMOTE_DIR}/deployment",
            "docker-compose down",
            "docker-compose up -d --build"
        ]
        
        full_command = " && ".join(commands)
        stdin, stdout, stderr = ssh.exec_command(full_command)
        
        # Stream output
        for line in stdout:
            print(f"  [REMOTE] {line.strip()}")
            
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("\n✅ Deployment Successful! Nexara is live.")
            print(f"   Check status with: ssh {REMOTE_USER}@{DROPLET_IP} 'docker logs -f clawdbot_vps'")
        else:
            print(f"\n❌ Remote command failed with exit code {exit_status}")
            print(stderr.read().decode())

    except Exception as e:
        print(f"\n❌ Deployment Failed: {e}")
    finally:
        ssh.close()
        shutil.rmtree(temp_dir) # Cleanup

if __name__ == "__main__":
    if len(sys.argv) < 2:
        password = input("Enter Droplet Password: ")
    else:
        password = sys.argv[1]
        
    deploy(password)
