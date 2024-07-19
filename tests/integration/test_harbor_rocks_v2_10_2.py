#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

from k8s_test_harness import harness
from k8s_test_harness.util import env_util
from k8s_test_harness.util import exec_util


CHART_RELEASE_URL = (
    "https://github.com/goharbor/harbor-helm/archive/refs/tags/v1.15.0.tar.gz")

# This mapping indicates which fields of the upstream Harbor Helm chart
# contain the 'image' fields which should be overriden with the ROCK
# image URLs and version during testing.
# https://github.com/goharbor/harbor-helm/blob/main/values.yaml
IMAGE_NAMES_TO_CHART_VALUES_OVERRIDES_MAP = {
    "harbor-db": "database.internal",
    "harbor-core": "core",
    "harbor-jobservice": "jobservice",
    "harbor-registryctl": "registry.controller",
    "harbor-exporter": "exporter",
    "harbor-portal": "portal",
    "nginx-photon": "nginx",
    "redis-photon": "redis.internal",
    "registry-photon": "registry.registry",
    "trivy-adapter-photon": "trivy",
}


def test_harbor_chart_deployment(module_instance: harness.Instance):

    version = "v2.10.2"

    # Compose the Helm command line args for overriding the
    # image fields for each component:
    all_chart_value_overrides_args = []
    for rmi in env_util.get_rocks_meta_info_from_env():
        if rmi.name in IMAGE_NAMES_TO_CHART_VALUES_OVERRIDES_MAP and (
                rmi.arch == "amd64"):
            chart_section = IMAGE_NAMES_TO_CHART_VALUES_OVERRIDES_MAP[rmi.name]
            repo, tag = rmi.image.split(':')
            all_chart_value_overrides_args.extend([
                "--set", f"{chart_section}.image.repository={repo}",
                "--set", f"{chart_section}.image.version={tag}"
            ])

    helm_command = [
        "sudo",
        "k8s",
        "helm",
        "install",
        "harbor",
        CHART_RELEASE_URL,
    ]
    helm_command.extend(all_chart_value_overrides_args)

    module_instance.exec(helm_command)

    exec_util.stubbornly(retries=3, delay_s=1).on(module_instance).exec(
        [
            "sudo",
            "k8s",
            "helm",
            "status",
            "harbor"
        ]
    )
