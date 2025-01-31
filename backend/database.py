import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def save_message(session_id, message):
    redis_client.lpush(session_id, message)

def get_chat_history(session_id, limit=10):
    return redis_client.lrange(session_id, 0, limit - 1)

def setup_database():
    print("Redis Connected!")
