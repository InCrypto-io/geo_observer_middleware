import json


class GEOToken:

    def __init__(self, connection, address):
        self.connection = connection

        interface_file = open("./abi/GEOToken.json", "r")
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

    def transfer_from(self, sender, receiver, value):
        raw_transaction = self.contract.functions.transferFrom(sender, receiver, value) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def transfer(self, receiver, value):
        raw_transaction = self.contract.functions.transfer(receiver, value) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def total_supply(self):
        return self.contract.functions.totalSupply().call()

    def set_individual_lockup_expire_time(self, who, time):
        raw_transaction = self.contract.functions.setIndividualLockupExpireTime(who, time) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def deny_transfer_in_lockup_period(self, who):
        raw_transaction = self.contract.functions.denyTransferInLockupPeriod(who) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def allow_transfer_in_lockup_period(self, who):
        raw_transaction = self.contract.functions.allowTransferInLockupPeriod(who) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def is_lockup_expired(self, _who):
        return self.contract.functions.isLockupExpired(_who).call()

    def increase_allowance(self, spender, added_value):
        raw_transaction = self.contract.functions.increaseAllowance(spender, added_value) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def decrease_allowance(self, spender, subtracted_value):
        raw_transaction = self.contract.functions.decreaseAllowance(spender, subtracted_value) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def burn(self, account, value):
        raw_transaction = self.contract.functions.burn(account, value) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def mint(self, account, value):
        raw_transaction = self.contract.functions.mint(account, value) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def balance_of(self, owner):
        return self.contract.functions.balanceOf(owner).call()

    def approve(self, spender, value):
        raw_transaction = self.contract.functions.approve(spender, value) \
            .buildTransaction({'from': self.address, 'gas': 100000, 'nonce': self.connection.get_nonce(self.address),
                               'gasPrice': self.connection.get_gas_price()})
        return self.connection.sign_and_send_transaction(self.address, raw_transaction)

    def allowance(self, owner, spender):
        return self.contract.functions.allowance(owner, spender).call()
