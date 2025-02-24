# 1. Visão Geral

Este projeto implementa um sistema de IA generativa para criar histórias no universo Star Wars. Ele obtém dados da SWAPI (via Pinecone) e utiliza o modelo GPT-3.5-turbo (OpenAI) para compor narrativas personalizadas. A arquitetura inclui:

- Ingestão Offline: Coleta e indexa dados no Pinecone.
- Lambda Function: Recebe parâmetros (personagens, planetas, naves) e retorna a narrativa.
- API Gateway: Exposição do endpoint HTTP.
- Interface Local (Flask): Front-end simples local para  interagir com a Lambda (local ou na aws).

# 2. Estrutura 

```
pod_case/
  ├── ingest/
  │   ├── ingest_swapi.py        # Script de ingestão offline no Pinecone
  ├── lambda/
  │   ├── app.py                 # Código principal da Lambda
  │   ├── requirements.txt       # Dependências
  ├── local_frontend/
  │   ├── server.py              # Servidor Flask para interface local
  ├── event.json                 # Exemplo de evento API Gateway (para sam local invoke)
  ├── template.yaml              # Template SAM
  └── README.md                  # Este README
```

# 3. Ingestão de Dados (Offline)

## 3.1 Objetivo
Carregar dados preprocessados da SWAPI no Pinecone, gerando o índice que a Lambda consultará.

## 3.2 Passos
1. Configurar suas variáveis de ambiente (chaves Pinecone, etc.).
2. Rodar o script de preprocessemaneto da swapi e depois o de ingestão:
```
cd ingest
python swapi_preprocessor.py
python ingest_data.py
```
> **NOTE**: Essa etapa não é executada dentro da Lambda. É um processamento offline e prévio ao deploy da lambda function 

# 4. Lambda local
## 4.1 SAM build e local start

1. Instalar o SAM CLI.
2. Editar lambda/requirements.txt se necessário.
3. Build:
```
sam build
```
4. Rodar local:
```
sam local start-api --env-vars local-env.json
```
> **NOTE**: Se esse passo persistir em erros, exporte as variáveis de ambiente no bash

- Subirá um endpoint em `http://127.0.0.1:3000/historia` (ou `/Prod/historia`, dependendo do template)
- Testar via `curl`:
```
curl -X POST -H "Content-Type: application/json" \
  -d '{"personagens":["Luke"],"planetas":["Tatooine"],"naves":["X-Wing"]}' \
  http://127.0.0.1:3000/historia

```

## 4.2 SAM local invovke
Para testar individualmente a função Lambda sem iniciar a rota:

1. Criar/editar `event.json` (simulando body do API Gateway):
```
{
  "resource": "/historia",
  "path": "/historia",
  "httpMethod": "POST",
  "body": "{\"personagens\":[\"Luke\"],\"planetas\":[\"Tatooine\"],\"naves\":[\"X-Wing\"]}"
}
```

2. Invocar:
1. Criar/editar `event.json` (simulando body do API Gateway):
```
sam build
sam local invoke "StarWarsLambda" --event event.json
```

# 5. Front local
## 5.1 Objetivo
Exibir um formulário HTML para enviar parâmetros (personagens, planetas, naves) e mostrar a narrativa. Útil para testar acentuação e formatação.

## 5.2 Passos
1. Instalar as dependências:
```
pip install flask requests
```

2. Iniciar o server:
```
cd local_frontend
python server.py
```
3. Acesse `http://127.0.0.1:5000` no browser
4. Na variável `lambda_url` atribua `http://127.0.0.1:3000/historia` se estiver rodando via SAM local. Se quiser testar com a lambda já deployada, mude para a url que é fornecida no deploy

# 6. Deploy com SAM

1. Configurar suas credenciais AWS (`aws configure`) e ter as chaves e api (Pinecone/OpenAI) em um segredo na Secrets Manager
> **NOTE 1**: crie o segredo na mesma regiao q ue vc vai deployar a lambda
> **NOTE 2**: No template em `Environment/Variables` use o arn completo criado pro segredo (no consosle tem o arn)

2. Build:
```
sam build
```
3. Deploy:
```
sam deploy --guided
```
- Defina Stack Name, regiao (tem de ser igual a do segredo)
- Se o deploy foi finalizado sem erro, o output exibirá a url

4. Testar:
```
curl -X POST -H "Content-Type: application/json" \
  -d '{"personagens":["Luke"],"planetas":["Tatooine"],"naves":["X-Wing"]}' \
  https://xxxxx.execute-api.us-west-2.amazonaws.com/Prod/historia
```