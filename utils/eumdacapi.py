import re
import urllib.parse
from contextlib import contextmanager

import requests
from eumdac import AccessToken
from iso8601 import parse_date


class EumdacApi(object):

    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        self.api_url = "https://api.eumetsat.int"

        self.token = None

        self.set_token()

    def get_auth_headers(self):
        access_token = self.token.access_token
        return {"Authorization": f"Bearer {access_token}"}

    def set_token(self):
        credentials = (self.consumer_key, self.consumer_secret)
        self.token = AccessToken(credentials)

    def search_collection(self, collection, start_date, end_date):
        url = f"{self.api_url}/data/search-products/1.0.0/os"

        params = {
            "pi": collection,
            "si": 0,
            "c": 100,
            "sort": "start,time,0",
            "dtstart": start_date,
            "dtend": end_date,
            "format": "json"
        }

        r = requests.get(url=url, params=params, auth=self.token.auth)

        r.raise_for_status()

        response = r.json()

        features = response["features"]

        products = []

        for product in features:
            props = product["properties"]

            data_dt = parse_date(props["date"].split("/")[0])

            data_dt = data_dt.replace(second=0).strftime('%Y-%m-%dT%H:%M:%SZ')

            p = {
                "identifier": props["identifier"],
                "date": parse_date(data_dt)
            }

            products.append(p)

        return products

    @property
    def _extract_filename(self):
        return re.compile(r'filename="(.*?)"')

    @contextmanager
    def open(self, collection, data_identifier):
        enc_collection = urllib.parse.quote(collection)

        url = f"https://api.eumetsat.int/data/download/1.0.0/collections/{enc_collection}/products/{data_identifier}"

        with requests.get(url=url, auth=self.token.auth, stream=True) as r:
            r.raise_for_status()
            match = self._extract_filename.search(r.headers["Content-Disposition"])

            filename = match.group(1)  # type: ignore[union-attr]
            r.raw.name = filename
            r.raw.decode_content = True
            yield r.raw
