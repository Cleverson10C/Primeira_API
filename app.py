from flask import Flask, jsonify, request, make_response
from estrutura_banco_de_dados import Autor, Postagem, app, db
import json
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps

# Rota de proteção de token
def token_obrigatorio(f):   
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Verificar se um token foi enviado
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer '
                
        if not token:
            return jsonify({'Mensagem': 'Token não foi incluído!'}), 401
            
        # Se temos um token, validar acesso consultando o BD
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

# CORRIGIDO: Suporte a GET e POST para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return jsonify({
            'mensagem': 'Use método POST ou Basic Auth para fazer login',
            'exemplo': {
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': {'email': 'cleversonpassos35@gmail.com', 'senha': '123456'}
            }
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
            
        try:
            token = jwt.encode({
                'id_autor': usuario.id_autor, 
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            # Se token for bytes, converter para string
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            return jsonify({
                'Token': token,
                'usuario': usuario.to_dict(),
                'expires_in': '30 minutos'
            })
        except Exception as e:
            return jsonify({'erro': f'Erro ao gerar token: {str(e)}'}), 500
    
    # Basic Auth (método original)
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})
        
    usuario = Autor.query.filter_by(nome=auth.username).first()
    if not usuario:
        return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})
        
    if auth.password == usuario.senha:
        try:
            token = jwt.encode({
                'id_autor': usuario.id_autor, 
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            return jsonify({'Token': token})
        except Exception as e:
            return jsonify({'erro': f'Erro ao gerar token: {str(e)}'}), 500
            
    return make_response('Login inválido', 401, {'WWW-Authenticate': 'Basic realm="Login obrigatório"'})

# Rota principal - informações da API
@app.route('/')
def home():
    return jsonify({
        'mensagem': 'Bem-vindo à API de Autores e Postagens!',
        'versao': '1.0',
        'rotas_disponiveis': {
            'POST /login': 'Fazer login',
            'GET /postagens': 'Listar postagens (requer token)',
            'GET /autores': 'Listar autores (requer token)',
            'GET /autores/<id>': 'Obter autor específico (requer token)',
            'POST /autores': 'Criar autor (requer token)',
            'PUT /autores/<id>': 'Atualizar autor (requer token)',
            'DELETE /autores/<id>': 'Excluir autor (requer token)'
        },
        'autenticacao': {
            'usuario_padrao': 'Cleverson Passos',
            'senha_padrao': '123456',
            'email_padrao': 'cleversonpassos35@gmail.com'
        }
    })

# CORRIGIDO: Obter postagens
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

# CORRIGIDO: Obter autores
@app.route('/autores')
@token_obrigatorio
def obter_autores(autor_logado):  # Nome diferente para evitar conflito
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

# CORRIGIDO: Obter autor por id
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

# CORRIGIDO: Criar novo autor
@app.route('/autores', methods=['POST'])
@token_obrigatorio
def novo_autor(autor_logado):
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
            
        # Verificar campos obrigatórios
        if not all(key in dados for key in ['nome', 'email', 'senha']):
            return jsonify({'erro': 'Nome, email e senha são obrigatórios'}), 400
        
        # Verificar se email já existe
        autor_existente = Autor.query.filter_by(email=dados['email']).first()
        if autor_existente:
            return jsonify({'erro': 'Email já cadastrado'}), 400
        
        novo_autor_obj = Autor(
            nome=dados['nome'],
            senha=dados['senha'],
            email=dados['email'],
            admin=dados.get('admin', False)
        )

        db.session.add(novo_autor_obj)
        db.session.commit()

        return jsonify({
            'mensagem': 'Usuário criado com sucesso',
            'autor': novo_autor_obj.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# CORRIGIDO: Alterar autor
@app.route('/autores/<int:id_autor>', methods=['PUT'])
@token_obrigatorio
def alterar_autor(autor_logado, id_autor):
    try:
        dados = request.get_json()
        autor_para_alterar = Autor.query.filter_by(id_autor=id_autor).first()
        
        if not autor_para_alterar:
            return jsonify({'erro': 'Autor não encontrado'}), 404
            
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualizar campos se fornecidos
        if 'nome' in dados:
            autor_para_alterar.nome = dados['nome']
        if 'email' in dados:
            # Verificar se email já existe (exceto para o próprio autor)
            email_existente = Autor.query.filter_by(email=dados['email']).first()
            if email_existente and email_existente.id_autor != id_autor:
                return jsonify({'erro': 'Email já cadastrado'}), 400
            autor_para_alterar.email = dados['email']
        if 'senha' in dados:
            autor_para_alterar.senha = dados['senha']
        if 'admin' in dados and hasattr(autor_para_alterar, 'admin'):
            autor_para_alterar.admin = dados['admin']

        db.session.commit()
        return jsonify({
            'mensagem': 'Usuário alterado com sucesso!',
            'autor': autor_para_alterar.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# CORRIGIDO: Excluir autor
@app.route('/autores/<int:id_autor>', methods=['DELETE'])
@token_obrigatorio
def excluir_autor(autor_logado, id_autor):
    try:
        autor_existente = Autor.query.filter_by(id_autor=id_autor).first()
        if not autor_existente:
            return jsonify({'erro': 'Autor não encontrado'}), 404

        db.session.delete(autor_existente)
        db.session.commit()

        return jsonify({'mensagem': 'Autor excluído com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# CORRIGIDO: Configuração para produção e desenvolvimento
if __name__ == '__main__':
    # Detectar se está em produção
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')  # 0.0.0.0 para produção
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print("🚀 Iniciando API...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print("🔑 Credenciais padrão:")
    print("   - User: Cleverson Passos")
    print("   - Email: cleversonpassos35@gmail.com")
    print("   - Pass: 123456")
    
    app.run(
        host=host,
        port=port, 
        debug=debug
    )

