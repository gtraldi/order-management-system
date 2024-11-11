from datetime import datetime, timedelta

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"


db = SQLAlchemy(app)


class Cliente(db.Model):
    __tablename__ = "clientes"
    ClienteID = db.Column(db.Integer, primary_key=True)
    Nome = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Telefone = db.Column(db.String(15))
    EnderecoEntrega = db.Column(db.Text)
    Senha = db.Column(db.String(100))

    pedidos = db.relationship("Pedido", back_populates="cliente")

    def verificar_senha(self, senha):
        return self.Senha == senha


class Pedido(db.Model):
    __tablename__ = "pedidos"
    PedidoID = db.Column(db.Integer, primary_key=True)
    StatusPedido = db.Column(db.String(20))
    DataPedido = db.Column(db.DateTime)
    Observacao = db.Column(db.Text)
    ValorCompra = db.Column(db.Numeric(10, 2))
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.ClienteID"))
    cliente = db.relationship("Cliente", back_populates="pedidos")

    itens_do_pedido = db.relationship("ItemPedido", back_populates="pedido")


class ItemPedido(db.Model):
    __tablename__ = "itens_pedido"
    ItemID = db.Column(db.Integer, primary_key=True)
    PedidoID = db.Column(db.Integer, db.ForeignKey("pedidos.PedidoID"))
    ProdutoID = db.Column(db.Integer, db.ForeignKey("produtos.ProdutoID"))
    Quantidade = db.Column(db.Integer)
    PrecoUnitario = db.Column(db.Float)

    pedido = db.relationship("Pedido", back_populates="itens_do_pedido")

    produto = db.relationship("Produto", back_populates="itens")


class Produto(db.Model):
    __tablename__ = "produtos"
    ProdutoID = db.Column(db.Integer, primary_key=True)
    Nome = db.Column(db.String(100), nullable=False)
    Descricao = db.Column(db.String(200))
    Preco = db.Column(db.Float, nullable=False)

    itens = db.relationship("ItemPedido", back_populates="produto")


class HistoricoPedido(db.Model):
    __tablename__ = "historico_pedidos"
    HistoricoID = db.Column(db.Integer, primary_key=True)
    PedidoID = db.Column(
        db.Integer, db.ForeignKey("pedidos.PedidoID", ondelete="CASCADE")
    )
    StatusAnterior = db.Column(db.String(20))
    NovoStatus = db.Column(db.String(20))
    DataHistorico = db.Column(db.Date)
    DataAlteracao = db.Column(db.DateTime, default=datetime.utcnow)

    pedido = db.relationship("Pedido", backref=db.backref("historico", lazy=True))


class Notificacao(db.Model):
    __tablename__ = "notificacoes"
    NotificacaoID = db.Column(db.Integer, primary_key=True)
    PedidoID = db.Column(db.Integer, db.ForeignKey("pedidos.PedidoID"), nullable=False)
    TipoNotificacao = db.Column(db.String(20))
    Mensagem = db.Column(db.Text)
    DataEnvio = db.Column(db.DateTime, default=datetime.utcnow)

    pedido = db.relationship("Pedido", backref="notificacoes")


@app.route("/criar_pedido", methods=["GET", "POST"])
def criar_pedido():
    if request.method == "POST":

        if "cliente_id" not in session:
            flash("Você precisa estar logado para criar um pedido.", "danger")
            return redirect(url_for("login"))

        cliente_id = session["cliente_id"]
        cliente = Cliente.query.get(cliente_id)

        produto_id = request.form.get("produto_id")
        quantidade = int(request.form.get("quantidade"))
        observacao = request.form.get("observacao")

        produto = Produto.query.get(produto_id)

        if produto is None:
            flash("Produto não encontrado.", "danger")
            return redirect(url_for("criar_pedido"))

        preco_unitario = produto.Preco

        total = preco_unitario * quantidade

        novo_pedido = Pedido(
            StatusPedido="Em andamento",
            DataPedido=datetime.utcnow(),
            Observacao=observacao,
            ValorCompra=total,
            cliente_id=cliente.ClienteID,
        )
        db.session.add(novo_pedido)
        db.session.commit()

        item_pedido = ItemPedido(
            PedidoID=novo_pedido.PedidoID,
            ProdutoID=produto_id,
            Quantidade=quantidade,
            PrecoUnitario=preco_unitario,
        )
        db.session.add(item_pedido)

        historico_pedido = HistoricoPedido(
            PedidoID=novo_pedido.PedidoID,
            StatusAnterior="Criado",
            NovoStatus="Em andamento",
            DataAlteracao=datetime.utcnow(),
        )
        db.session.add(historico_pedido)
        db.session.commit()

        flash("Pedido criado com sucesso!", "success")
        return redirect(url_for("index"))

    produtos = Produto.query.all()
    return render_template("criar_pedido.html", produtos=produtos)


@app.route("/logout")
def logout():
    session.pop("cliente_id", None)
    flash("Você foi desconectado.", "info")
    return redirect(url_for("login"))


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")

        if senha != confirmar_senha:
            flash("As senhas não coincidem!", "danger")
            return redirect(url_for("login"))

        if Cliente.query.filter_by(Email=email).first():
            flash("Email já está em uso!", "danger")
            return redirect(url_for("login"))

        novo_cliente = Cliente(Nome=nome, Email=email, Senha=senha)
        db.session.add(novo_cliente)
        db.session.commit()

        flash("Usuário cadastrado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))


@app.route("/home", methods=["GET", "POST"])
def index():

    if "cliente_id" not in session:
        return redirect(url_for("login"))

    try:

        pedidos_recentem = Pedido.query.filter(
            Pedido.DataPedido >= datetime.utcnow() - timedelta(days=30)
        ).count()

        num_clientes = Cliente.query.count()
        num_produtos = Produto.query.count()

        vendas_totais = (
            db.session.query(
                db.func.sum(ItemPedido.Quantidade * ItemPedido.PrecoUnitario)
            ).scalar()
            or 0
        )

        pedidos = Pedido.query.filter(
            Pedido.DataPedido >= datetime.utcnow() - timedelta(days=30)
        ).all()

        for pedido in pedidos:
            pedido.itens = ItemPedido.query.filter(
                ItemPedido.PedidoID == pedido.PedidoID
            ).all()

    except Exception as e:

        print(f"Erro ao carregar dados para o dashboard: {e}")
        pedidos_recentem = 0
        num_clientes = 0
        num_produtos = 0
        vendas_totais = 0
        pedidos = []

    return render_template(
        "paginaInicial.html",
        pedidos_recentem=pedidos_recentem,
        num_clientes=num_clientes,
        num_produtos=num_produtos,
        vendas_totais=vendas_totais,
        pedidos=pedidos,
    )


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        cliente = Cliente.query.filter_by(Email=email).first()

        if cliente and cliente.Senha == senha:
            session["cliente_id"] = cliente.ClienteID
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("index"))

        flash("Email ou senha inválidos", "danger")

    return render_template("login.html")


@app.route("/editar_pedido/<int:pedido_id>", methods=["GET", "POST"])
def editar_pedido(pedido_id):

    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        flash("Pedido não encontrado.", "danger")
        return redirect(url_for("index"))

    item_pedido = pedido.itens_do_pedido[0]
    produto_atual = Produto.query.get(item_pedido.ProdutoID)

    usuario_especifico = session.get("cliente_id") == 1

    if request.method == "POST":

        produto_id = request.form.get("produto_id")
        quantidade = int(request.form.get("quantidade"))
        observacao = request.form.get("observacao")

        novo_produto = Produto.query.get(produto_id)
        if not novo_produto:
            flash("Produto não encontrado.", "danger")
            return redirect(url_for("editar_pedido", pedido_id=pedido_id))

        item_pedido.ProdutoID = produto_id
        item_pedido.Quantidade = quantidade
        item_pedido.PrecoUnitario = novo_produto.Preco
        pedido.Observacao = observacao

        pedido.ValorCompra = sum(
            item.Quantidade * item.PrecoUnitario for item in pedido.itens_do_pedido
        )

        if usuario_especifico:
            status_pedido = request.form.get("status_pedido")
            pedido.StatusPedido = status_pedido

        db.session.commit()

        flash("Pedido atualizado com sucesso!", "success")
        return redirect(url_for("index"))

    produtos = Produto.query.all()
    return render_template(
        "editar_pedido.html",
        pedido=pedido,
        produtos=produtos,
        usuario_especifico=usuario_especifico,
    )


@app.route("/excluir_pedido/<int:pedido_id>", methods=["GET"])
def excluir_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    historico_pedidos = HistoricoPedido.query.filter_by(PedidoID=pedido_id).all()
    if historico_pedidos:
        for historico in historico_pedidos:
            db.session.delete(historico)
        db.session.commit()

    try:
        db.session.delete(pedido)
        db.session.commit()
        flash("Pedido excluído com sucesso!", "success")
        return redirect(url_for("index"))
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir o pedido: {str(e)}", "danger")
        return redirect(url_for("index"))


@app.route("/produtos")
def produtos():
    produtos = Produto.query.all()
    return render_template("produtos.html", produtos=produtos)


produtos = [
    Produto(
        Nome="Camiseta Polo",
        Descricao="Camiseta Polo de algodão, confortável e de alta qualidade. Ideal para ocasiões casuais.",
        Preco=49.90,
    ),
    Produto(
        Nome="Tênis Esportivo",
        Descricao="Tênis esportivo de alta performance, ideal para corridas e atividades físicas.",
        Preco=159.99,
    ),
    Produto(
        Nome="Smartphone XYZ 12",
        Descricao="Smartphone com tela de 6.5 polegadas, 128GB de armazenamento e câmera de 48MP.",
        Preco=1999.90,
    ),
    Produto(
        Nome="Notebook Dell Inspiron",
        Descricao="Notebook Dell Inspiron com processador Intel i7, 16GB de RAM e 512GB de SSD.",
        Preco=3499.90,
    ),
    Produto(
        Nome="Caderno A4",
        Descricao="Caderno espiral tamanho A4 com 200 folhas, ideal para anotações escolares ou profissionais.",
        Preco=9.90,
    ),
    Produto(
        Nome="Cafeteira Elétrica",
        Descricao="Cafeteira elétrica de 1000W, para preparo rápido de café com filtro permanente.",
        Preco=129.90,
    ),
    Produto(
        Nome="Headphone Bluetooth",
        Descricao="Headphone com cancelamento de ruído, conexão Bluetooth e até 20 horas de bateria.",
        Preco=299.90,
    ),
    Produto(
        Nome='Monitor 24" Full HD',
        Descricao="Monitor de 24 polegadas com resolução Full HD, ideal para trabalhar e jogar.",
        Preco=899.90,
    ),
    Produto(
        Nome="Relógio de Pulso",
        Descricao="Relógio de pulso analógico com pulseira de couro, elegante e sofisticado.",
        Preco=89.90,
    ),
    Produto(
        Nome="Lâmpada LED",
        Descricao="Lâmpada LED de 10W, alta eficiência energética, com durabilidade de até 20.000 horas.",
        Preco=19.90,
    ),
]


with app.app_context():

    db.create_all()
    db.session.add_all(produtos)
    db.session.commit()
    print("Produtos inseridos com sucesso!")


if __name__ == "__main__":
    app.run(debug=True)
