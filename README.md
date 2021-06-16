# ImJoy App Engine

## Steps to install ImJoy App Engine

```
sudo snap install microk8s --classic
microk8s start # start the cluster
microk8s enable helm3
microk8s helm3 install --set imjoyHostName=engine.imjoy.io imjoy-app-engine ./charts/imjoy-app-engine
```