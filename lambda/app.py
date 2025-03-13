import json

import boto3
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore  
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage


# Inicializar cliente do AWS Secrets Manager e SSM
session = boto3.session.Session()

secret_client = session.client(
    service_name="secretsmanager",
    region_name="us-west-2"
)
ssm_client = session.client(
    service_name="ssm",
    region_name="us-west-2"
)

def get_secret_arn():
    """Busca o ARN do segredo no AWS SSM Parameter Store na AWS"""
    response = ssm_client.get_parameter(Name="/myproject/starwars/secret-arn", WithDecryption=True)
    return response["Parameter"]["Value"]

def get_secret(secret_key):
    """Busca o valor do segredo no AWS Secrets Manager."""
    secret_arn = get_secret_arn()
    response = secret_client.get_secret_value(SecretId=secret_arn)
    secret_data = json.loads(response["SecretString"])
    return secret_data.get(secret_key)

def retrieve_documents(vectorstore, personagens, planetas, naves, k_personagens=20, k_outros=10):
    """
    Para cada entidade (personagens, planetas, naves), busca documentos relevantes.
    
    - Para personagens, traz tanto personalidade quanto informações da SWAPI.
    - Para planetas e naves, traz informações gerais da SWAPI.
    - Usa busca sem filtro para evitar falhas por nomes diferentes.
    
    Args:
        vectorstore: Instância do PineconeVectorStore
        personagens: Lista de personagens
        planetas: Lista de planetas
        naves: Lista de naves
        k_personagens: Quantidade de documentos para personagens (padrão: 20)
        k_outros: Quantidade de documentos para planetas e naves (padrão: 10)
    
    Returns:
        Lista de documentos relevantes
    """
    all_docs = []

    # 1) Recupera documentos para cada personagem
    for personagem in personagens:
        docs = vectorstore.similarity_search(personagem, k=k_personagens)
        all_docs.extend(docs)

    # 2) Recupera documentos para cada planeta
    for planeta in planetas:
        docs = vectorstore.similarity_search(planeta, k=k_outros)
        all_docs.extend(docs)

    # 3) Recupera documentos para cada nave
    for nave in naves:
        docs = vectorstore.similarity_search(nave, k=k_outros)
        all_docs.extend(docs)

    return all_docs

def generate_narrative(context_text, personagens, planetas, naves, openai_api_key):
    """
    Gera uma narrativa baseada nos dados recuperados do Pinecone.
    Usa ChatOpenAI do LangChain para gerar o texto.
    """

    # 1) Criar a string dos personagens, planetas e naves para o prompt
    personagens_str = ", ".join(personagens)
    planetas_str = ", ".join(planetas)
    naves_str = ", ".join(naves)

    # 2) Definir o modelo (aqui você pode trocar para GPT-4 Turbo ou outro)
    llm = ChatOpenAI(
        openai_api_key=openai_api_key,
        model_name="gpt-4o",  # Melhorando o modelo!
        temperature=0.7,
        max_tokens=4000  # Aumentando a capacidade da história
    )

    # 3) Construir a mensagem do usuário com o prompt refinado
    human_msg = HumanMessage(content=(
        f"Contexto:\n{context_text}\n\n"
        "Você é um contador de histórias lendário no universo de Star Wars. "
        "Baseando-se no contexto fornecido, que contém informações sobre a personalidade dos personagens "
        "e dados canônicos da SWAPI, crie uma **narrativa épica** seguindo uma estrutura envolvente. A história deve conter:\n\n"
        "1. **Introdução:** Apresente o protagonista e o conflito ou missão que o impulsiona.\n"
        "2. **Desenvolvimento:** Descreva desafios e reviravoltas, explorando como a personalidade influencia decisões e relações.\n"
        "3. **Clímax:** Conduza a narrativa a um ponto de alta tensão, onde o protagonista enfrenta um desafio crítico.\n"
        "4. **Desfecho:** Conclua com uma resolução impactante, mostrando a evolução do personagem.\n\n"
        "**Não divida explicitamente a história nessas partes**. A transição deve ser fluida e natural.\n\n"
        "**Elementos obrigatórios:**\n"
        f"- **Personagens:** {personagens_str}\n"
        f"- **Planetas:** {planetas_str}\n"
        f"- **Naves:** {naves_str}\n\n"
        "**Importante:**\n"
        "- Priorize o desenvolvimento do enredo e a evolução dos personagens.\n"
        "- Priorize o avanço da narrativa.\n"
        "- Garanta que a história tenha um **fluxo coeso** e um **desfecho marcante**.\n\n"
        "- Não indique no texto qual é a parte da estrutura (se climax, desfecho, etc)"
        "- A história deve **sempre** ser em português!"
        "Agora, crie essa aventura!"
    ))

    # 5) Chamar o modelo
    response = llm([human_msg])

    return response.content

def lambda_handler(event, context):
    try:
        # 1) Ler e validar body
        body_str = event.get("body", "{}")
        body = json.loads(body_str)

        # Checamos se 'personagens', 'planetas', 'naves' existem e são listas
        if not isinstance(body, dict):
            return {"statusCode": 400, "body": json.dumps({"error": "Body inválido. Deve ser JSON."})}

        for campo in ["personagens", "planetas", "naves"]:
            if campo not in body:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": f"Campo '{campo}' é obrigatório."})
                }
            if not isinstance(body[campo], list) or len(body[campo]) < 1:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": f"'{campo}' deve ser uma lista com ao menos 1 item."
                    })
                }

        personagens = body["personagens"]
        planetas = body["planetas"]      
        naves = body["naves"]            

        # Buscar segredos do AWS Secrets Manager
        openai_api_key = get_secret("OPENAI_API_KEY")
        pinecone_api_key = get_secret("PINECONE_API_KEY")
        pinecone_env = get_secret("PINECONE_ENV")
        
        # 2) Conexão com Pinecone
        pc = Pinecone(
            api_key=pinecone_api_key,
            environment=pinecone_env
        )

        # 3) Embeddings
        embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model="text-embedding-ada-002"
        )

        # 4) VectorStore do langchain_community
        vectorstore = PineconeVectorStore(
            pc.Index('sw-index'),
            embeddings,
            'text',
        )

        # 5) Recupera documentos do Pinecone
        docs = retrieve_documents(
            vectorstore,
            personagens,
            planetas,
            naves
        )

        if docs is None:
            return {
                "statusCode": 400, 
                "body": json.dumps({"error": "Nenhuma entidade encontrada na base canônica."})
            }
        
        # Contexto gerado a partir dos documentos
        context_text = "\n\n".join(
            [doc.page_content for doc in docs]
        )

        # 6) Gera a narrativa
        narrativa = generate_narrative(
            context_text,
            personagens,
            planetas,
            naves,
            openai_api_key
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"narrativa": narrativa})
        }

    except Exception as e:
        print("Erro interno:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
