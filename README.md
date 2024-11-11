
# Sistema de Gerenciamento de Pedidos

Este é um sistema de gerenciamento de pedidos baseado em Flask, que oferece funcionalidades de controle de pedidos, produtos, clientes e histórico de notificações.

## Funcionalidades Principais

- **Autenticação de Clientes**: Permite login e logout de clientes.
- **Gerenciamento de Pedidos**: Criação, edição, visualização e exclusão de pedidos. Cada pedido pode conter múltiplos itens.
- **Catálogo de Produtos**: Listagem de produtos disponíveis para compra.
- **Histórico de Pedidos e Notificações**: Registro das atualizações de status dos pedidos e notificações relacionadas.
- **Interface Web**: Interface de usuário construída usando HTML, renderizada com `render_template` do Flask.

## Estrutura do Projeto

- `app.py`: Contém toda a lógica da aplicação, incluindo a definição de rotas, modelos, e interações com o banco de dados.
- `requirements.txt`: Lista de dependências necessárias para o projeto.
- `templates`: Pasta que contém todos os arquivos html do projeto.
- `instance`: Contém o banco de dados utilizado no projeto.

## Modelos de Dados

1. **Cliente**:
   - Armazena informações sobre o cliente, como nome, email e telefone.
   - Relacionado aos modelos `Pedido` (1:N).

2. **Pedido**:
   - Representa um pedido feito pelo cliente, incluindo informações como data, status, valor total e observações.
   - Relacionado ao `Cliente` e ao `ItemPedido`.

3. **ItemPedido**:
   - Detalha os itens individuais em um pedido, incluindo quantidade e preço unitário.
   - Relacionado ao `Pedido` e ao `Produto`.

4. **Produto**:
   - Representa um produto disponível para compra com nome, descrição e preço.
   - Relacionado aos `ItemPedido`.

5. **HistoricoPedido**:
   - Armazena o histórico de alterações de status de um pedido.

6. **Notificacao**:
   - Armazena notificações relacionadas a um pedido.

## Dependências

As dependências da aplicação estão listadas no arquivo `requirements.txt`:

- `Flask`: Framework web para desenvolvimento da aplicação.
- `SQLAlchemy`: ORM para gerenciamento do banco de dados.
- `gunicorn`: Servidor WSGI usado para o deploy da aplicação.

### Instalação

1. Clone este repositório:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Executando o Projeto

Para rodar a aplicação em modo de desenvolvimento:

```bash
python app.py
```
