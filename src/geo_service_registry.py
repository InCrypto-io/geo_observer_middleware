import json


class GeoServiceRegistry:

    def __init__(self, connection, address):
        self.connection = connection

        interface_file = open("./abi/GSR.json", "r")
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

    def set_sender(self, address):
        self.address = address

    def create_record(self, name, raw_record):
        raw_transaction = self.contract.functions.createRecord(name, raw_record) \
            .buildTransaction({'from': self.address, 'gas': 1000000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def remove_record(self, name, raw_record):
        raw_transaction = self.contract.functions.removeRecord(name, raw_record) \
            .buildTransaction({'from': self.address, 'gas': 1000000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def get_owner_of_name(self, name):
        return self.contract.functions.getOwnerOfName(name).call()

    def get_raw_record_at(self, name, index):
        return self.contract.functions.getRawRecordAt(name, index).call()

    def get_records_count(self, name):
        return self.contract.functions.getRecordsCount(name).call()

    def is_name_exist(self, name):
        return self.contract.functions.isNameExist(name).call()

