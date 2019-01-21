#!/usr/bin/python
import config
from test import Test
from rest import REST
import sys
from eth_connection import EthConnection
from events_cache import EventCache
from registries_cache import RegistriesCache
from geo_service_registry import GeoServiceRegistry
from settings import Settings

if __name__ == "__main__":
    if "TEST" in config.COMMAND_ARGS:
        test = Test()
        test.test()
        # test.test_events_cache()
        test.test_registries_cache()
    elif "REST" in config.COMMAND_ARGS:
        rest = REST()
        rest.launch()
    elif "CLEAR" in sys.argv:
        eth_connection = EthConnection(config.WEB3_PROVIDER, config.MNEMONIC, config.DB_URL)
        settings = Settings(config.DB_URL)
        gsr = GeoServiceRegistry(eth_connection, config.GEOSERVICEREGISTRY_ADDRESS)
        event_cache = EventCache(
            eth_connection,
            gsr,
            config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK,
            config.DB_URL,
            config.CONFIRMATION_COUNT,
            settings)
        registries_cache = RegistriesCache(event_cache, config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK, config.DB_URL,
                                           config.INTERVAL_FOR_PREPROCESSED_BLOCKS, settings,
                                           config.VOTES_ROUND_TO_NUMBER_OF_DIGIT)
        event_cache.erase_all(0)
        registries_cache.erase(0)
        eth_connection.erase()
    else:
        print("in config.COMMAND_ARGS: TEST - for testing")
        print("in config.COMMAND_ARGS: REST - launch REST API service")
        print("in cmd line: CLEAR - erase db")
