
import json
import hmac
import hashlib
import requests
import datetime
import uuid
from requests.auth import AuthBase

class NiceHashAuth(AuthBase):
    def __init__(self, fname = None, api_secret = None, api_key = None, org_id = None):
        if fname is not None:
            with open(fname) as f:
                keys = json.load(f)
            self.api_secret = keys['api_secret']
            self.api_key = keys['api_key']
            self.org_id = keys['org_id']

        if api_secret is not None:
            self.api_secret = api_secret
        if api_key is not None:
            self.api_key = api_key
        if org_id is not None:
            self.org_id = org_id

        assert self.api_secret is not None
        assert self.api_key is not None
        assert self.org_id is not None

    def make_timestamp(self):
        # current UTC time in ms as a integer expressed as a string
        return str(round(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000.0))

    def make_nonce(self):
        # random long string
        return str(uuid.uuid4())

    def __call__(self, request):
        timestamp = self.make_timestamp()
        nonce = self.make_nonce()
        empty = bytearray('\x00', 'utf-8')

        comps = request.path_url.split('?', 1)
        url = comps[0]
        query = '' if len(comps) == 1 else comps[1]

        body = bytearray(self.api_key, 'utf-8') + empty
        body += bytearray(timestamp, 'utf-8') + empty
        body += bytearray(nonce, 'utf-8') + empty + empty
        body += bytearray(self.org_id, 'utf-8') + empty + empty
        body += bytearray(request.method, 'utf-8') + empty
        body += bytearray(url, 'utf-8') + empty + bytearray(query, 'utf-8')

        if request.body:
            body += empty + request.body

        digest = hmac.new(bytearray(self.api_secret, 'utf-8'), body, hashlib.sha256).hexdigest()

        request.headers.update({
            'X-Time': timestamp,
            'X-Nonce': nonce,
            'X-Organization-Id': self.org_id,
            'X-Auth': f'{self.api_key}:{digest}',
        })

        return request

def checkNHTime():
    '''Check that our clock is within 5 minutes of the nicehash clock (no point in continuing
    it is isn't).'''
    nhtime = float(requests.get('https://api2.nicehash.com/api/v2/time').json()['serverTime'])
    nhtime /= 1000.0
    nhtime = datetime.datetime.fromtimestamp(nhtime, tz=datetime.timezone.utc)
    mytime = datetime.datetime.now(tz=datetime.timezone.utc)
    delta = nhtime - mytime
    assert delta <= datetime.timedelta(minutes=5) and delta >= datetime.timedelta(minutes=-5), \
        f"timedelta is too great: {delta}"
