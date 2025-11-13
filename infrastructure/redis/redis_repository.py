import logging
from redis import Redis, RedisError


class RedisRepository:
    def __init__(self, redis_client: Redis, logger: logging.Logger):
        self.redis_client = redis_client
        self.logger = logger

    def health_check(self) -> bool:
        try:
            self.redis_client.ping()
            return True
        except RedisError as error:
            self.logger.error(error, exc_info=True)
            return False
