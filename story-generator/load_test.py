import asyncio
import aiohttp
import time
import json
from datetime import datetime

async def make_request(session, url, payload, request_id):
    try:
        start_time = time.time()
        async with session.post(url, json=payload) as response:
            elapsed = time.time() - start_time
            return {
                'request_id': request_id,
                'status': response.status,
                'time': elapsed,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {
            'request_id': request_id,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def load_test(url, requests_per_second, duration_seconds):
    # Exemplo de payload
    payload = {
        "personagens": ["Luke Skywalker", "Darth Vader"],
        "planetas": ["Tatooine"],
        "naves": ["Millennium Falcon"]
    }
    
    results = []
    total_requests = requests_per_second * duration_seconds
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(total_requests):
            # Distribuir requests ao longo do tempo
            delay = (i % requests_per_second) / requests_per_second
            await asyncio.sleep(delay)
            
            task = asyncio.create_task(
                make_request(session, url, payload, i)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
    
    # Análise dos resultados
    successful = len([r for r in results if r['status'] == 200])
    failed = len(results) - successful
    avg_time = sum(r['time'] for r in results if 'time' in r) / len(results)
    
    print(f"\nResultados do Teste de Carga:")
    print(f"Total de requests: {len(results)}")
    print(f"Sucesso: {successful}")
    print(f"Falhas: {failed}")
    print(f"Tempo médio: {avg_time:.2f}s")
    
    # Salvar resultados detalhados
    with open('load_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    API_URL = "sua_api_url_aqui"
    REQUESTS_PER_SECOND = 5  # Ajuste conforme necessário
    DURATION_SECONDS = 60    # 1 minuto de teste
    
    print(f"Iniciando teste de carga:")
    print(f"- {REQUESTS_PER_SECOND} requests/segundo")
    print(f"- Duração: {DURATION_SECONDS} segundos")
    print(f"- Total: {REQUESTS_PER_SECOND * DURATION_SECONDS} requests")
    
    asyncio.run(load_test(API_URL, REQUESTS_PER_SECOND, DURATION_SECONDS))
