import json
import os
import boto3
from datetime import datetime

def datetime_handler(obj):
    """Serializa objetos datetime para JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def lambda_handler(event, context):
    """API Lambda para gerar histórias"""
    print("Evento recebido:", json.dumps(event))
    
    # Extrair método e path
    method = event['requestContext']['http']['method']
    path = event['rawPath']
    print(f"Método: {method}, Path: {path}")
    
    # Remover o stage do path
    if path.startswith('/staging/'):
        path = path[len('/staging/'):]
    print(f"Path após remover stage: {path}")
    
    if method == 'POST' and path == 'historia':
        return iniciar_geracao(event)
    elif method == 'GET' and path.startswith('historia/'):
        pedido_id = path.split('/')[-1]
        return verificar_status(pedido_id)
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'erro': 'Rota não encontrada'})
        }

def iniciar_geracao(event):
    """Inicia geração de história"""
    try:
        print("Iniciando geração de história")
        
        # Extrair dados do corpo
        body = json.loads(event['body'])
        print("Corpo da requisição:", json.dumps(body))
        
        # Validar campos obrigatórios
        campos = ['personagens', 'planetas', 'naves']
        for campo in campos:
            if campo not in body:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'erro': f'Campo obrigatório ausente: {campo}'
                    })
                }
        
        # Iniciar Step Function
        sfn = boto3.client('stepfunctions')
        print("ARN da Step Function:", os.environ['STORY_STATE_MACHINE_ARN'])
        response = sfn.start_execution(
            stateMachineArn=os.environ['STORY_STATE_MACHINE_ARN'],
            input=json.dumps(body)
        )
        print("Resposta da Step Function:", json.dumps(response, default=datetime_handler))
        
        # Extrair ID da execução do ARN
        execution_id = response['executionArn'].split(':')[-1]
        
        return {
            'statusCode': 202,
            'body': json.dumps({
                'pedido_id': execution_id,
                'status': 'processando'
            }, default=datetime_handler)
        }
        
    except json.JSONDecodeError:
        print("Erro: JSON inválido")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'erro': 'Corpo da requisição deve ser JSON válido'
            })
        }
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'erro': 'Erro interno do servidor'
            })
        }

def verificar_status(pedido_id):
    """Verifica status de uma geração"""
    try:
        print(f"Verificando status do pedido: {pedido_id}")
        
        # Buscar execução da Step Function
        sfn = boto3.client('stepfunctions')
        print("Cliente Step Functions criado")
        
        # Construir ARN da execução
        state_machine_arn = os.environ['STORY_STATE_MACHINE_ARN']
        print(f"ARN da state machine: {state_machine_arn}")
        
        state_machine_name = state_machine_arn.split(':')[-1]  # StoryStateMachine-N4PwDu9nLLld
        execution_arn = state_machine_arn.replace(
            f':stateMachine:{state_machine_name}',
            f':execution:{state_machine_name}:{pedido_id}'
        )
        print(f"ARN da execução: {execution_arn}")
        
        print("Chamando describe_execution...")
        response = sfn.describe_execution(
            executionArn=execution_arn
        )
        print("Resposta da Step Function:", json.dumps(response, default=datetime_handler))
        
        # Mapear status
        status_map = {
            'RUNNING': 'processando',
            'SUCCEEDED': 'concluido',
            'FAILED': 'erro',
            'TIMED_OUT': 'timeout',
            'ABORTED': 'cancelado'
        }
        print(f"Status original: {response['status']}")
        
        status = status_map.get(response['status'], 'desconhecido')
        print(f"Status mapeado: {status}")
        
        # Se concluído com sucesso, incluir resultado
        result = None
        if status == 'concluido':
            print("Processando resultado...")
            result = json.loads(response['output'])
            print(f"Resultado: {json.dumps(result)}")
        
        resposta = {
            'statusCode': 200,
            'body': json.dumps({
                'pedido_id': pedido_id,
                'status': status,
                'resultado': result
            }, default=datetime_handler)
        }
        print(f"Resposta final: {json.dumps(resposta)}")
        return resposta
        
    except Exception as e:
        print(f"Erro ao verificar status: {str(e)}")
        print(f"Tipo do erro: {type(e)}")
        print(f"Args do erro: {e.args}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'erro': 'Erro ao verificar status'
            })
        }
