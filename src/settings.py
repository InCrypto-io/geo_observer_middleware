from pymongo import MongoClient


class Settings:
    def __init__(self, db_url):
        self.client = MongoClient(db_url)
        self.db = self.client['db_geo_settings']

    def get_value(self, key):
        if self.db["settings"].find_one({"name": key}) is not None:
            return self.db["settings"].find_one({"name": key})["value"]
        return None

    def set_value(self, key, value):
        setting = self.db["settings"].find_one({"name": key})
        if setting is not None:
            setting['value'] = value
            self.db["settings"].save(setting)
        else:
            self.db["settings"].insert_one({
                "name": key,
                "value": value
            })
