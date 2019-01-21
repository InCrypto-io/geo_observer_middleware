import pymongo
from pymongo import MongoClient
import time
from threading import Thread
import concurrent.futures


class EventCache:
    def __init__(self, connection, gsr, gsr_created_at_block, db_url, confirmation_count, settings):
        self.connection = connection
        self.gsr = gsr
        self.confirmation_count = confirmation_count
        self.client = MongoClient(db_url)
        self.db = self.client['db_geo_events']
        self.events_collection = self.db["events"]
        self.check_and_wait_connection_to_db()
        self.events_collection.create_index([
            ("blockNumber", pymongo.ASCENDING),
            ("logIndex", pymongo.ASCENDING)
        ], unique=True)
        self.stop_collect_events = True
        self.settings = settings
        self.gsr_created_at_block = gsr_created_at_block

    def collect(self):
        self.stop_collect_events = False
        worker = Thread(target=self.process_events, daemon=True)
        worker.start()

    def process_events(self):
        new_block_filter = self.connection.get_web3().eth.filter('latest')
        while not self.stop_collect_events:
            try:
                for _ in new_block_filter.get_new_entries():
                    last_block_number = self.connection.get_web3().eth.blockNumber
                    print("exist new block", last_block_number)
                    while self.get_last_processed_block_number() + self.confirmation_count < last_block_number:
                        print("get events for block:", self.get_last_processed_block_number() + 1)
                        for event_name in self.gsr.get_events_list():
                            event_filter = self.gsr.contract.eventFilter(event_name,
                                                                         {'fromBlock': self.get_last_processed_block_number() + 1,
                                                                          'toBlock': self.get_last_processed_block_number() + 1})
                            for event in event_filter.get_all_entries():
                                self.write_event(event)
                            self.connection.get_web3().eth.uninstallFilter(event_filter.filter_id)
                        self.set_last_processed_block_number(self.get_last_processed_block_number() + 1)
                time.sleep(10)
            except concurrent.futures._base.TimeoutError or ValueError:
                new_block_filter = self.connection.get_web3().eth.filter('latest')

        self.connection.get_web3().eth.uninstallFilter(new_block_filter.filter_id)

    def stop_collect(self):
        self.stop_collect_events = True

    def write_event(self, event):
        print("write_event", event)
        for f in ["event", "logIndex", "transactionIndex", "transactionHash", "address", "blockHash", "blockNumber"]:
            if f not in event:
                print("Event not contains expected fields")
                break
        data = {}
        for key in event:
            if key in ["args"]:
                continue
            data[key] = event[key]
        for key in event["args"]:
            data[key] = event["args"][key]
        try:
            self.events_collection.insert_one(data)
        except pymongo.errors.DuplicateKeyError:
            pass

    def erase_all(self, from_block_number=0):
        self.events_collection.remove({"blockNumber": {'$gte': from_block_number}})
        self.set_last_processed_block_number(from_block_number - 1)

    def get_events_count(self):
        return self.events_collection.count()

    def get_event(self, index):
        cursor = self.events_collection.find({}).sort(
            [("blockNumber", pymongo.ASCENDING), ("logIndex", pymongo.ASCENDING)]).skip(index).limit(1)
        if cursor.count():
            return cursor[0]
        return {}

    def get_events_in_range(self, block_start, block_end):
        assert block_start <= block_end
        return self.events_collection.find({"blockNumber": {'$gte': block_start, '$lte': block_end}}).sort(
            [("blockNumber", pymongo.ASCENDING), ("logIndex", pymongo.ASCENDING)])

    def check_and_wait_connection_to_db(self):
        while True:
            try:
                print("Check connection to mongodb server")
                print(self.client.server_info())
                break
            except pymongo.errors.ServerSelectionTimeoutError:
                print("Can't connect to mongodb server")

    def get_last_processed_block_number(self):
        result = self.settings.get_value("last_processed_in_block_number_for_event")
        if not result:
            result = self.gsr_created_at_block - 1
        return result

    def set_last_processed_block_number(self, value):
        self.settings.set_value("last_processed_in_block_number_for_event", value)
