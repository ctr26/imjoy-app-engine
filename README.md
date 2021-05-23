# Deploy ImJoy App Engine Server to K8s

Useful links:
 * k8s cheatsheet: https://kubernetes.io/docs/reference/kubectl/cheatsheet/

## Create a volume

Create a directory, e.g. /mnt/data, then change it in the imjoy-config-map.yml

Ref: https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/
## Setup dashboard
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.2.0/aio/deploy/recommended.yaml
```

### Create service account
```
kubectl apply -f ../service-account.yml
kubectl get serviceaccount
```

### Visit dashboard

Get the token:
```
kubectl get secrets
kubectl describe secret imjoy-service-account-token-z74fg
```

Run the following command to start the proxy:
```
kubectl proxy
```

Go to http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login

And login with the token.

### Deploy an ingress controller

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.46.0/deploy/static/provider/cloud/deploy.yaml

# verify the installation
kubectl get pods -n ingress-nginx \
  -l app.kubernetes.io/name=ingress-nginx --watch
```

Detect installed controller version
```
POD_NAMESPACE=default
POD_NAME=$(kubectl get pods -n $POD_NAMESPACE -l app.kubernetes.io/name=ingress-nginx --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it $POD_NAME -n $POD_NAMESPACE -- /nginx-ingress-controller --version
```

Ref: https://kubernetes.github.io/ingress-nginx/deploy/



### Deploy ImJoy

Build docker image
```
docker build ./imjoy-app-engine -t imjoy-team/imjoy-app-engine
docker build ./imjoy-worker -t imjoy-team/imjoy-worker
```

Install
```
helm install imjoy-app-engine ./charts/imjoy-app-engine/
```
Upgrade

```
helm upgrade imjoy-app-engine ./charts/imjoy-app-engine/
```

Test with a imjoy worker pod
```
kubectl run -it testimjoyworker --image=imjoy-team/imjoy-test-worker --image-pull-policy=Never --restart=Never --rm
```
You should see the following:
```
Generated token: imjoy@eyJhbGci...
echo: a message
```

To start an interactive session:
```
kubectl run -it testimjoyworker --image=imjoy-team/imjoy-test-worker --image-pull-policy=Never bin/bash --restart=Never --rm

# run in the command prompt
wget http://imjoy-app-engine
```




### Debugging with a test pod

```
kubectl run -it testpod --image=alpine bin/ash --restart=Never --rm
```

This will allow us to test the pods in the same cluster, e.g.:
```
wget imjoy-app-engine
```

### Support mounting datasets from s3

```
kubectl apply -f https://raw.githubusercontent.com/IBM/dataset-lifecycle-framework/master/release-tools/manifests/dlf.yaml
kubectl label namespace default monitor-pods-datasets=enabled

kubectl apply -f example-dataset.yml
```

Ref: https://github.com/datashim-io/datashim

