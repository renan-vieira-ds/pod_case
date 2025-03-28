import requests
from typing import List, Dict
import json

from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()

class SWAPIPreprocessor:
    def __init__(self):
        self.endpoints = ['people', 'planets', 'films', 'species', 'vehicles', 'starships']
        self.entity_cache = self._build_entity_cache()

    def _build_entity_cache(self) -> Dict[str, Dict]:
        """Coleta e armazena todas as entidades da SWAPI"""
        cache = {ep: {} for ep in self.endpoints}
        
        for ep in self.endpoints:
            url = f"https://swapi.dev/api/{ep}/"
            while url:
                response = requests.get(url)
                data = response.json()
                for item in data['results']:
                    item_id = item['url'].split('/')[-2]
                    cache[ep][item_id] = {
                        'name': item.get('name') or item.get('title'),
                        'data': item
                    }
                url = data.get('next')
        return cache

    def _resolve_relations(self, entity_data: Dict) -> Dict:
        """Substitui URLs por nomes de entidades relacionadas"""
        processed = {}
        for key, value in entity_data.items():
            if key == 'url':
                processed['url'] = value
                continue
                
            if isinstance(value, list):
                processed[key] = [
                    self.entity_cache[url.split('/')[-3]][url.split('/')[-2]]['name']
                    for url in value
                ]
            elif isinstance(value, str) and value.startswith('https://'):
                parts = value.split('/')
                processed[key] = self.entity_cache[parts[-3]][parts[-2]]['name']
            else:
                processed[key] = value
        return processed

    def generate_documents(self) -> List[Document]:
        """Gera documentos LangChain formatados"""
        documents = []
        for ep in self.endpoints:
            for entity_id, entity in self.entity_cache[ep].items():
                processed = self._resolve_relations(entity['data'])
                
                metadata = {
                    'entity_type': ep,
                    'swapi_id': entity_id,
                    'name': processed.get('name') or processed.get('title'),
                    'source_url': processed['url']
                }
                
                content = "\n".join(
                    f"{k.replace('_', ' ').title()}: {v}" 
                    for k, v in processed.items() 
                    if k != 'url'
                )
                
                documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
        return documents

if __name__ == "__main__":
    processor = SWAPIPreprocessor()
    docs = processor.generate_documents()
    
    # Salvar em arquivo no formato LangChain-compatível
    processed_data = [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata
        } 
        for doc in docs
    ]
    
    with open("processed_docs.json", "w") as f:
        json.dump(processed_data, f)
    
    print(f"Documentos salvos em 'processed_docs.json'")