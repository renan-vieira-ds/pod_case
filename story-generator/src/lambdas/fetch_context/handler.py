import json
import os
from typing import List, Dict, Any

import boto3
from pinecone import Pinecone
from langchain.embeddings import BedrockEmbeddings


def get_pinecone_secrets():
    """Busca credenciais do Pinecone diretamente do Secrets Manager"""
    secrets = boto3.client('secretsmanager')
    secret_name = "myproject/starwars"
    
    try:
        response = secrets.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar segredo: {str(e)}")

def get_embeddings(text: str, bedrock) -> List[float]:
    """Gera embeddings usando Bedrock"""
    embeddings = BedrockEmbeddings(
        model_id="cohere.embed-multilingual",
        client=bedrock
    )
    return embeddings.embed_query(text)

def fetch_entity_context(entity: str, index, bedrock, top_k: int = 2) -> List[str]:
    """Busca contexto para uma entidade específica"""
    query_embedding = get_embeddings(entity, bedrock)
    
    # Buscar vetores mais similares
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # Extrair e retornar o contexto
    contexts = []
    for match in results['matches']:
        if match['score'] >= 0.7:  # Threshold de similaridade
            contexts.append(match['metadata']['context'])
    
    return contexts

def fetch_context(characters: List[str], planets: List[str], ships: List[str]) -> Dict[str, Any]:
    """Busca contexto relevante do Pinecone para cada entidade"""
    # Inicializar clientes
    bedrock = boto3.client('bedrock-runtime')
    secrets = get_pinecone_secrets()
    
    # Inicializar Pinecone
    pc = Pinecone(api_key=secrets['api_key'])
    index = pc.Index(secrets['index_name'])
    
    # Buscar contexto para cada tipo de entidade
    context = {
        'characters': {},
        'planets': {},
        'ships': {}
    }
    
    # Processar personagens
    for character in characters:
        context['characters'][character] = fetch_entity_context(character, index, bedrock)
    
    # Processar planetas
    for planet in planets:
        context['planets'][planet] = fetch_entity_context(planet, index, bedrock)
    
    # Processar naves
    for ship in ships:
        context['ships'][ship] = fetch_entity_context(ship, index, bedrock)
    
    return context

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler do Lambda"""
    try:
        # Extrair entidades do evento
        characters = event.get('personagens', [])
        planets = event.get('planetas', [])
        ships = event.get('naves', [])
        
        # Buscar contexto
        context = fetch_context(characters, planets, ships)
        
        return {
            'statusCode': 200,
            'body': context
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
