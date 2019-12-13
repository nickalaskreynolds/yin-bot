import sys
import subprocess
import datetime
from logging import Formatter, INFO, StreamHandler, getLogger
from time import time, sleep

import asyncio
import gila

from cogs.utils.db_utils import PostgresController

async def get_postgres():
    """
    async method to initialize the pg_utils class
    """
    config = gila.Gila()
    config.set_default("log_level", "INFO")
    config.set_config_file('config/config.yml')
    config.read_config_file()
    config = config.all_config()
    print(config['postgres_credentials'])
    logger = getLogger('migration')
    console_handler = StreamHandler()
    console_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s')
    )
    logger.addHandler(console_handler)
    logger.setLevel(INFO)
    postgres_cred = config['postgres_credentials']
    pg_utils = None
    while not pg_utils:
        try:
            pg_utils = await PostgresController.get_instance(
                logger=logger, connect_kwargs=postgres_cred)
        except Exception as e:
            logger.critical(
                f'Error initializing DB - trying again in 5 seconds')
            logger.debug(f'Error: {e}')
            sleep(5)
    return (pg_utils, config, logger)

async def migrate():
    pg_utils, config, logger = await get_postgres()

    add_table_warnings = f"""
    ALTER TABLE {config['postgres_credentials']['database']}.warnings
        ADD COLUMN modid BIGINT DEFAULT 0;
    """

    add_table_moderation = f"""
    ALTER TABLE {config['postgres_credentials']['database']}.moderation
        ADD COLUMN modid BIGINT DEFAULT 0;
    """
    try:
        await pg_utils.pool.execute(add_table_warnings)
        await pg_utils.pool.execute(add_table_moderation)
    except Exception as e:
        logger.critical("Error doing final migration:")
        logger.critical(e)
    return

def run():
    asyncio.run(migrate())

if __name__ == '__main__':
    run()
