import logging
from unittest import TestCase
from unittest.mock import MagicMock

from redis import Redis

from infrastructure.redis.redis_repository import RedisRepository
from main import get_env_value


class TestRedisRepository(TestCase):
    app: Redis
    repo: RedisRepository
    logger: MagicMock

    @classmethod
    def setUpClass(cls) -> None:
        cls.logger = MagicMock()
        cls.logger.setLevel(logging.DEBUG)
        redis_host = get_env_value("REDIS_HOST")
        redis_port = int(get_env_value("REDIS_PORT"))
        redis_password = get_env_value("REDIS_PASSWORD")
        redis_db = int(get_env_value("REDIS_DB"))

        redis_client = Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=redis_db,
            decode_responses=True,
        )

        cls.repo = RedisRepository(redis_client=redis_client, logger=cls.logger)

    def test_health_check_success(self) -> None:
        self.assertTrue(self.repo.health_check())

    def test_health_check_fail(self) -> None:
        bad_redis_client = Redis(
            host="localhost",
            port=9999,
            decode_responses=True,
        )
        redis_repo = RedisRepository(redis_client=bad_redis_client, logger=self.logger)
        self.assertFalse(redis_repo.health_check())
