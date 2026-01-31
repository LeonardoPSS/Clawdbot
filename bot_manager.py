"""
Simple Bot Manager - Direct activation script
Run this to start the LinkedIn bot
"""
import subprocess
import sys
import os

def start_bot():
    bot_dir = r"C:\Users\leona\Downloads\AntigravityJobBot"
    os.chdir(bot_dir)
    
    print("🚀 Starting LinkedIn Bot with Auto-Restart...")
    print("The bot will run continuously. If it crashes, it will restart in 60 seconds.")
    print("Press Ctrl+C to stop.\n")
    
    while True:
        try:
            print(f"\n[Manager] Launching bot instance...")
            # Run the bot and wait for it to complete/crash
            process = subprocess.run([sys.executable, "-m", "src.main"], check=False)
            
            # Check exit code
            if process.returncode == 0:
                print(f"[Manager] Bot finished gracefully. Restarting in 60s...")
            else:
                print(f"[Manager] Bot crashed with code {process.returncode}. Restarting in 60s...")
                
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n✋ Bot stopped by user (Manager).")
            break
        except Exception as e:
            print(f"❌ Manager Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    start_bot()
