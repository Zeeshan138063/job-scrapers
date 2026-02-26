import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def test_redis():
    try:
        print(f"Connecting to Redis at {REDIS_URL}...")
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        print("Successfully connected to Redis!")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")

if __name__ == "__main__":
    test_redis()
