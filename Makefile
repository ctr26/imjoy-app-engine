#!make
include .env
include secrets.env
export
BASEDIR = $(shell pwd)
# SOURCE:=$(shell source secrets.env)
# include .secrets
deploy.prod:
	helmsman --apply --debug --group production -f helmsman/token.yaml -f helmsman.yaml -f helmsman/production.yaml
deploy.staging:
	helmsman --apply --debug --group production -f helmsman/token.yaml -f helmsman.yaml -f helmsman/production.yaml
deploy.triton:

deploy.minikube:
	helmsman --apply --debug --group staging -f helmsman/token.yaml -f helmsman.yaml -f helmsman/staging.yaml -f helmsman/minikube.yaml

triton.deploy.prod.minikube:
	helmsman --apply --debug --target tritoninferenceserver -f helmsman.yaml -f helmsman/production.yaml -f helmsman/minikube.yaml --always-upgrade




minio.deploy.prod.denbi:
	helmsman --apply --debug --target minio -f helmsman.yaml -f helmsman/production.yaml -f helmsman/denbi.yaml --always-upgrade


denbi.k8s.jump:
	sshuttle --dns -NHr denbi-jumphost-01.bihealth.org 0/0


# load_env:
# 	if [ -f .env ]; then
# 		export $(echo $(cat .env | sed 's/#.*//g'| xargs) | envsubst)
# 	fi