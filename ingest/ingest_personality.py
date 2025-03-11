import os
import requests
from bs4 import BeautifulSoup
import re

import openai
import pinecone
import time
import tiktoken
from unidecode import unidecode  # importa a função para normalizar


# ================= CONFIGURAÇÃO =================
INDEX_NAME = "sw-index"  
MAX_TOKENS = 500  
REQUEST_SLEEP = 1  # segundos para evitar rate limiting

openai.api_key = os.environ.get("OPENAI_API_KEY")

pc = pinecone.Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.environ.get("PINECONE_ENV")
)
index = pc.Index(INDEX_NAME)
# =================================================

def clean_references(text):
    """Remove referências no formato [número]"""
    return re.sub(r'\[\d+\]', '', text)

def extract_section(soup, section_id):
    """
    Extrai o conteúdo da seção identificada pelo id (ex: "Personality_and_traits").
    Procura o <span class="mw-headline" id="section_id"> e coleta os elementos até o próximo cabeçalho.
    """
    headline = soup.find('span', {'class': 'mw-headline', 'id': section_id})
    if not headline:
        return ""
    header = headline.parent
    section_content = []
    for sibling in header.find_next_siblings():
        if sibling.name in ['h2', 'h3'] and sibling.find('span', {'class': 'mw-headline'}):
            break
        section_content.append(sibling.get_text(separator=" ", strip=True))
    return "\n\n".join(section_content)

def chunk_text(text, max_tokens=MAX_TOKENS):
    """
    Divide o texto em chunks com base no número máximo de tokens utilizando tiktoken.
    Retorna uma lista de strings, cada uma com até max_tokens.
    """
    # Obtém o encoding para o modelo text-embedding-ada-002
    enc = tiktoken.encoding_for_model("text-embedding-ada-002")
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
        chunk = enc.decode(chunk_tokens)
        chunks.append(chunk)
    return chunks

def get_embedding(text):
    """Gera o embedding para o texto usando o modelo text-embedding-ada-002."""
    response = openai.embeddings.create(input=text, model="text-embedding-ada-002")
    # Acessa a propriedade data[0].embedding
    return response.data[0].embedding

def get_swapi_characters():
    """
    Obtém a lista de personagens da SWAPI.
    Retorna uma lista de dicionários, onde cada um contém pelo menos o campo 'name'.
    """
    url = "https://swapi.dev/api/people/"
    characters = []
    while url:
        response = requests.get(url)
        data = response.json()
        characters.extend(data.get('results', []))
        url = data.get('next')
    return characters

def scrape_personality_and_traits(character_name):
    """
    Dado o nome de um personagem, monta a URL da Wookieepedia e extrai a seção "Personality and traits".
    """
    base_url = "https://starwars.fandom.com/wiki/"
    name_for_url = character_name.replace(" ", "_")
    url = base_url + name_for_url
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erro ao acessar {url} para {character_name}")
        return None
    soup = BeautifulSoup(response.content, 'html.parser')
    section_text = extract_section(soup, "Personality_and_traits")
    section_text = clean_references(section_text)
    return section_text.strip()

def sanitize_id(text):
    """
    Remove ou converte caracteres não-ASCII para garantir que o ID seja ASCII.
    """
    return unidecode(text)

def ingest_personality_data():
    characters = get_swapi_characters()
    all_records = []
    for char in characters:
        name = char.get('name')
        print(f"Processando {name}...")
        personality_text = scrape_personality_and_traits(name)
        if not personality_text:
            print(f"Sem dados de personality para {name}")
            continue
        chunks = chunk_text(personality_text)
        for i, chunk in enumerate(chunks):
            emb = get_embedding(chunk)
            raw_id = f"{name.replace(' ', '_')}_personality_{i}"
            record_id = sanitize_id(raw_id)
            metadata = {
                "character": name,
                "section": "Personality and traits",
                "chunk_index": i,
                "text": chunk
            }
            record = {"id": record_id, "values": emb, "metadata": metadata}
            all_records.append(record)
            time.sleep(REQUEST_SLEEP)
    # Upsert em batches (exemplo: 100 por batch)
    if all_records:
        batch_size = 100
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i+batch_size]
            index.upsert(vectors=batch)
        print("Dados de personality e traits inseridos com sucesso.")
    else:
        print("Nenhum registro para inserir.")


if __name__ == "__main__":
    ingest_personality_data()
