import pandas as pd
import sys
from src.config import load_config

def show_dashboard():
    config = load_config("config/settings.yaml")
    csv_path = config.logging.save_path + "/applied.csv"
    # Force UTF-8 output for Windows terminals
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except FileNotFoundError:
        print("No data found yet.")
        return
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print("\n" + "="*40)
    print(f"📊  JOB BOT DASHBOARD  📊")
    print("="*40)
    
    # 1. Total Applications
    total = len(df)
    print(f"\n📌 TOTAL VAGAS PROCESSADAS: {total}")
    
    # 2. Status Breakdown
    print(f"\n📌 STATUS:")
    print(df['status'].value_counts().to_string())

    # 3. Platform Breakdown
    print(f"\n📌 PLATAFORMAS:")
    print(df['platform'].value_counts().to_string())
    
    # 4. Latest Actions
    print(f"\n📌 ÚLTIMAS 5 AÇÕES:")
    latest = df.tail(5)[['date', 'title', 'company', 'status']]
    print(latest.to_string(index=False))
    
    print("\n" + "="*40)

if __name__ == "__main__":
    show_dashboard()
