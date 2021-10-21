import argparse
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

def setup_extension(imjoy_api):
    workspace = os.environ.get("ADMINS", "admin-workspace")
    owners = os.environ.get("ADMINS", "")
    owners = [e.strip() for e in owners.split(",") if e.strip()]
    allow_list = os.environ.get("ALLOW_LIST", "")
    allow_list = [e.strip() for e in allow_list.split(",") if e.strip()]
    visibility = os.environ.get("VISIBILITY", "protected")
    assert visibility in ["protected", "public"]
    ws = imjoy_api.create_workspace(
        {
            "name": workspace,
            "persistent": False,  # The workspace can be removed
            "owners": owners,
            "allow_list": allow_list,
            "deny_list": [],
            "visibility": visibility,  # protected or public
        }
    )
    ws['register_service'](
        {
            "name": "Plugin Pod Launcher",
            "type": "#plugin-pod-launcher",
            "start": start_plugin_pod,
            "stop": stop_plugin_pod,
            "heartbeat": lambda x: x
        }
    )
    

async def start_liveness_check(pod_service, liveness_file):
    if os.path.exists(liveness_file):
        os.remove(liveness_file)
    while True:
        try:
            await pod_service.heart_beat()
            with open(liveness_file, 'w'):
                pass
        except Exception:
            if os.path.exists(liveness_file):
                os.remove(liveness_file)
        await asyncio.sleep(1)

async def main(opt):
    loop = asyncio.get_event_loop()
    logger.info("Connecting to server...")
    retry_count = 1000
    api = None
    while retry_count and not api:
        try:
            api = await connect_to_server(server_url=opt.server_url)
        except Exception:
            logger.info("Cannot reach to the server, retrying...%d", retry_count)
            time.sleep(1)
            retry_count -= 1
    if not api:
        logger.error("Failed to reach to the server, exiting...")
        loop.stop()
        raise ConnectionError("Failed to connect to the server")
    owners = opt.admins or os.environ.get("ADMINS", "")
    owners = [e.strip() for e in owners.split(",") if e.strip()]
    allow_list = opt.allow_list or os.environ.get("ALLOW_LIST", "")
    allow_list = [e.strip() for e in allow_list.split(",") if e.strip()]
    visibility = opt.visibility or os.environ.get("VISIBILITY", "protected")
    opt.workspace = opt.workspace or os.environ.get("WORKSPACE", "admin-workspace")
    assert visibility in ["protected", "public"]
    logger.info("Creating workspace: %s...", opt.workspace)
    try:
        ws = await api.get_workspace(opt.workspace)
    except Exception:
        ws = await api.create_workspace(
            {
                "name": opt.workspace,
                "persistent": False,  # The workspace can be removed
                "owners": owners,
                "allow_list": allow_list,
                "deny_list": [],
                "visibility": visibility,  # protected or public
            }
        )
    await ws.log("Workspace created")
    logger.info("Registering plugin pod launcher...")
    await ws.register_service(
        {
            "name": "Plugin Pod Launcher",
            "type": "#plugin-pod-launcher",
            "start": start_plugin_pod,
            "stop": stop_plugin_pod,
            "heartbeat": lambda x: x
        }
    )
    pod_service = await ws.get_services({"type": "#plugin-pod-launcher"})
    await ws.log("plugin pod launcher service registered")
    logger.info("ImJoy cluster controller is ready.")
    if opt.liveness_file:
        loop.create_task(start_liveness_check(pod_service, opt.liveness_file))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server-url", type=str, default="http://127.0.0.1:4000", help="The imjoy core serve URL"
    )
    parser.add_argument(
        "--admins", type=str, default=None, help="A list of email or id for administrators, separated by comma"
    )
    parser.add_argument(
        "--allow-list", type=str, default=None, help="A list of email or id for the users which are allowed to access the controller"
    )
    parser.add_argument(
        "--visibility", type=str, default=None, help="The visibility of the controller, default: protected"
    )
    parser.add_argument(
        "--workspace", type=str, default="admin-workspace", help="The name of the workspace"
    )
    parser.add_argument(
        "--liveness-file", type=str, default=None, help="A file path for liveness check"
    )
    opt = parser.parse_args()
    async def run():
        try:
            await main(opt)
        except Exception:
            loop.stop()

    asyncio.ensure_future(run())
    loop.run_forever()
