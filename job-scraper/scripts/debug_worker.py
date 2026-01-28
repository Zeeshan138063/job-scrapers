import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Load environment variables from docker/.env
env_path = os.path.join(project_root, 'docker', '.env')
if os.path.exists(env_path):
    print(f"Loading environment from {env_path}")
    load_dotenv(env_path)
else:
    print(f"Warning: .env file not found at {env_path}")

# Set local debugging overrides
redis_port = os.environ.get('REDIS_PORT', '6379')
os.environ['REDIS_URL'] = f"redis://localhost:{redis_port}"

# Check for placeholder credentials
# if 'your-project' in os.environ.get('SUPABASE_URL', ''):
#     print("WARNING: It looks like you are using placeholder Supabase credentials.")
#     print("Please update docker/.env with your real SUPABASE_URL and SUPABASE_KEY.")


from worker.worker import ScrapingWorker

if __name__ == "__main__":
    print("Starting Worker in Debug Mode...")
    print(f"Redis URL: {os.environ.get('REDIS_URL')}")
    print(f"Supabase URL: {os.environ.get('SUPABASE_URL')}")
    
    worker = ScrapingWorker(os.environ.get('REDIS_URL'))
    
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        print("Worker stopping...")
