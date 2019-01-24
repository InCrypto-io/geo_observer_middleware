import json


class Voting:

    def __init__(self, connection, address, created_at_block):
        self.connection = connection

        interface_file = open("./abi/Voting.json", "r")
        contract_interface = json.load(interface_file)
        interface_file.close()

        w3 = connection.get_web3()

        self.contract = w3.eth.contract(
            address=address,
            abi=contract_interface['abi'],
        )

        if len(connection.get_accounts()) > 0:
            self.address = connection.get_accounts()[0]
        else:
            self.address = ""

        self.creation_timestamp = self.connection.get_web3().eth.getBlock(created_at_block)["timestamp"]

    def set_sender(self, address):
        self.address = address

    def is_registry_exist(self, registry_name):
        return self.contract.functions.isRegistryExist(registry_name).call()

    def withdraw(self, amount):
        raw_transaction = self.contract.functions.withdraw(amount) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def vote_service_for_new_registry(self, registry_name):
        raw_transaction = self.contract.functions.voteServiceForNewRegistry(registry_name) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def vote_service_lockup_for_new_registry(self, registry_name):
        raw_transaction = self.contract.functions.voteServiceLockupForNewRegistry(registry_name) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def vote_service(self, registry_name, _candidates, _amounts):
        raw_transaction = self.contract.functions.voteService(registry_name, _candidates, _amounts) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def vote_service_lockup(self, registry_name, _candidates, _amounts):
        raw_transaction = self.contract.functions.voteServiceLockup(registry_name, _candidates, _amounts) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def set_vote_weight_in_lockup_period(self, new_amount):
        raw_transaction = self.contract.functions.setVoteWeightInLockupPeriod(new_amount) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def make_deposit(self, addition_amount):
        raw_transaction = self.contract.functions.makeDeposit(addition_amount) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def deposit(self, address):
        return self.contract.functions.deposit(address).call()

    @staticmethod
    def get_events_list():
        return ["Deposit", "NewRegistry", "Vote", "Withdrawal"]
