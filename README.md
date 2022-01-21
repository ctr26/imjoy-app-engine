## Tooling 

Helmsman version: v3.6.3
Helm: v3

## Quickstart

Running

    make

It will use helmsman to deploy the necessary tooling to kube-context with name *imjoy-app-engine*. Hypha deployment is currently not automated:

    kubectl apply -f hypha/deployment.yaml hypha/ingress.yaml

Should work

This does not install the gpu-operator as that varies so much between kubernetes cluster deployments that it can be more harmful. The nvidia driver however is installed be default.

## TODO

 - All of the secrets are currently hardcoded
 - Automate hypha deployment
 - No CI/CD or automated testing
