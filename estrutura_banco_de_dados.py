from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Criar a instância da aplicação Flask
app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' \
'postgres:kgpPvAweRIhgSRwj@db.bmornebvmwqbznoeweke.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['x-access-token'] = 'x-access-token'
app.config['SECRET_KEY'] = 'sua-chave-super-secreta-render-123456'

# Inicializar o SQLAlchemy
db = SQLAlchemy(app)

# Modelo/Classe Autor
class Autor(db.Model):
    __tablename__ = 'autor'
    
    id_autor = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Autor {self.nome}>'
    
    def to_dict(self):
        return {
            'id_autor': self.id_autor,
            'nome': self.nome,
            'email': self.email,
            'admin': self.admin
        }

# NOVA: Classe Postagem para compatibilidade com app.py
class Postagem(db.Model):
    __tablename__ = 'postagem'
    
    id_postagem = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    id_autor = db.Column(db.Integer, db.ForeignKey('autor.id_autor'), nullable=False)
    
    # Relacionamento
    autor_rel = db.relationship('Autor', backref='postagens')
    
    def __repr__(self):
        return f'<Postagem {self.titulo}>'
    
    def to_dict(self):
        return {
            'id_postagem': self.id_postagem,
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'id_autor': self.id_autor
        }

def inicializar_banco():
    """Função para inicializar o banco de dados"""
    try:
        print("🔄 Inicializando banco de dados...")
        
        # CORRIGIDO: Primeiro drop, depois create
        db.drop_all()  # Limpar primeiro
        print("✅ Tabelas antigas removidas")
        
        db.create_all()  # Criar depois
        print("✅ Tabelas criadas com sucesso")
        
        # Verificar se já existe um admin
        admin_existente = Autor.query.filter_by(email='cleversonpassos35@gmail.com').first()
        
        if not admin_existente:
            # Criar usuário administrador
            autor_admin = Autor(
                nome='Cleverson Passos',
                email='cleversonpassos35@gmail.com',
                senha='123456',
                admin=True
            )
            
            db.session.add(autor_admin)
            db.session.commit()
            print(f"✅ Usuário admin criado: {autor_admin.email}")
            
            # Criar postagem de exemplo
            postagem_exemplo = Postagem(
                titulo='Bem-vindo à API!',
                conteudo='Esta é uma postagem de exemplo criada automaticamente.',
                id_autor=autor_admin.id_autor
            )
            
            db.session.add(postagem_exemplo)
            db.session.commit()
            print("✅ Postagem de exemplo criada")
            
        else:
            print("✅ Usuário admin já existe")
            
        print("🎉 Banco de dados inicializado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        db.session.rollback()
        return False

# EXECUTAR apenas se o arquivo for chamado diretamente
if __name__ == '__main__':
    with app.app_context():
        inicializar_banco()
        
        # Testar se está funcionando
        total_autores = Autor.query.count()
        total_postagens = Postagem.query.count()
        
        print(f"📊 Total de autores: {total_autores}")
        print(f"📊 Total de postagens: {total_postagens}")
        
        if total_autores > 0:
            primeiro_autor = Autor.query.first()
            print(f"👤 Primeiro autor: {primeiro_autor.nome} ({primeiro_autor.email})")

# IMPORTANTE: Remover a execução automática que estava causando problema
# Agora só executa quando chamado diretamente, não na importação
