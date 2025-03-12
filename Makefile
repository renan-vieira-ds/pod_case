AWS_REGION=us-west-2

.PHONY: setup-local
setup-local:
	@echo "Criando o ARN do secrets manager no SSM Parameter Store..."
	aws ssm put-parameter --name "$(SECRET_ARN_NAME)" --value "$(SECRET_ARN_VALUE)" --type String --region "$(AWS_REGION)" --overwrite
	@echo "ARN salvo no SSM."

.PHONY: test-local
test-local:
	@echo "Rebuildando e Rodando Lambda localmente..."
	sam build
	sam local invoke StarWarsLambda -e event.json

.PHONY: start-local
start-local:
	@echo "Rebuildando e Iniciando serviço localmente (API Gateway + Lambda)..."
	sam build
	sam local start-api

.PHONY: deploy
deploy:
	@echo "Fazendo build do SAM..."
	sam build
	@echo "Fazendo deploy para a AWS..."
	sam deploy --guided
