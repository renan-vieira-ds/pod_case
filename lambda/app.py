import os
import json
from typing import List

from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore  
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage


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

        personagens = body["personagens"]  # lista de strings
        planetas = body["planetas"]        # lista de strings
        naves = body["naves"]             # lista de strings

        # 2) Conexão com Pinecone
        pc = Pinecone(
            api_key=os.environ["PINECONE_API_KEY"],
            environment=os.environ["PINECONE_ENV"]
        )

        # 3) Embeddings e LLM (via langchain_openai)
        embeddings = OpenAIEmbeddings(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            model="text-embedding-ada-002"
        )
        llm = ChatOpenAI(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=800
        )

        # 4) VectorStore do langchain_community
        vectorstore = PineconeVectorStore(
            pc.Index('sw-index'),
            embeddings,
            'text',
        )

         # 5) Fazer apenas UMA busca
        query_text = " ".join(personagens + planetas + naves)
        docs = vectorstore.similarity_search(query_text, k=3)
        if not docs:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Nenhuma entidade encontrada na base canônica."})
            }

        # 6) Concatena o conteúdo dos documentos como "context"
        context_text = ""
        for doc in docs:
            context_text += doc.page_content + "\n\n"

        # 7) Montar prompt
        personagens_str = ", ".join(personagens)
        planetas_str = ", ".join(planetas)
        naves_str = ", ".join(naves)

        human_msg = HumanMessage(content=(
            f"Contexto:\n{context_text}\n\n"
            f"Crie uma narrativa de Star Wars envolvendo os personagens: {personagens_str}, "
            f"nos planetas: {planetas_str}, com as naves: {naves_str}.\n\n"
            "A história deve entregar uma narrativa incrível e imersiva para um star war fan"
        ))

        # 9) Envia as mensagens ao LLM
        response = llm([human_msg])
        narrativa = response.content

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
