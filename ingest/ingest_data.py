import os
from typing import List
import json

import pinecone
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()

class PineconeIngestor:
    def __init__(self):
        # Configurar conexão com OpenAI
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Configurar cliente Pinecone (v3+)
        self.pc = pinecone.Pinecone(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.environ.get("PINECONE_ENV")
        )
        
        # Nome do índice fixo
        self.index_name = "sw-index"
        self.index = self.pc.Index(self.index_name)
        
        # Verificar se o índice existe
        if self.index_name not in self.pc.list_indexes().names():
            raise ValueError(f"Índice {self.index_name} não encontrado!")

    def load_processed_documents(self, file_path: str) -> List[Document]:
        """Carrega documentos pré-processados de arquivo"""
        with open(file_path, "r") as f:
            stored_docs = json.load(f)
        
        return [
            Document(
                page_content=doc["page_content"],
                metadata=doc["metadata"]
            )
            for doc in stored_docs
        ]
    
    def ingest_documents(self, documents: List[Document]):
        """Realiza a ingestão dos documentos no Pinecone"""
        print(self.index_name)
        Pinecone.from_documents(
            documents=documents,
            embedding=self.embeddings,
            index_name=self.index_name,  # Parâmetro corrigido
            # pinecone_client=self.pc  # Passar o cliente explicitamente
        )
        print(f"{len(documents)} documentos ingeridos no índice {self.index_name}")

if __name__ == "__main__":
    ingestor = PineconeIngestor()
    documents = ingestor.load_processed_documents("processed_docs.json")
    ingestor.ingest_documents(documents)