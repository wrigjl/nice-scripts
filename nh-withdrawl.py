
import requests
import nicehash
from decimal import Decimal
import sys
import argparse

# TODO: deal with pagination (currently I assume everything I need is on page 1)

def get_addr_id(addrs, name):
    '''We need an address "id" to start a withdrawal. Iterate over the list of withdrawal addresses
    and see if name matches the 'id', 'name', or 'address' of a whitelisted key. If so, return
    its 'id'.
    '''
    for addr in addrs['list']:
        if addr['status']['code'] != 'ACTIVE':
            continue
        if addr['id'] == name:
            return addr['id']
        if addr['name'] == name:
            return addr['id']
        if addr['address'] == name:
            return addr['id']
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Withdrawal automater')
    parser.add_argument('--keyfile', help='json file with api_key, org_id, api_secret', default="nh-withdrawl.json")
    parser.add_argument('--apikey', help='api key', default=None)
    parser.add_argument('--apisecret', help='api secret (not a good idea to use on command line)', default=None)
    parser.add_argument('--orgid', help='organization id', default=None)
    parser.add_argument('--bypass-minimum', action='store_true',
        help='bypass the minimum balance check and try anyway')
    parser.add_argument('--fee', default=Decimal('0.00000100'),
        help='fee charge for withdrawals')
    parser.add_argument('--minimum', default=Decimal('0.001'),
        help='minimum for a withdrawal (you need fee+minimum to complete this action)')
    parser.add_argument('--amount', default=None,
        help='amount to transfer (default is maximum available)')
    parser.add_argument('--address', default='home',
        help='destination address (can be BTC addr or "name" at NiceHash), must already be whitelisted')
    args = parser.parse_args()

    nhauth = nicehash.NiceHashAuth(fname=args.keyfile, api_key=args.apikey, api_secret=args.apisecret, org_id=args.orgid)
    nicehash.checkNHTime()

    # Where are we sending it?
    addrs = requests.get('https://api2.nicehash.com/main/api/v2/accounting/withdrawalAddresses', params={'currency': 'BTC'}, auth=nhauth).json()
    keyid = get_addr_id(addrs, args.address)
    assert keyid is not None, "no ID found for key, did you whitelist this address already?"

    # Is there enough to proceed?
    withdrawal_fee = Decimal(args.fee)
    minwithdrawal = Decimal(args.minimum)

    if args.amount is not None:
        balance = Decimal(args.amount)
    else:
        balance = requests.get('https://api2.nicehash.com/main/api/v2/accounting/account2/BTC', auth=nhauth).json()
        if not args.bypass_minimum and Decimal(balance['available']) < minwithdrawal:
            print(f"balance too low: {balance['available']} < {minwithdrawal}")
            sys.exit(0)
        balance = Decimal(balance['available'])

    params = {
        'currency': 'BTC',
        'amount': str(balance),
        'withdrawalAddressId': keyid,
    }
    r = requests.post("https://api2.nicehash.com/main/api/v2/accounting/withdrawal", json=params, auth=nhauth)
    print(r)
