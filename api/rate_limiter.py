import redis
import time
import os

class RateLimiter:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
        self.default_limit = 10 # req per minute
        self.window = 60 # seconds

    def is_allowed(self, client_id: str, limit: int = None) -> bool:
        """
        Sliding window rate limiter using Redis.
        """
        limit = limit or self.default_limit
        now = time.time()
        key = f"rate_limit:{client_id}"
        
        # Remove old requests
        self.redis.zremrangebyscore(key, 0, now - self.window)
        
        # Count current requests
        request_count = self.redis.zcard(key)
        
        if request_count < limit:
            self.redis.zadd(key, {str(now): now})
            # Set expiry to clean up keys
            self.redis.expire(key, self.window)
            return True
        return False
