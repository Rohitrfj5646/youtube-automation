import sys
from datetime import datetime
from app import run_pipeline, init_db

def main():
    # Initialize DB (creates file if not exists)
    init_db()

    niche = None
    if len(sys.argv) > 1 and sys.argv[1] and sys.argv[1] != '""':
        niche = sys.argv[1]
    else:
        # Determine niche based on UTC hour
        # Cron triggers at 02:30, 06:30, 11:30 UTC
        current_hour = datetime.utcnow().hour
        if current_hour == 2 or current_hour == 3: # 02:30 UTC -> Stocks
            niche = "Stocks"
        elif current_hour == 6 or current_hour == 7: # 06:30 UTC -> Forex
            niche = "Forex"
        elif current_hour == 11 or current_hour == 12: # 11:30 UTC -> Crypto
            niche = "Crypto"
        else:
            print(f"No scheduled task for UTC hour {current_hour}. Defaulting to Crypto for testing.")
            niche = "Crypto"
            
    print(f"Running pipeline for: {niche}")
    try:
        run_pipeline(niche)
        print(f"Pipeline for {niche} finished successfully on GitHub Actions.")
    except Exception as e:
        print(f"Pipeline crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
