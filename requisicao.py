import requests

# Configuração
BASE_URL = 'http://localhost:5000'

try:
    # 1. Login
    print("1. Fazendo login...")
    login_response = requests.post(f'{BASE_URL}/login', json={
        "email": "cleversonpassos35@gmail.com",
        "senha": "123456"
    })
    
    print(f"Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # 2. Obter token
        token = login_response.json()['token']
        print(f"✅ Token: {token[:15]}...")
        
        # 3. Buscar autores
        print("\n2. Buscando autores...")
        autores_response = requests.get(f'{BASE_URL}/autores', 
                                      headers={'x-access-token': token})
        
        print(f"Status: {autores_response.status_code}")
        print("Autores:", autores_response.json())
        
    else:
        print("❌ Erro:", login_response.text)

except Exception as e:
    print(f"❌ Erro: {e}")