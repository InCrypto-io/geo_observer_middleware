import pymongo
from pymongo import MongoClient


class RegistriesCache:
    def __init__(self, event_cache, voting_created_at_block, db_url, interval_of_epoch, settings,
                 votes_round_to_number_of_digit, voting_creation_timestamp):
        self.event_cache = event_cache
        self.voting_created_at_block = voting_created_at_block
        self.settings = settings
        self.votes_round_to_number_of_digit = votes_round_to_number_of_digit
        self.voting_creation_timestamp = voting_creation_timestamp
        self.interval_of_epoch = interval_of_epoch
        self.voting_created_at_block = voting_created_at_block

        self.collection_name_prefix = "registry_"

        self.client = MongoClient(db_url)
        self.db = self.client['db_geo_registries']

    def update(self):
        try:
            available_block_timestamp = self.event_cache.get_timestamp_for_block_number(
                self.event_cache.get_last_processed_block_number())
        except KeyError:
            available_block_timestamp = 0

        while self.get_last_preprocessed_block_number() < self.event_cache.get_last_processed_block_number():
            last_epoch = self.get_last_preprocessed_epoch_number()
            next_epoch = last_epoch + 1
            new_epoch_start_time = self.get_time_of_start_epoch(next_epoch)
            if new_epoch_start_time > available_block_timestamp:
                break
            try:
                new_last_block = self.get_number_of_first_block_for_epoch(next_epoch) - 1
            except (AssertionError, KeyError):
                break
            assert self.get_last_preprocessed_block_number() < new_last_block
            self.__preprocess_block(new_last_block)
            self.__set_last_preprocessed_block_number(new_last_block)
            self.__set_last_preprocessed_epoch_number(next_epoch)

    def __preprocess_block(self, block_number, save_to_db=True):
        print("__preprocess_block", block_number)
        assert block_number >= self.voting_created_at_block

        previous_block = self.__determine_previous_preprocessed_block(block_number)

        # reg name -> voter -> candidate -> amount in percent
        votes = {}
        # voter -> amount
        weights = {}
        # names
        registries = []
        # reg name -> sorted array -> [candidate, total tokens]
        winners = {}

        if previous_block > self.voting_created_at_block:
            self.__load_from_db(votes, weights, registries, winners, previous_block)

        if previous_block == block_number:
            return votes, weights, registries, winners

        winners = {}
        self.__apply_events(votes, weights, registries, winners, previous_block, block_number)

        if save_to_db:
            self.__save_to_db(votes, weights, registries, winners, block_number)

        return votes, weights, registries, winners

    def __load_from_db(self, votes, weights, registries, winners, block_number):
        assert len(votes) == 0
        assert len(weights) == 0
        assert len(registries) == 0
        assert len(winners) == 0
        collection_votes = self.db[self.collection_name_prefix + "votes_" + str(block_number)]
        collection_weights = self.db[self.collection_name_prefix + "weights_" + str(block_number)]
        collection_registries = self.db[self.collection_name_prefix + "registries_" + str(block_number)]
        collection_winners = self.db[self.collection_name_prefix + "winners_" + str(block_number)]

        for document in collection_registries.find():
            registries.append(document["name"])
            votes[document["name"]] = {}
            winners[document["name"]] = []

        for document in collection_votes.find():
            if document["voter"] not in votes[document["registry_name"]].keys():
                votes[document["registry_name"]][document["voter"]] = {}
            votes[document["registry_name"]][document["voter"]][document["candidate"]] = document["percentage_amount"]

        for document in collection_weights.find():
            weights[document["voter"]] = document["amount"]

        for document in collection_winners.find().sort([("position", pymongo.ASCENDING)]):
            winners[document["registry_name"]].append([document["candidate"], document["amount"]])

    def __save_to_db(self, votes, weights, registries, winners, block_number):
        collection_votes = self.db[self.collection_name_prefix + "votes_" + str(block_number)]
        collection_weights = self.db[self.collection_name_prefix + "weights_" + str(block_number)]
        collection_registries = self.db[self.collection_name_prefix + "registries_" + str(block_number)]
        collection_winners = self.db[self.collection_name_prefix + "winners_" + str(block_number)]

        if collection_votes.find({}).count():
            collection_votes.remove({})
        if collection_weights.find({}).count():
            collection_weights.remove({})
        if collection_registries.find({}).count():
            collection_registries.remove({})
        if collection_winners.find({}).count():
            collection_winners.remove({})

        for reg_name in votes.keys():
            for voter in votes[reg_name].keys():
                for candidate in votes[reg_name][voter].keys():
                    collection_votes.insert_one({
                        "registry_name": reg_name,
                        "voter": voter,
                        "candidate": candidate,
                        "percentage_amount": votes[reg_name][voter][candidate]
                    })

        for voter in weights.keys():
            collection_weights.insert_one({
                "voter": voter,
                "amount": weights[voter]
            })

        for reg_name in registries:
            collection_registries.insert_one({
                "name": reg_name
            })

        for reg_name in winners.keys():
            for i in range(0, len(winners[reg_name])):
                collection_winners.insert_one({
                    "registry_name": reg_name,
                    "candidate": winners[reg_name][i][0],
                    "amount": winners[reg_name][i][1],
                    "position": i
                })

    def __remove_dbs_for_block_number(self, block_number):
        self.client.drop_database(self.collection_name_prefix + "votes_" + str(block_number))
        self.client.drop_database(self.collection_name_prefix + "weights_" + str(block_number))
        self.client.drop_database(self.collection_name_prefix + "registries_" + str(block_number))
        self.client.drop_database(self.collection_name_prefix + "winners_" + str(block_number))

    def __apply_events(self, votes, weights, registries, winners, from_block_number, to_block_number):
        assert len(winners) == 0
        events = self.event_cache.get_events_in_range(from_block_number, to_block_number)

        for event in events:
            if event["event"] == "Deposit" or event["event"] == "Withdrawal":
                if event["event"] == "Deposit":
                    weights[event["_voter"]] = event["_fullSize"]
                elif event["event"] == "Withdrawal":
                    weights[event["_voter"]] = weights[event["_voter"]] - event["_amountWithdraw"]
                    assert weights[event["_voter"]] >= 0
                if weights[event["_voter"]] == 0:
                    for reg_name in registries:
                        if event["_voter"] in votes[reg_name].keys():
                            del votes[reg_name][event["_voter"]]
            elif event["event"] == "Vote":
                votes[event["_name"]][event["_voter"]] = {}
                for i in range(0, len(event["_candidates"])):
                    votes[event["_name"]][event["_voter"]][event["_candidates"][i]] = event["_amounts"][i]
            elif event["event"] == "NewRegistry":
                if event["_name"] not in registries:
                    registries.append(event["_name"])
                    votes[event["_name"]] = {}

        # reg name -> candidate -> total tokens
        participants = {}

        for reg_name in registries:
            participants[reg_name] = {}
            for voter in votes[reg_name].keys():
                for candidate in votes[reg_name][voter].keys():
                    if candidate not in participants[reg_name].keys():
                        participants[reg_name][candidate] = 0
                    weight_in_tokens = round(votes[reg_name][voter][candidate] * weights[voter] / 10000,
                                             self.votes_round_to_number_of_digit)
                    participants[reg_name][candidate] = participants[reg_name][candidate] + weight_in_tokens

        for reg_name in registries:
            winners[reg_name] = []
            for candidate in participants[reg_name].keys():
                winners[reg_name].append([candidate, participants[reg_name][candidate]])
            winners[reg_name].sort(key=lambda candidate_and_total: candidate_and_total[1], reverse=True)

        for reg_name in winners.keys():
            winners[reg_name] = list(filter(lambda item: item[1] > 0, winners[reg_name]))

    def erase(self, block_number=0):
        if block_number == 0:
            block_number = self.voting_created_at_block
        if block_number > self.get_last_preprocessed_block_number():
            return

        while block_number <= self.get_last_preprocessed_block_number():
            self.__remove_dbs_for_block_number(self.get_last_preprocessed_block_number())
            self.__set_last_preprocessed_block_number(self.get_last_preprocessed_block_number()
                                                      - self.interval_of_epoch)

    def is_registry_exist(self, registry_name, block_number):
        if block_number > self.get_last_preprocessed_block_number():
            return False
        prepared_block_data = self.__preprocess_block(block_number, False)
        return registry_name in prepared_block_data[2]

    def get_registry_list(self, block_number):
        if block_number > self.get_last_preprocessed_block_number():
            return []
        prepared_block_data = self.__preprocess_block(block_number, False)
        return prepared_block_data[2]

    def get_total_votes_for_candidate(self, candidate_address, registry_name, block_number):
        if block_number > self.get_last_preprocessed_block_number():
            return 0
        winners = self.get_winners_list(registry_name, block_number)
        if len(winners):
            for candidate in winners:
                if candidate[0] == candidate_address:
                    return candidate[1]
        return 0

    def get_winners_list(self, registry_name, block_number):
        if block_number > self.get_last_preprocessed_block_number():
            return []
        prepared_block_data = self.__preprocess_block(block_number, False)
        if registry_name in prepared_block_data[3].keys():
            return prepared_block_data[3][registry_name]
        return []

    def get_weight(self, voter, block_number):
        if block_number > self.get_last_preprocessed_block_number():
            return []
        prepared_block_data = self.__preprocess_block(block_number, False)
        if voter in prepared_block_data[1].keys():
            return prepared_block_data[1][voter]
        return 0

    def __determine_previous_preprocessed_block(self, block_number):
        try:
            epoch_number = self.get_epoch_number_for_block_number(block_number)
            if epoch_number < self.get_last_preprocessed_epoch_number():
                end_of_epoch = self.get_number_of_first_block_for_epoch(epoch_number + 1) - 1
                if block_number == end_of_epoch:
                    return block_number
            return self.get_last_block_number_of_previous_epoch(block_number)
        except AssertionError:
            return self.voting_created_at_block

    def get_last_preprocessed_block_number(self):
        result = self.settings.get_value("last_preprocessed_block_number")
        if not result:
            result = self.voting_created_at_block
        return result

    def __set_last_preprocessed_block_number(self, value):
        self.settings.set_value("last_preprocessed_block_number", value)

    def get_last_preprocessed_epoch_number(self):
        result = self.settings.get_value("last_preprocessed_epoch_number")
        if not result:
            result = 0
        return result

    def __set_last_preprocessed_epoch_number(self, value):
        self.settings.set_value("last_preprocessed_epoch_number", value)

    def get_time_of_start_epoch(self, epoch_number):
        return self.voting_creation_timestamp + epoch_number * self.interval_of_epoch

    def get_number_of_first_block_for_epoch(self, epoch_number):
        time_stamp = self.get_time_of_start_epoch(epoch_number)
        return self.event_cache.get_first_block_number_after_timestamp(time_stamp)

    def get_epoch_number_for_block_number(self, block_number):
        assert self.voting_created_at_block <= block_number, "block number less creation block number"
        assert self.get_last_preprocessed_block_number() >= block_number, "block number not processed"
        time_stamp = self.event_cache.get_timestamp_for_block_number(block_number)
        return (time_stamp - self.voting_creation_timestamp) // self.interval_of_epoch

    def get_last_block_number_of_previous_epoch(self, block_number):
        epoch_number = self.get_epoch_number_for_block_number(block_number)
        return self.get_number_of_first_block_for_epoch(epoch_number) - 1
