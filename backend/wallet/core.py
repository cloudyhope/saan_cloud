from wallet.models import *
import json
from string import Template
from django.utils.translation import gettext_lazy as _

class WalletCore:
    def __init__(self):
        self.keys = [
            {"key":"creator", "type": type(User()), "mandatory": True, "nullable": False}, #TODO type checking
            {"key":"amount", "type": int, "mandatory": True, "nullable": False},
            {"key":"from", "type": str, "mandatory": True, "nullable": True},
            {"key":"to", "type": str, "mandatory": True, "nullable": True},
            {"key":"currency", "type": str, "mandatory": True, "nullable": False},
            {"key":"layer", "type": str, "mandatory": True, "nullable": False},
            {"key":"transaction_type", "type": str, "mandatory": True, "nullable": False},
            {"key":"ref", "type": dict, "mandatory": False, "nullable": False},
            {"key":"description", "type": str, "mandatory": False, "nullable": False},
        ]
        self.mapping = {}
        pass

    def retrieve_queries(self, data: dict) -> None:
        self.amount = data['amount']
        self.from_wallet = Wallet.objects.get(public_address=data['from']) if data['from'] else None
        self.to_wallet = Wallet.objects.get(public_address=data['to']) if data['to'] else None
        self.transaction_type = TransactionType.objects.get(key=data['transaction_type'])
        self.from_currency = Currency.objects.get(abbreviation=data['currency'])
        self.from_layer = Layer.objects.get(key=data['layer'])

    def validate_rules(self, data: dict) -> bool:
        transaction_type = self.transaction_type
        # Amount validation:
        if data['amount'] > transaction_type.max_amount:
            raise ValueError(_("Max amount could be %(max_amount).") % {"max_amount": str(transaction_type.max_amount)})
        if data['amount'] < transaction_type.min_amount:
            raise ValueError(_("Min amount could be %(min_amount).") % {"min_amount": str(transaction_type.min_amount)})
        allowed_transaction_rules = AllowedTransactionRule.objects.filter(from_layer=self.from_layer, transaction_type=transaction_type, wallet_type=self.from_wallet.type if self.from_wallet else None, currency=self.from_currency).exists()
        if not allowed_transaction_rules:
            raise ValueError(_("This type of transaction in this wallet type and it's layer is not permitted!"))
        return True

    def validate_input_data_scheme(self, data: dict) -> bool:
        
        for key in self.keys:
            if key["mandatory"] and key["key"] not in data.keys():
                raise ValueError(_("Key `%(key)` is mandatory and not provided!") % {"key": key["key"]})
            elif not key["mandatory"] and key["key"] in data.keys():
                if type(data[key['key']]) not in [key["type"], type(None), type("")]:
                    raise ValueError(_("Type of optional key `%(key)` didn't matched.") % {"key": key["key"]})
            else:
                print("KEY", key)
                if key['key'] in data.keys():
                    if not type(data[key['key']]) == key["type"]:
                        if key['nullable'] and data[key['key']] is None:
                            continue
                        if key['key'] == "creator":
                            continue
                        raise ValueError(_("Type of mandatory key `%(key)` didn't matched.") % {"key": key["key"]})
        return True

    def get_variable_config(self, the_dict):
        query = VariableConfig.objects.all()
        for q in query:
            the_dict[q.key] = q.value
        return the_dict

    def assemble_transaction(self, data: dict, *args, **kwargs) -> list:
        transaction_type = self.transaction_type
        config = Template(transaction_type.config)
        #  amount - from - currency - layer - to
        # print("amount - from - currency - layer - to", data['amount'], self.from_wallet.id, self.from_currency.id, self.from_layer.id, self.to_wallet.id)
        mapping = {
            "amount":data['amount'], 
            "from_address":self.from_wallet.id if self.from_wallet else None, 
            "currency_id":self.from_currency.id, 
            "layer_id":self.from_layer.id, 
            "to_address":self.to_wallet.id,
            "ref": json.dumps(data['ref']) if 'ref' in data.keys() else None
        }
        mapping = self.get_variable_config(mapping)
        mapping = {**mapping, **kwargs}
        self.mapping = mapping
        formatted_config = config.substitute(**mapping)
        print("formatted_config", formatted_config)
        formatted_config_json = json.loads(formatted_config)
        for i in range(len(formatted_config_json)):
            formatted_config_json[i]['amount'] = int(eval(formatted_config_json[i]['amount']))
        output = {
            "creator": data["creator"],
            "type": transaction_type,
            "description": data["description"] if "description" in data.keys() else None,
            "lines": formatted_config_json
        }
        return output
    
    def check_wallet_ownership(self, data: dict) -> bool:
        if self.from_wallet:
            if data["creator"].is_staff == True:
                return True
            if not Wallet.objects.get(public_address=data["from"]).account.user == data["creator"]:
                raise ValueError(_("Ownership error!"))
        return True

    def validate_sigma_zero(self, transaction):
        sum = 0
        for line in transaction["lines"]:
            sum = sum  + line["amount"]
        return sum == 0
            
    def rest_correction(self, transaction):
        sum = 0
        for line in transaction["lines"]:
            sum = sum + line["amount"]
        if sum != 0 and sum < transaction["type"].max_acceptable_rest_amount:
            lines = transaction["lines"]
            rest_config = Template(transaction["type"].rest_config)
            rest_amount = str(-sum)
            mapping = {**self.mapping, **{"rest_amount": rest_amount}}
            formatted_rest_config = rest_config.substitute(**mapping)
            json_formatted_rest_config = json.loads(formatted_rest_config)
            json_formatted_rest_config['amount'] = int(eval(json_formatted_rest_config['amount']))
            lines.append(json_formatted_rest_config)
            transaction["lines"] = lines
            return transaction
        raise ValueError(_("The rest amount is too much!"))

    def transaction_line_type_check(self, transaction: dict):
        for line in transaction['lines']:
            line['type'] = TransactionLineType.objects.get(id=line['type'])
            if line['type'].indicator * line['amount'] < 0:
                raise ValueError(_("type indicator doesn't match with amount!"))
            if line['type'].has_ref and 'ref' not in line.keys():
                raise ValueError(_("ref is mandatory by transaction line type rules!"))
        return True

    @staticmethod
    def get_balance(wallet, layer, currency, by_wallet_id=True): #TODO add by public_address
        from django.db.models import Sum
        balance = WalletTransactionLine.objects.filter(wallet=wallet, layer=layer, currency=currency, transaction__is_reversed=False).aggregate(Sum('amount'))['amount__sum']
        return balance if balance is not None else 0

    def balance_sufficiency_check(self, from_wallet: object, from_layer: object, from_currency: object, amount: int):
        if from_wallet is None:
            return True
        if amount > self.get_balance(wallet=from_wallet, layer=from_layer, currency=from_currency):
            raise ValueError(_("Insufficient balance!"))
        return True

    def save_transaction_in_db(self, transaction: dict) -> int:
        head = WalletTransaction()
        head.creator = transaction["creator"]
        head.type = transaction['type']
        if 'description' in transaction.keys():
            head.description = transaction['description']
        else:
            head.description = None
        head.save()
        for line in transaction['lines']:
            obj = WalletTransactionLine()
            obj.transaction = head
            obj.wallet = Wallet.objects.get(id=line['wallet']) if line['wallet'] else line['wallet']
            obj.layer = Layer.objects.get(id=line['layer'])
            obj.currency = Currency.objects.get(id=line['currency'])
            obj.type = line['type']
            obj.amount = line['amount']
            if 'ref' in line.keys():
                this_ref = RefTransaction()
                for ref_key in line['ref'].keys():
                    if ref_key == "bank_charge_credit":
                        setattr(this_ref, ref_key, BankCreditCharge.objects.get(id=line['ref'][ref_key]))
                        continue
                    if ref_key == "outer_transaction":
                        setattr(this_ref, ref_key, OuterTransaction.objects.get(id=line['ref'][ref_key]))
                        continue
                    if ref_key == "wallet_invoice":
                        setattr(this_ref, ref_key, WalletInvoice.objects.get(id=line['ref'][ref_key]))
                        continue
                    setattr(this_ref, ref_key, line['ref'][ref_key])
                this_ref.save()
                obj.ref = this_ref
            obj.save()

        return head.id

    def place_transaction(self, data: dict, is_test=False, forced=False, *args, **kwargs) -> tuple:
        """
        data = {
            "creator": User Object; the request.user object,
            "amount": int; amount,
            "from": str; wallet_public_address,
            "to": str; wallet_public_address,
            "currency": str; currency_abbreviation,
            "layer": str; layer_key of from,
            "transaction_type": str; transaction_type_key,
            "description": str; description by user,
            "ref": blank or null or json; real bank transaction data
        }
        """
        self.validate_input_data_scheme(data)
        self.retrieve_queries(data)
        self.validate_rules(data)
        if forced and data['creator'].is_superuser:
            pass
        else:
            self.check_wallet_ownership(data)
        transaction = self.assemble_transaction(data, **kwargs)
        if not self.validate_sigma_zero(transaction):
            transaction = self.rest_correction(transaction)
            if not self.validate_sigma_zero(transaction):
                raise ValueError("Sigma non-Zero Error!")
        self.transaction_line_type_check(transaction)
        if self.from_wallet:
            self.balance_sufficiency_check(self.from_wallet, self.from_layer, self.from_currency, self.amount)
        # Now time to place the transaction!
        if not is_test:
            transaction_id = self.save_transaction_in_db(transaction)
        else:
            transaction_id = 0
        return (False, transaction_id)

    def transaction_validator(self, transaction: dict) -> bool:
        return True

    @staticmethod
    def create_wallet_for_user(user, wallet_type_key, short_address=None):
        # making sure that wallet type exists:
        wallet_types = WalletType.objects.filter(key=wallet_type_key)
        if not wallet_types.exists():
            raise ValueError(_("This Type of Wallet Does Not Exists!"))
        wallet_type = wallet_types.first()
        # making sure that wallet does not already exists:
        wallets = Wallet.objects.filter(account__user=user, type=wallet_type)
        if wallets.exists():
            raise ValueError(_("This Wallet Already Exists!"))
        # make sure that the user has account:
        accounts = Account.objects.filter(user=user)
        if accounts.exists():
            account = accounts[0]
        else:
            account = Account()
            account.user = user
            account.save()
        wallet = Wallet()
        wallet.account = account
        wallet.type = wallet_type
        wallet.short_address = short_address
        wallet.save()
        return wallet

    def create_wallet_for_user_if_not_exists(self, user, wallet_type_key, short_address=None):
        try:
            self.create_wallet_for_user(user, wallet_type_key, short_address)
        except:
            pass
        return True

    def safe_get_wallet(self, user: object, type: str):
        query = Wallet.objects.filter(type__key=type, account__user=user)
        if query.exists():
            return query.first()
        else:
            return self.create_wallet_for_user(user, type)


    @staticmethod
    def check_general_wallet_for_user(user):
        # making sure that wallet type exists:
        wallet_types = WalletType.objects.filter(is_general=True)
        if not wallet_types.exists():
            raise ValueError(_("There is no general wallet type!"))
        wallet_type = wallet_types.first()
        # making sure that wallet does not already exists:
        wallets = Wallet.objects.filter(account__user=user, type=wallet_type)
        if wallets.exists():
            return wallets.first()
        # make sure that the user has account:
        accounts = Account.objects.filter(user=user)
        if accounts.exists():
            account = accounts[0]
        else:
            account = Account()
            account.user = user
            account.save()
        wallet = Wallet()
        wallet.account = account
        wallet.type = wallet_type
        wallet.short_address = None
        wallet.save()
        return wallet


#  amount - from_address - currency - layer_key - to_address

# [{
#     "wallet": "$from_address",
#     "layer": $layer_id,
#     "currency": $currency_id,
#     "type": 1,
#     "amount": "-$amount"
# },
# {
#     "wallet": "$to_address",
#     "layer": $layer_id,
#     "currency": $currency_id,
#     "type": 2,
#     "amount": "$amount"
# }]
    

