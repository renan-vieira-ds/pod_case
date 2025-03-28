import json
import boto3


def lambda_handler(event, context):
    """Gera história usando Bedrock"""
    
    # Extrair dados
    personagens = event['personagens']
    planetas = event['planetas']
    naves = event['naves']
    contexto = event['contexto']  # vem do FetchContext
    
    # Montar prompt
    prompt = f"""Você é um narrador de histórias de Star Wars. Use o contexto fornecido para criar uma história envolvente.

Contexto sobre os elementos:
{contexto}

Elementos que devem aparecer na história:
- Personagens: {', '.join(personagens)}
- Planetas: {', '.join(planetas)}
- Naves: {', '.join(naves)}

Crie uma história emocionante em português que:
1. Tenha entre 3-4 parágrafos
2. Use todos os elementos fornecidos
3. Seja fiel ao universo Star Wars
4. Tenha um arco narrativo claro
5. Termine com uma conclusão satisfatória

História:"""

    # Chamar Bedrock
    bedrock = boto3.client('bedrock-runtime')
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-v2',
        body=json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant: ",
            "max_tokens_to_sample": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "anthropic_version": "bedrock-2023-05-31"
        })
    )
    
    # Extrair história
    historia = json.loads(response['body'].read())['completion']
    
    return {
        'historia': historia.strip()
    }
