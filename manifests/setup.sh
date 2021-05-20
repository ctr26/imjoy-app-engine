# load config map (edit it before executing this script)
kubectl apply -f config-map.yml 

# deploy ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.46.0/deploy/static/provider/cloud/deploy.yaml
kubectl get pods -n ingress-nginx \
  -l app.kubernetes.io/name=ingress-nginx

# deploy imjoy engine server
# docker build ./imjoy-app-engine -t imjoy-team/imjoy-app-engine
# docker build ./imjoy-worker -t imjoy-team/imjoy-worker

kubectl apply -f imjoy-app-engine/deployment.yml
kubectl apply -f imjoy-app-engine/service.yml
kubectl apply -f ingress.yml


# test with imjoy worker
# kubectl run -it testimjoyworker --image=imjoy-team/imjoy-test-worker --image-pull-policy=Never --restart=Never --rm

# start dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.2.0/aio/deploy/recommended.yaml

# setup account for the dashboard
kubectl apply -f ./service-account.yml
kubectl get serviceaccount
kubectl get secrets
# kubectl describe secret imjoy-service-account-token-vrxr7


# enable dataset support
kubectl apply -f https://raw.githubusercontent.com/IBM/dataset-lifecycle-framework/master/release-tools/manifests/dlf.yaml
kubectl label namespace default monitor-pods-datasets=enabled
# fillin with credentials in the file
#kubectl apply -f example-dataset.yml

# mount a persistent volume
# kubectl apply -f pv-volume.yml

