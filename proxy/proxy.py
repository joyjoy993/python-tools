from proxybroker import Broker
import asyncio
import random
import requests
from time import time, sleep


class Proxy:
    def __init__(self):
        self.proxies = self.get_valid_proxies()

    def refresh_proxy(self):
        while True:
            self.proxy = self.get_valid_proxies()
            sleep(15 * 60)

    def get_valid_proxies(self):
        proxies = []
        for proxy in self.get_proxy(50):
            proxyDict = {
                "http": 'http://{}'.format(proxy),
            }
            r = requests.get('https://www.google.com/', proxies=proxyDict)
            if r.status_code == 200:
                proxies.append(proxyDict)
        return proxies

    def get_proxy(self, count):
        proxyList = []

        async def show(proxies):
            while True:
                proxy = await proxies.get()
                if proxy is None:
                    break
                proxyList.append('{}:{}'.format(proxy.host, proxy.port))
        proxies = asyncio.Queue()
        broker = Broker(proxies)
        tasks = asyncio.gather(
            broker.find(types=['HTTP'], limit=count),
            show(proxies))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tasks)
        return proxyList


# proxy_generator = Proxy()
# proxy = random.choice(proxy_generator.proxies)
# response = requests.post('url', proxies=proxy)
