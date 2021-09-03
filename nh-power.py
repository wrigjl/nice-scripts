import nicehash
import requests
import json

def compute_power(rigs):
    power = 0.0
    for rig in rigs['miningRigs']:
        for dev in rig['devices']:
            power += float(dev['powerUsage'])
    return power

if __name__ == "__main__":
    nhauth = nicehash.NiceHashAuth(fname="nicehash.json")
    nicehash.checkNHTime()
    r = requests.get('https://api2.nicehash.com/main/api/v2/mining/rigs2', params={'path': 'op'}, auth=nhauth)
    print(compute_power(r.json()))
