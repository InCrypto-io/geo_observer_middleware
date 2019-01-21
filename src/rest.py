from aiohttp import web
import config
from eth_connection import EthConnection
from geo_service_registry import GeoServiceRegistry
from geo_token import GEOToken
from events_cache import EventCache
import time
from registries_cache import RegistriesCache
from settings import Settings
from threading import Thread
import json
from hexbytes import HexBytes


class HexJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, HexBytes):
            return obj.hex()
        return super().default(obj)


class REST:
    def __init__(self):
        self.eth_connection = EthConnection(config.WEB3_PROVIDER, config.MNEMONIC, config.DB_URL)

        self.gsr = GeoServiceRegistry(self.eth_connection, config.GEOSERVICEREGISTRY_ADDRESS)
        self.geo = GEOToken(self.eth_connection, config.GEOTOKEN_ADDRESS)

        settings = Settings(config.DB_URL)

        self.event_cache = EventCache(
            self.eth_connection,
            self.gsr,
            config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK,
            config.DB_URL,
            config.CONFIRMATION_COUNT,
            settings)

        self.registries_cache = RegistriesCache(self.event_cache, config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK,
                                                config.DB_URL,
                                                config.INTERVAL_FOR_PREPROCESSED_BLOCKS, settings,
                                                config.VOTES_ROUND_TO_NUMBER_OF_DIGIT)

        self.allow_process_events = False

    def get_first_block_number(self, request):
        text = str(config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK)
        return web.Response(text=text)

    def get_current_block_number(self, request):
        text = str(self.registries_cache.get_current_preprocessed_block_number())
        return web.Response(text=text)

    def get_registries(self, request):
        if "blockNumber" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            block_number = int(request.rel_url.query["blockNumber"])
            if block_number < config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK \
                    or block_number > self.registries_cache.get_current_preprocessed_block_number():
                return web.Response(status=404)
            text = json.dumps({
                "registries": self.registries_cache.get_registry_list(block_number),
                "blockNumber": block_number
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)

    def is_registry_exist(self, request):
        if "registryName" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "blockNumber" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            registry_name = str(request.rel_url.query["registryName"])
            block_number = int(request.rel_url.query["blockNumber"])
            if block_number < config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK \
                    or block_number > self.registries_cache.get_current_preprocessed_block_number():
                return web.Response(status=404)
            text = json.dumps({
                "registry": registry_name,
                "exist": self.registries_cache.is_registry_exist(registry_name, block_number),
                "blockNumber": block_number
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)

    def get_winners_list(self, request):
        if "registryName" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "blockNumber" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            registry_name = str(request.rel_url.query["registryName"])
            block_number = int(request.rel_url.query["blockNumber"])
            if block_number < config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK \
                    or block_number > self.registries_cache.get_current_preprocessed_block_number():
                return web.Response(status=404)
            text = json.dumps({
                "registry": registry_name,
                "winners": self.registries_cache.get_winners_list(registry_name, block_number),
                "blockNumber": block_number
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)

    def get_vote_for_candidate(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "registryName" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "blockNumber" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            address = str(request.rel_url.query["address"])
            registry_name = str(request.rel_url.query["registryName"])
            block_number = int(request.rel_url.query["blockNumber"])
            if block_number < config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK \
                    or block_number > self.registries_cache.get_current_preprocessed_block_number():
                return web.Response(status=404)
            text = json.dumps({
                "registry": registry_name,
                "address": address,
                "tokens": self.registries_cache.get_total_votes_for_candidate(address, registry_name, block_number),
                "blockNumber": block_number
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)

    def get_weight(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "blockNumber" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            address = str(request.rel_url.query["address"])
            block_number = int(request.rel_url.query["blockNumber"])
            if block_number < config.GEOSERVICEREGISTRY_CREATED_AT_BLOCK \
                    or block_number > self.registries_cache.get_current_preprocessed_block_number():
                return web.Response(status=404)
            text = json.dumps({
                "address": address,
                "weight": self.registries_cache.get_weight(address, block_number),
                "blockNumber": block_number
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)

    def get_gas_price(self, request):
        text = str(self.eth_connection.get_gas_price())
        return web.Response(text=text)

    def get_ethereum_accounts(self, request):
        text = json.dumps({
            "addresses": self.eth_connection.get_accounts()
        })
        return web.Response(text=text)

    def get_transaction_info(self, request):
        if "hash" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            hash = str(request.rel_url.query["hash"])
            text = json.dumps(dict(self.eth_connection.get_transaction_info(hash)), cls=HexJsonEncoder)
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)

    def resend(self, request):
        if "hash" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            hash = str(request.rel_url.query["hash"])
            if "gasPrice" not in request.rel_url.query.keys():
                gas_price = 0
            else:
                gas_price = str(request.rel_url.query["gasPrice"])
            # if old transaction not found newHash will be empty
            text = json.dumps({
                "oldHash": hash,
                "newHash": self.eth_connection.resend(hash, gas_price)
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def process_events(self):
        while self.allow_process_events:
            self.registries_cache.update()
            self.registries_cache.update_current_block()
            time.sleep(1)

    def gsr_withdraw(self, request):
        if "amount" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.gsr.set_sender(str(request.rel_url.query["sender"]))
            amount = int(request.rel_url.query["amount"])
            text = str(self.gsr.withdraw(amount).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def gsr_vote_service_lockup_for_new_registry(self, request):
        if "registryName" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.gsr.set_sender(str(request.rel_url.query["sender"]))
            registry_name = str(request.rel_url.query["registryName"])
            text = str(self.gsr.vote_service_lockup_for_new_registry(registry_name).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    async def gsr_vote_service_lockup(self, request):
        data = await request.post()
        if "registryName" not in data.keys():
            return web.Response(status=400)
        if "list" not in data.keys():
            return web.Response(status=400)
        try:
            if "sender" in data.keys():
                self.gsr.set_sender(str(data["sender"]))
            registry_name = str(data["registryName"])
            candidates = []
            amounts = []
            array = json.loads(str(data["list"]))
            for key in array.keys():
                candidates.append(key)
                amounts.append(int(array[key]))
            text = str(self.gsr.vote_service_lockup(registry_name, candidates, amounts).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def gsr_vote_service_for_new_registry(self, request):
        if "registryName" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.gsr.set_sender(str(request.rel_url.query["sender"]))
            registry_name = str(request.rel_url.query["registryName"])
            text = str(self.gsr.vote_service_for_new_registry(registry_name).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    async def gsr_vote_service(self, request):
        data = await request.post()
        if "registryName" not in data.keys():
            return web.Response(status=400)
        if "list" not in data.keys():
            return web.Response(status=400)
        try:
            if "sender" in data.keys():
                self.gsr.set_sender(str(data["sender"]))
            registry_name = str(data["registryName"])
            candidates = []
            amounts = []
            array = json.loads(str(data["list"]))
            for key in array.keys():
                candidates.append(key)
                amounts.append(int(array[key]))
            text = str(self.gsr.vote_service(registry_name, candidates, amounts).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def gsr_set_vote_weight_in_lockup_period(self, request):
        if "newAmount" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.gsr.set_sender(str(request.rel_url.query["sender"]))
            new_amount = int(request.rel_url.query["newAmount"])
            text = str(self.gsr.set_vote_weight_in_lockup_period(new_amount).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def gsr_make_deposit(self, request):
        if "additionAmount" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.gsr.set_sender(str(request.rel_url.query["sender"]))
            addition_amount = int(request.rel_url.query["additionAmount"])
            text = str(self.gsr.make_deposit(addition_amount).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def gsr_is_registry_exist(self, request):
        if "registryName" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            registry_name = str(request.rel_url.query["registryName"])
            text = json.dumps({
                "registry": registry_name,
                "exist": self.gsr.is_registry_exist(registry_name)
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def gsr_deposit(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            address = str(request.rel_url.query["address"])
            text = json.dumps({
                "address": address,
                "deposit": self.gsr.deposit(address)
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_allow_transfer_in_lockup_period(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            address = str(request.rel_url.query["address"])
            text = str(self.geo.allow_transfer_in_lockup_period(address).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_allowance(self, request):
        if "ownerAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "spenderAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            owner_address = str(request.rel_url.query["ownerAddress"])
            spender_address = str(request.rel_url.query["spenderAddress"])
            text = json.dumps({
                "ownerAddress": owner_address,
                "spenderAddress": spender_address,
                "allowance": self.geo.allowance(owner_address, spender_address)
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_approve(self, request):
        if "spenderAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "value" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            spender = str(request.rel_url.query["spenderAddress"])
            value = int(request.rel_url.query["value"])
            text = str(self.geo.approve(spender, value).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_balance_of(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            address = str(request.rel_url.query["address"])
            text = json.dumps({
                "address": address,
                "balance": self.geo.balance_of(address)
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_burn(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "value" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            address = str(request.rel_url.query["address"])
            value = int(request.rel_url.query["value"])
            text = str(self.geo.burn(address, value).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_decrease_allowance(self, request):
        if "spenderAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "subtractedValue" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            spender = str(request.rel_url.query["spenderAddress"])
            subtracted_value = int(request.rel_url.query["subtractedValue"])
            text = str(self.geo.decrease_allowance(spender, subtracted_value).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_deny_transfer_in_lockup_period(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            address = str(request.rel_url.query["address"])
            text = str(self.geo.deny_transfer_in_lockup_period(address).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_increase_allowance(self, request):
        if "spenderAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "addedValue" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            spender = str(request.rel_url.query["spenderAddress"])
            added_value = int(request.rel_url.query["addedValue"])
            text = str(self.geo.increase_allowance(spender, added_value).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_is_lockup_expired(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            address = str(request.rel_url.query["address"])
            text = json.dumps({
                "address": address,
                "expired": self.geo.is_lockup_expired(address)
            })
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_mint(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "value" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            address = str(request.rel_url.query["address"])
            value = int(request.rel_url.query["value"])
            text = str(self.geo.mint(address, value).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_set_individual_lockup_expire_time(self, request):
        if "address" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "time" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            address = str(request.rel_url.query["address"])
            expired_time = int(request.rel_url.query["time"])
            text = str(self.geo.set_individual_lockup_expire_time(address, expired_time).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_total_supply(self, request):
        try:
            text = str(self.geo.total_supply())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_transfer(self, request):
        if "receiverAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "value" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            receiver = str(request.rel_url.query["receiverAddress"])
            value = int(request.rel_url.query["value"])
            text = str(self.geo.transfer(receiver, value).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def token_transfer_from(self, request):
        if "transferFromAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "receiverAddress" not in request.rel_url.query.keys():
            return web.Response(status=400)
        if "value" not in request.rel_url.query.keys():
            return web.Response(status=400)
        try:
            if "sender" in request.rel_url.query.keys():
                self.geo.set_sender(str(request.rel_url.query["sender"]))
            sender = str(request.rel_url.query["transferFromAddress"])
            receiver = str(request.rel_url.query["receiverAddress"])
            value = int(request.rel_url.query["value"])
            text = str(self.geo.transfer_from(sender, receiver, value).hex())
            return web.Response(text=text)
        except ValueError:
            return web.Response(status=400)
        except AssertionError:
            return web.Response(status=406)

    def launch(self):
        app = web.Application()
        app.add_routes([web.get('/blocks/firstBlock', self.get_first_block_number),
                        web.get('/blocks/currentBlock', self.get_current_block_number),

                        web.get('/registries/list', self.get_registries),
                        web.get('/registries/exist', self.is_registry_exist),

                        web.get('/votes/list', self.get_winners_list),
                        web.get('/votes/candidate', self.get_vote_for_candidate),

                        web.get('/weight', self.get_weight),

                        web.get('/eth/gasPrice', self.get_gas_price),
                        web.get('/eth/accounts', self.get_ethereum_accounts),
                        web.get('/eth/transaction_info', self.get_transaction_info),
                        web.get('/eth/resend', self.resend),

                        web.get('/gsr/registry/exist', self.gsr_is_registry_exist),
                        web.get('/gsr/registry/vote', self.gsr_vote_service_for_new_registry),
                        web.post('/gsr/vote', self.gsr_vote_service),
                        web.post('/gsr/lockupPeriod/vote', self.gsr_vote_service_lockup),
                        web.get('/gsr/lockupPeriod/registry/vote', self.gsr_vote_service_lockup_for_new_registry),
                        web.get('/gsr/lockupPeriod/weight/set', self.gsr_set_vote_weight_in_lockup_period),
                        web.get('/gsr/weight/makeDeposit', self.gsr_make_deposit),
                        web.get('/gsr/weight/withdraw', self.gsr_withdraw),
                        web.get('/gsr/weight/size', self.gsr_deposit),

                        web.get('/token/lockupPeriod/allow', self.token_allow_transfer_in_lockup_period),
                        web.get('/token/lockupPeriod/deny', self.token_deny_transfer_in_lockup_period),
                        web.get('/token/lockupPeriod/expired', self.token_is_lockup_expired),
                        web.get('/token/lockupPeriod/set', self.token_set_individual_lockup_expire_time),
                        web.get('/token/allowance', self.token_allowance),
                        web.get('/token/allowance/decrease', self.token_decrease_allowance),
                        web.get('/token/allowance/increase', self.token_increase_allowance),
                        web.get('/token/approve', self.token_approve),
                        web.get('/token/balance', self.token_balance_of),
                        web.get('/token/burn', self.token_burn),
                        web.get('/token/mint', self.token_mint),
                        web.get('/token/totalSupply', self.token_total_supply),
                        web.get('/token/transfer', self.token_transfer),
                        web.get('/token/transferFrom', self.token_transfer_from),
                        ])

        self.allow_process_events = True
        self.event_cache.collect()

        worker = Thread(target=self.process_events, daemon=True)
        worker.start()

        web.run_app(app)

        self.allow_process_events = False
        self.event_cache.stop_collect()

        while worker.is_alive():
            time.sleep(1)
