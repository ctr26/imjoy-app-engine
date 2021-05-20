"""Utility functions for managing k8s pods"""
import logging
import sys
import time

from kubernetes import config
from kubernetes.client import Configuration, V1ConfigMap, V1ObjectMeta
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger("controller")
logger.setLevel(logging.WARNING)

_api_instance = None


def get_api_instance():
    global _api_instance
    if _api_instance:
        return _api_instance
    # config.load_kube_config() # for running from the host
    config.load_incluster_config()  # for running inside the cluster
    try:
        c = Configuration().get_default_copy()
    except AttributeError:
        c = Configuration()
        c.assert_hostname = False
    Configuration.set_default(c)
    _api_instance = core_v1_api.CoreV1Api()
    return _api_instance


def create_configmap(
    api_instance, name, data, workspace, plugin_name, namespace="default"
):
    # Configureate ConfigMap metadata
    metadata = V1ObjectMeta(
        name=name,
        namespace=namespace,
        labels={
            "workspace": workspace,
            "plugin": plugin_name,
            "type": "imjoy-plugin-runner",
        },
    )
    # Instantiate the configmap object
    configmap = V1ConfigMap(
        api_version="v1", kind="ConfigMap", data=data, metadata=metadata
    )
    try:
        api_instance.create_namespaced_config_map(
            namespace=namespace,
            body=configmap,
        )
        logger.info("created config map")
    except ApiException as e:
        logger.exception(
            "Exception when calling CoreV1Api->create_namespaced_config_map: %s\n", e
        )


def delete_pods(api_instance, workspace, plugin_name, namespace="default"):
    pods = api_instance.list_namespaced_pod(
        namespace,
        label_selector=f"plugin={plugin_name},workspace={workspace}",
        watch=False,
    )
    logger.info("Deleting pods: %d", len(pods.items))
    for pod in pods.items:
        try:
            resp = api_instance.delete_namespaced_pod(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                grace_period_seconds=0,
                propagation_policy="Background",
            )
        except ApiException as e:
            logger.error(
                "Exception when calling CoreV1Api->delete_namespaced_pod: %s\n", e
            )


def launch_pod(
    api_instance,
    plugin_id,
    workspace,
    plugin_name,
    command,
    source_files,
    extra_commands=None,
    image="imjoy-team/imjoy-plugin-worker",
    namespace="default",
    mount_dataset=None,
    home_pvc_claim=None,
):
    source_config = plugin_id + "-src-config"
    create_configmap(api_instance, source_config, source_files, workspace, plugin_name)

    resp = None
    try:
        resp = api_instance.read_namespaced_pod(name=plugin_id, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error("Unknown error: %s", e)
            raise Exception(f"Unknown error: {e}")

    if resp:
        logger.error("Pod %s already exist. Deleting it...", plugin_id)
        raise Exception(f"Pod {plugin_id} already exist. Deleting it...")

    logger.info("Creating pod %s...", plugin_id)
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "labels": {
                "workspace": workspace,
                "plugin": plugin_name,
                "type": "imjoy-plugin-runner",
            },
            "name": plugin_id,
        },
        "spec": {
            "containers": [
                {
                    "image": image,
                    "name": "imjoy-plugin-worker",
                    "args": [c for c in command.split(" ") if c.strip()],
                    "imagePullPolicy": "Never",
                    "volumeMounts": [
                        {"name": "src", "mountPath": "/src", "readOnly": True}
                    ],
                }
            ],
            "volumes": [{"name": "src", "configMap": {"name": source_config}}],
            "restartPolicy": "Never",
        },
    }

    if mount_dataset:
        pod_manifest["metadata"]["labels"]["dataset.0.id"] = mount_dataset
        pod_manifest["metadata"]["labels"]["dataset.0.useas"] = "mount"
        pod_manifest["spec"]["containers"][0]["volumeMounts"].append(
            {"mountPath": f"/mnt/datasets/{mount_dataset}", "name": mount_dataset}
        )

    if home_pvc_claim:
        pod_manifest["spec"]["containers"][0]["volumeMounts"].append(
            {"mountPath": "/home", "name": "pv-storage"}
        )
        pod_manifest["spec"]["volumes"].append(
            {
                "name": "pv-storage",
                "persistentVolumeClaim": {"claimName": home_pvc_claim},
            }
        )

    resp = api_instance.create_namespaced_pod(body=pod_manifest, namespace=namespace)
    while True:
        resp = api_instance.read_namespaced_pod(name=plugin_id, namespace=namespace)
        if resp.status.phase != "Pending":
            break
        time.sleep(1)
    logger.info("Pod created: %s", plugin_id)

    if not extra_commands:
        return

    for command in extra_commands:
        if isinstance(command, str):
            command = [c for c in command.split(" ") if c.strip()]
        logger.info("Running command %s", command)
        # Calling exec and waiting for response
        resp = stream(
            api_instance.connect_get_namespaced_pod_exec,
            plugin_id,
            namespace,
            command=command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        logger.info("Response for command %s: %s", command, resp)


if __name__ == "__main__":
    name = "imjoy-plugin-pod"
    plugin_name = "my-plugin"
    cmd = "python -m imjoy.runner --server-url=http://imjoy-app-engine /home/example_plugin.py --quit-on-ready"
    api_instance = get_api_instance()
    workspace = "my-workspace"
    # delete_pods(api_instance, workspace, plugin_name)
    launch_pod(api_instance, name, workspace, plugin_name, cmd)
