all: prod
prod:
	helmsman --debug --apply -f imjoy-app-engine-dsf.yaml -f production.yaml

staging:
	helmsman --debug --apply -f imjoy-app-engine-dsf.yaml -f staging.yaml -f minikube.yaml

staging.minikube:
	helmsman --debug --apply -f imjoy-app-engine-dsf.yaml -f staging.yaml -f minikube.yaml

destroy: destroy.prod

destroy.prod:
	helmsman --debug --destroy -f imjoy-app-engine-dsf.yaml -f production.yaml
# destroy.staging:
# 	helmsman --debug --destroy -f imjoy-app-engine-dsf.yaml -f staging.yaml
nuke:
	kubectl delete namespace cert-manager staging production --force