from ipaddress import ip_address, ip_network
from os import environ
from pathlib import Path
from platform import machine, system
from shlex import split
from shutil import move, which
from socket import AF_UNSPEC, gaierror, getaddrinfo, gethostbyname, gethostname
from subprocess import DEVNULL, CalledProcessError, Popen, run
from sys import exit
from urllib.parse import urlencode

import docker
import orjson
from homegrownai.exceptions import AIAppError
from loguru import logger
from niquests import get
from playwright.sync_api import sync_playwright
from urllib3.util import parse_url


class Browser:
    def __init__(self):
        obscura_command = "obscura serve --stealth -v --storage-dir ./"
        docker_degoog_command = "docker compose --file {} up -d"

        if which("obscura") == None:
            untar_command = "tar xvf obscura.tar.gz"

            if "darwin" in system().lower():
                obscura_download = get(
                    "https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-aarch64-macos.tar.gz"
                )
            elif "linux" in system().lower() and "amd64" in machine().lower():
                obscura_download = get(
                    "https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux.tar.gz"
                )
            elif "linux" in system().lower():
                obscura_download = get(
                    "https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-aarch64-linux.tar.gz"
                )
            else:
                logger.error("Platform not currently supported!")

            with open("obscura.tar.gz", "wb") as file:
                file.writelines(obscura_download.iter_content(1024))

            try:
                untar_process = run(split(untar_command), shell=True, check=True)
                move("obscura", "/usr/local/bin/")
                move("obscura-worker", "/usr/local/bin/")

                untar_process.check_returncode()
            except CalledProcessError as e:
                logger.error(
                    "Untar command or move command failed! Are you sure you have tar installed? If so, do you have access to the /usr/local/ directory?"
                )
                logger.error(str(e))
                exit(-1)

        if which("docker") == None:
            logger.error(
                "Docker is not installed! Please install it to fetch search results via Degoog."
            )
            exit(-1)
        else:
            cwd = str(Path.cwd())
            if "HomeGrownAI" in cwd and "apps" not in cwd:
                path_to_docker_compose = Path(cwd, "apps/backend/compose.yaml")
            elif "apps" in cwd:
                head, _ = cwd.split("apps")
                path_to_docker_compose = Path(head, "apps/backend/compose.yaml")
            else:
                raise AIAppError(
                    "Unknown directory! Please run HomeGrownAI from the repository directory."
                )

            try:
                self.docker_process = run(
                    docker_degoog_command.format(str(path_to_docker_compose)),
                    shell=True,
                    env=environ,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    check=False,
                )

                self.docker_process.check_returncode()
            except CalledProcessError as e:
                logger.error(
                    f"Unable to launch Degoog container! Does your user have permissions to use Docker (i.e., you don't need sudo to use it)?\nFailed command: {e!s}"
                )
                exit(-1)

        self.obscura_process = Popen(
            split(obscura_command), shell=True, stdout=DEVNULL, stderr=DEVNULL
        )
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            "ws://127.0.0.1:9222/devtools/browser"
        )

    def __del__(self):
        logger.info("Shutting down the browser...")
        self.browser.close()
        self.playwright.stop()
        self.obscura_process.kill()

        client = docker.from_env()
        for container in client.containers.list():
            if "degoog" in container.name:
                container.stop()

    def web_search(self, search_query: str) -> dict[str, str]:
        params = urlencode({"q": search_query})
        response = get(f"http://localhost:4444/api/search?{params}")

        if response.content == None:
            return {
                "error": "Request failed.",
                "details": "The web request failed when attempting to query the search engine.",
            }
        else:
            results = orjson.loads(response.content)["results"]

            __import__("pprint").pprint(results)
            return results

    def navigate_to_site(self, link: str) -> str:
        parsed_url = parse_url(link)

        if parsed_url[0] == "http":
            raise AIAppError("Attempting to access insecure webpage!")
        elif parsed_url[3] != None and (
            parsed_url[0] == None or "file" in parsed_url[0]
        ):
            raise AIAppError(
                "Attempting to access a file-system path or passing a port to the URL!"
            )
        else:
            try:
                if str(parsed_url[2]) == "localhost":
                    raise AIAppError("Attempting to access an IP address directly!")

                ip_address(str(parsed_url[2]))

                raise AIAppError("Attemping to access an IP address directly!")
            except ValueError:
                try:
                    results = getaddrinfo(parsed_url[2], None, AF_UNSPEC)

                    ips = {res[4][0] for res in results}

                    hostname = gethostname()
                    local_ip = gethostbyname(hostname)

                    local_subnet = ip_network(local_ip, strict=False)

                    for ip in ips:
                        if ip in local_subnet:
                            raise AIAppError("IP address is inside the local subnet!")
                except gaierror:
                    raise AIAppError("gaierror")

                browser = self.browser.new_context().new_page()

                if get(link).status_code != 200:
                    raise AIAppError("Error when accessing the webpage!")
                browser.goto(link)

                return browser.inner_html("body")
