import asyncio
import logging
import os
import random
import sys
import time
from pathlib import Path

from imjoy_rpc import connect_to_server

from .controller import delete_pods, get_api_instance, launch_pod

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger("main")
logger.setLevel(logging.WARNING)


def start_plugin_pod(config: dict):
    pod_id = config.get("id") or (
        "imjoy-plugin-pod-" + config.get("name", "") + str(random.random())
    )
    name = config.get("name") or "my-plugin"
    cmd = "python -m imjoy.runner --server-url=http://imjoy-app-engine /src/imjoy_plugin.py"
    workspace = config.get("workspace")
    api_instance = get_api_instance()

    if not config.get("source_code"):
        example_plugin_file = (
            Path(__file__) / "../../tests/example_plugin.py"
        ).resolve()
        with open(example_plugin_file, "r") as f:
            source_code = f.read()
    else:
        source_code = config.get("source_code")

    mount_dataset = config.get("mount_dataset")
    launch_pod(
        api_instance,
        pod_id,
        workspace,
        name,
        cmd,
        {"imjoy_plugin.py": source_code},
        mount_dataset=mount_dataset,
    )


def stop_plugin_pod(config: dict):
    api_instance = get_api_instance()
    delete_pods(api_instance, config["workspace"], config["name"])


async def main():
    logger.info("Connecting to server...")
    retry_count = 1000
    api = None
    while retry_count and not api:
        try:
            api = await connect_to_server(server_url="http://127.0.0.1:4000")
        except Exception:
            logger.info("Cannot reach to the server, retrying...%d", retry_count)
            time.sleep(1)
            retry_count -= 1
    if not api:
        logger.error("Failed to reach to the server, exiting...")
        loop = asyncio.get_event_loop()
        loop.stop()
        raise Exception("Failed to connect to the server")
    owners = os.environ.get("ADMINS", "")
    owners = [e.strip() for e in owners.split(",") if e.strip()]
    allow_list = os.environ.get("ALLOW_LIST", "")
    allow_list = [e.strip() for e in allow_list.split(",") if e.strip()]
    visibility = os.environ.get("VISIBILITY", "protected")
    assert visibility in ["protected", "public"]
    logger.info("Creating admin-workspace...")
    ws = await api.create_workspace(
        {
            "name": "admin-workspace",
            "persistent": True,  # make sure it won't be removed
            "owners": owners,
            "allow_list": allow_list,
            "deny_list": [],
            "visibility": visibility,  # protected or public
        }
    )
    await ws.log("admin-workspace created")
    logger.info("Registering plugin pod launcher...")
    await ws.register_service(
        {
            "name": "Plugin Pod Launcher",
            "type": "#plugin-pod-launcher",
            "start": start_plugin_pod,
            "stop": stop_plugin_pod,
        }
    )
    await ws.log("plugin pod launcher service registered")
    logger.info("ImJoy cluster controller is ready.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main())
    loop.run_forever()
