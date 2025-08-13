from flask import Flask, jsonify, request, make_response
from estrutura_banco_de_dados import Autor, Postagem, app, db
import json
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps

# NOVO: Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def token_obrigatorio(f):   
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                
        if not token:
            return jsonify({'Mensagem': 'Token não foi incluído!'}), 401
            
        try:
            resultado = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            autor = Autor.query.filter_by(id_autor=resultado['id_autor']).first()
            if not autor:
                return jsonify({'Mensagem': 'Usuário não encontrado'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'Mensagem': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'Mensagem': 'Token é inválido'}), 401
        except Exception as e:
            return jsonify({'Mensagem': f'Erro no token: {str(e)}'}), 401
            
        return f(autor, *args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'GET':
            return jsonify({
                'mensagem': 'Use método POST ou Basic Auth para fazer login',
                'exemplo': {
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'body': {'email': 'cleversonpassos35@gmail.com', 'senha': '123456'}
                },
                'status': 'API funcionando'
            })
        
        # POST - JSON login
        if request.method == 'POST' and request.is_json:
            dados = request.get_json()
            username = dados.get('email') or dados.get('nome')
            password = dados.get('senha')
            
            if not username or not password:
                return jsonify({'erro': 'Email/nome e senha são obrigatórios'}), 400
                
            usuario = Autor.query.filter(
                (Autor.nome == username) | (Autor.email == username)
            ).first()
            
            if not usuario or password != usuario.senha:
                return jsonify({'erro': 'Credenciais inválidas'}), 401
                
            token = jwt.encode({
                'id_autor': usuario.id_autor, 
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            return jsonify({
                'Token': token,
                'usuario': usuario.to_dict(),
                'expires_in': '30 minutos'
            })
        
        # Basic Auth
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})
            
        usuario = Autor.query.filter_by(nome=auth.username).first()
        if not usuario or auth.password != usuario.senha:
            return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})
            
        token = jwt.encode({
            'id_autor': usuario.id_autor, 
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            
        return jsonify({'Token': token})
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro interno no login: {str(e)}',
            'tipo': type(e).__name__
        }), 500

# NOVO: Rota de health check
@app.route('/health')
def health_check():
    try:
        # Testar conexão com banco
        total_autores = Autor.query.count()
        return jsonify({
            'status': 'OK',
            'database': 'conectado',
            'total_autores': total_autores,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'database': 'erro',
            'erro': str(e)
        }), 500

@app.route('/')
def home():
    return jsonify({
        'mensagem': 'API de Autores e Postagens funcionando!',
        'versao': '1.0',
        'deploy': 'Render',
        'rotas_disponiveis': {
            'GET /health': 'Status da API',
            'POST /login': 'Fazer login',
            'GET /postagens': 'Listar postagens (requer token)',
            'GET /autores': 'Listar autores (requer token)',
        },
        'autenticacao': {
            'usuario_padrao': 'Cleverson Passos',
            'senha_padrao': '123456',
            'email_padrao': 'cleversonpassos35@gmail.com'
        }
    })

# RESTO DAS ROTAS (mesmo código que você já tem)
@app.route('/postagens')
@token_obrigatorio
def obter_postagens(autor): 
    try:
        postagens = Postagem.query.all()
        list_postagens = []
        
        for postagem in postagens:
            postagem_atual = {
                'id_postagem': postagem.id_postagem,
                'titulo': postagem.titulo,
                'conteudo': postagem.conteudo,
                'id_autor': postagem.id_autor,
                'data_criacao': postagem.data_criacao.isoformat() if postagem.data_criacao else None
            }
            list_postagens.append(postagem_atual)
            
        return jsonify({
            'postagens': list_postagens,
            'total': len(list_postagens)
        })
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route('/autores')
@token_obrigatorio
def obter_autores(autor_logado):
    try:
        autores = Autor.query.all()
        lista_de_autores = []
        
        for autor_item in autores:
            autor_atual = {
                'id_autor': autor_item.id_autor,
                'nome': autor_item.nome,
                'email': autor_item.email,
                'admin': autor_item.admin if hasattr(autor_item, 'admin') else False
            }
            lista_de_autores.append(autor_atual)

        return jsonify({
            'autores': lista_de_autores,
            'total': len(lista_de_autores)
        })
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# [RESTO DAS SUAS ROTAS - mesmo código]
@app.route('/autores/<int:id_autor>', methods=['GET'])
@token_obrigatorio
def obter_autor_por_id(autor_logado, id_autor):
    try:
        autor_encontrado = Autor.query.filter_by(id_autor=id_autor).first()
        if not autor_encontrado:
            return jsonify({'erro': 'Autor não encontrado'}), 404
            
        autor_atual = {
            'id_autor': autor_encontrado.id_autor,
            'nome': autor_encontrado.nome,
            'email': autor_encontrado.email,
            'admin': autor_encontrado.admin if hasattr(autor_encontrado, 'admin') else False
        }

        return jsonify({'autor': autor_atual})
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# CORRIGIDO: Configuração final
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # CORRIGIDO: Para Render sempre usar 0.0.0.0
    app.run(host='0.0.0.0', port=port, debug=False)
