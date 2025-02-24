from flask import Flask, request
import requests
import json

app = Flask(__name__)

@app.route('/')
def index():
    # Form simples em HTML com UTF-8
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <title>Star Wars Narrativa</title>
</head>
<body>
  <h1>Gerador de Histórias Star Wars</h1>
  <form action="/gerar" method="post">
    <label>Personagens (separados por vírgula):</label><br/>
    <input type="text" name="personagens" value="Luke Skywalker, Leia Organa"/><br/><br/>

    <label>Planetas (separados por vírgula):</label><br/>
    <input type="text" name="planetas" value="Tatooine"/><br/><br/>

    <label>Naves (separadas por vírgula):</label><br/>
    <input type="text" name="naves" value="X-Wing"/><br/><br/>

    <button type="submit">Gerar História</button>
  </form>
</body>
</html>
'''

@app.route('/gerar', methods=['POST'])
def gerar():
    # Coletar dados do formulário
    personagens_str = request.form.get('personagens', '')
    planetas_str = request.form.get('planetas', '')
    naves_str = request.form.get('naves', '')

    # Transformar em listas
    personagens_list = [x.strip() for x in personagens_str.split(',') if x.strip()]
    planetas_list = [x.strip() for x in planetas_str.split(',') if x.strip()]
    naves_list = [x.strip() for x in naves_str.split(',') if x.strip()]

    # Montar payload JSON para Lambda
    payload = {
        "personagens": personagens_list,
        "planetas": planetas_list,
        "naves": naves_list
    }

    # URL do seu endpoint Lambda (local ou produção)
    lambda_url = 'https://f3riutkvbi.execute-api.us-west-2.amazonaws.com/Prod/historia'
    # lambda_url = "http://127.0.0.1:3000/historia"

    try:
        resp = requests.post(lambda_url, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            # Se retornou {"narrativa": "..."} exibimos o texto
            if "narrativa" in data:
                narrativa = data["narrativa"]
                return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <title>História Gerada</title>
</head>
<body>
  <h2>História Gerada:</h2>
  <pre>{narrativa}</pre>
  <p><a href="/">Voltar</a></p>
</body>
</html>
"""
            # Se retornou {"error": "..."} ou outra estrutura
            else:
                return f"<h2>Resposta inesperada</h2><pre>{json.dumps(data, ensure_ascii=False, indent=2)}</pre>"
        else:
            # Erro HTTP
            return f"<h2>Erro HTTP {resp.status_code}</h2><pre>{resp.text}</pre>"
    except Exception as e:
        # Erro de conexão ou outro
        return f"<h2>Erro ao chamar Lambda:</h2><pre>{str(e)}</pre>"

if __name__ == '__main__':
    # Rodar servidor Flask em localhost:5000
    app.run(debug=True, port=5000)
