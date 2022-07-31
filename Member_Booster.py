import httpx
import time
import string
import json
import re
import os
import sys
import random
import threading
import websocket
from itertools import cycle
from names import get_last_name, get_first_name
from capmonster_python import HCaptchaTask
from urllib.request import Request, urlopen
from base64 import b64encode as enc
from colorama import Fore
from pystyle import Colors, Colorate, Center
from timeit import default_timer as timer
from datetime import timedelta

# Intilize some variables
thread_lock = threading.Lock()
accounts_created = 0


class Solve_captcha:
    """Solves captcha and returns captcha key"""

    def __init__(self, url: str, siteKey: str) -> None:
        self.url = url
        self.siteKey = siteKey
        with open("config.json", "r") as config:
            self.config = json.load(config)

    def solve_captcha(self) -> str:
        capmonster = HCaptchaTask(self.config["capmonster_key"])
        task_id = capmonster.create_task(self.url, self.siteKey)
        result = capmonster.join_task_result(task_id)
        response = result.get("gRecaptchaResponse")
        return response


class Others:
    # Gets discord build number
    @staticmethod
    def getClientData():
        client_request = (
            urlopen(
                Request(
                    f"https://discord.com/app",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36"
                    },
                )
            ).read()
        ).decode("utf-8")

        jsFileRegex = re.compile(r"([a-zA-z0-9]+)\.js", re.I)

        asset = jsFileRegex.findall(client_request)[-1]

        assetFileRequest = (
            urlopen(
                Request(
                    f"https://discord.com/assets/{asset}.js",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36"
                    },
                )
            ).read()
        ).decode("utf-8")

        try:
            build_info_regex = re.compile(
                "Build Number: [0-9]+, Version Hash: [A-Za-z0-9]+"
            )
            build_info_strings = (
                build_info_regex.findall(assetFileRequest)[0]
                .replace(" ", "")
                .split(",")
            )
        except (RuntimeError, TypeError, NameError):
            print(RuntimeError or TypeError or NameError)

        build_num = build_info_strings[0].split(":")[-1]

        return build_num

    @staticmethod
    def get_usernames() -> str:
        with open("config.json", "r") as config:
            config = json.load(config)

        random_numbers = (
            " | " + "".join(random.choice(string.digits) for _ in range(5))
            if config["add_numbers"]
            else ""
        )

        if config["custom_username"]:
            random_name = random.choice(
                open("usernames.txt", "r", encoding="utf-8").read().splitlines()
            )
            return f"{random_name}{random_numbers}"
        else:
            return f"{get_first_name()}{random_numbers}"

    @staticmethod
    def get_logins() -> dict:
        password = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(10)
        )

        domains = ["@outlook.com", "@hotmail.com", "@gmail.com"]
        email = (
            f"{get_first_name()}.{get_last_name()}"
            + "".join(random.choice(string.digits) for _ in range(4))
            + random.choice(domains)
        )

        return {"password": password, "email": email}


class Console:
    """Console utils"""

    @staticmethod
    def _time():
        return time.strftime("%H:%M:%S", time.gmtime())

    @staticmethod
    def clear():
        os.system("cls" if os.name == "nt" else "clear")

    # Safe print, to stop overlapping when printing in thread tasks
    @staticmethod
    def sprint(content: str, status: bool = True) -> None:
        thread_lock.acquire()
        sys.stdout.write(
            f"[{Fore.LIGHTBLUE_EX}{Console()._time()}{Fore.RESET}] {Fore.GREEN if status else Fore.RED}{content}"
            + "\n"
            + Fore.RESET
        )
        thread_lock.release()

class Generator:
    """Main genrator, generates an account and joins a server. Accounts becomes phone locked"""

    def __init__(
        self, invite: str, build_num: int = Others().getClientData(), proxy: str = None
    ) -> None:
        self.invite = invite
        self.build_num = build_num
        self.client = httpx.Client(proxies=proxy, timeout=90)
        self.username = Others().get_usernames()

        Other = Others().get_logins()
        self.email, self.password = Other["email"], Other["password"]

    def __main__(self) -> None:
        # Tasks
        try:
            if not self.__session__():
                Console().sprint("Could not create session", False)
                return

            if not self.try_register():
                Console().sprint("Could not try register", False)
                return

            if not self.register():
                Console().sprint("Could not register", False)
                return
            else:
                Console().sprint(f"Created {self.username} ~ {self.token}", True)
                thread_lock.acquire()
                global accounts_created
                accounts_created += 1
                with open("tokens.txt", "a") as tokens:
                    tokens.write(self.token + "\n")
                thread_lock.release()

            self.keep_online()

        except Exception as err:
            Console().sprint(f"Error: {err}", False)

    def __session__(self) -> bool:
        self.client.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36",
                "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
        )

        get_site = self.client.get("https://discord.com/register")

        if not (get_site.status_code in [200, 201, 204]):
            return False

        self.__dcfduid = (
            get_site.headers["set-cookie"].split("__dcfduid=")[1].split(";")[0]
        )
        self.__sdcfduid = (
            get_site.headers["set-cookie"].split("__sdcfduid=")[1].split(";")[0]
        )

        self.client.cookies.update(
            {
                "__dcfduid": self.__dcfduid,
                "__sdcfduid": self.__sdcfduid,
                "locale": "en-US",
            }
        )

        self.super_properties = enc(
            json.dumps(
                {
                    "os": "Windows",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "en-US",
                    "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36",
                    "browser_version": "103.0.5060.66",
                    "os_version": "10",
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "stable",
                    "client_build_number": self.build_num,
                    "client_event_source": None,
                },
                separators=(",", ":"),
            ).encode()
        ).decode()

        self.client.headers.update(
            {
                "X-Context-Properties": "eyJsb2NhdGlvbiI6IlJlZ2lzdGVyIn0=",
                "X-Debug-Options": "bugReporterEnabled",
                "X-Discord-Locale": "en-US",
                "X-Super-Properties": self.super_properties,
            }
        )

        self.client.headers.update(
            {"Host": "discord.com", "Referer": "https://discord.com/register"}
        )

        self.fingerprint = self.client.get("https://discord.com/api/v9/experiments")

        if not (self.fingerprint.status_code in [200, 201, 204]):
            return False

        self.fingerprint = self.fingerprint.json()["fingerprint"]

        self.client.headers["Origin"] = "https://discord.com"

        if not (get_site.status_code in [200, 201, 204]):
            return False

        self.client.headers.update({"X-Fingerprint": self.fingerprint})

        return True

    def try_register(self) -> bool:
        self.dob = (
            str(random.randint(1990, 2002))
            + "-"
            + "{:02d}".format(random.randint(1, 12))
            + "-"
            + "{:02d}".format(random.randint(1, 28))
        )

        payload = {
            "fingerprint": self.fingerprint,
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "invite": self.invite,
            "consent": True,
            "date_of_birth": self.dob,
            "gift_code_sku_id": None,
            "captcha_key": None,
            "promotional_email_opt_in": False,
        }

        register = self.client.post(
            "https://discord.com/api/v9/auth/register", json=payload
        )

        if register.status_code == 400:
            self.siteKey = register.json()["captcha_sitekey"]
            return True
        else:
            return False

    def register(self) -> bool:
        captcha_key = Solve_captcha(
            "http://discord.com/register", self.siteKey
        ).solve_captcha()

        payload = {
            "fingerprint": self.fingerprint,
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "invite": self.invite,
            "consent": True,
            "date_of_birth": self.dob,
            "gift_code_sku_id": None,
            "captcha_key": captcha_key,
            "promotional_email_opt_in": False,
        }

        register = self.client.post(
            "https://discord.com/api/v9/auth/register", json=payload
        )

        if register.status_code in [201, 200, 204]:
            self.token = register.json()["token"]
            return True
        else:
            return False

    # This was made by kek. Thanks
    def keep_online(self):
        ws = websocket.WebSocket()
        ws.connect("wss://gateway.discord.gg/?v=6&encoding=json")
        data = json.loads(ws.recv())
        heartbeat_interval = data["d"]["heartbeat_interval"]
        auth = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "$os": sys.platform,
                    "$browser": "RTB",
                    "$device": f"{sys.platform} Device",
                },
            },
            "s": None,
            "t": None,
        }
        ws.send(json.dumps(auth))
        ack = {"op": 1, "d": None}
        while True:
            time.sleep(heartbeat_interval // 1000)

            try:
                ws.send(json.dumps(ack))
            except:
                break


if __name__ == "__main__":
    Console().clear()

    print(
        Center.XCenter(
            Colorate.Vertical(
                Colors.red_to_purple,
                f"""
                                          /$$$$$$              /$$     /$$
                                         /$$__  $$            | $$    |__/
                                        | $$  \ $$  /$$$$$$  /$$$$$$   /$$
                                        | $$  | $$ /$$__  $$|_  $$_/  | $$
                                        | $$  | $$| $$  \ $$  | $$    | $$
                                        | $$  | $$| $$  | $$  | $$ /$$| $$
                                        |  $$$$$$/| $$$$$$$/  |  $$$$/| $$
                                         \______/ | $$____/    \___/  |__/
                                                  | $$                    
                                                  | $$      Build Number: [{Others().getClientData()}]     
                                                  |__/      Made by ! Aran#9999

    """,
                1,
            )
        )
    )

    proxies = cycle(open("proxies.txt", "r").read().splitlines())
    build_num = Others().getClientData()

    with open("config.json", "r") as config:
        config = json.load(config)

    threads = []
    for _ in range(config["accounts"]):
        try:
            next_proxy = next(proxies)
            proxy = {
                "http://": "http://" + next_proxy,
                "https://": "http://" + next_proxy,
            }
        except:
            proxy = None

        thread = threading.Thread(
            target=Generator(config["invite"], build_num, proxy).__main__
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
