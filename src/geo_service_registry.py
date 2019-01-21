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

    def createRecord(self):
        #(string name,bytes rawRecord)
        pass

    def getOwnerOfName(self):
        #(string name)
        pass

    def getRawRecordAt(self):
        #(string name,uint128 index)
        pass

    def getRecordsCount(self):
        #(string name)
        pass

    def isNameExist(self):
        #(string name)
        pass

    def removeRecord(self):
        #(string name,bytes rawRecord)
        pass

