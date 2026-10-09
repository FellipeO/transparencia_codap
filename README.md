# Portal da Transparência — CODAP

Aplicação web desenvolvida em **Python e Flask** para consulta de lançamentos financeiros e gerenciamento de usuários autorizados. O sistema utiliza um banco de dados MySQL, autenticação por meio do Google OAuth e controle de acesso por grupos de usuários.

> **Contexto:** projeto desenvolvido durante minha experiência profissional na Companhia de Desenvolvimento de Aparecida de Goiânia (CODAP). Este repositório apresenta parte da implementação técnica do sistema.

## Funcionalidades

- Consulta de lançamentos financeiros armazenados no MySQL.
- Autenticação de usuários com Google OAuth.
- Verificação de acesso com base nos e-mails cadastrados no sistema.
- Associação de usuários a grupos de acesso (`super_admin`, `admin` e `usuario`), com regras específicas para operações administrativas.
- Gerenciamento de usuários autorizados, incluindo cadastro, alteração de grupo e exclusão, restrito ao grupo `super_admin`.

## Tecnologias

- **Python**
- **Flask**
- **Flask-SQLAlchemy e SQLAlchemy**
- **MySQL** e `mysql-connector-python`
- **Authlib** para integração com Google OAuth
- **python-dotenv** para carregar configurações por variáveis de ambiente
- **HTML/Jinja e Bootstrap** para as páginas da aplicação

## Estrutura do projeto

```text
transparencia_codap/
├── app/
│   ├── __init__.py       # Inicialização da aplicação e extensões
│   ├── auth.py           # Autenticação e encerramento de sessão
│   ├── decorators.py     # Proteção de rotas que exigem login
│   ├── models.py         # Modelos de dados
│   └── routes.py         # Rotas principais e gerenciamento de usuários
├── config.py             # Configurações da aplicação
├── requirements.txt      # Dependências Python
├── run.py                # Ponto de entrada para execução local
└── .gitignore
```

## Pré-requisitos

Para executar a aplicação localmente, você precisará de:

- Python instalado;
- acesso a um banco de dados MySQL com as tabelas esperadas pela aplicação;
- credenciais OAuth de um cliente configurado no Google Cloud Console.

**Observação:** o repositório não inclui um processo de migração ou criação automática do esquema do banco. As tabelas e os dados necessários devem estar preparados antes de testar as funcionalidades que consultam o banco.

## Configuração local

### 1. Clonar o repositório

```bash
git clone https://github.com/FellipeO/transparencia_codap.git
cd transparencia_codap
```

### 2. Criar e ativar um ambiente virtual

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```dotenv
DATABASE_URL=mysql+mysqlconnector://USUARIO:SENHA@HOST:3306/NOME_DO_BANCO
SECRET_KEY=SUBSTITUA_POR_UMA_CHAVE_FORTE
GOOGLE_CLIENT_ID=SEU_CLIENT_ID
GOOGLE_CLIENT_SECRET=SEU_CLIENT_SECRET
```

Substitua os valores de exemplo pelas configurações do seu ambiente. Se a senha do banco contiver caracteres especiais, eles poderão precisar ser codificados para uso na URL de conexão.

O arquivo `.env` não deve ser enviado ao Git nem compartilhado, pois contém credenciais e configurações sensíveis.

### 5. Configurar o Google OAuth

No Google Cloud Console, configure um cliente OAuth e cadastre a URI de redirecionamento correspondente ao endereço local utilizado para acessar a aplicação. Por exemplo, ao executar localmente em `http://127.0.0.1:5000`, use:

```text
http://127.0.0.1:5000/auth/callback
```

Cadastre o `GOOGLE_CLIENT_ID` e o `GOOGLE_CLIENT_SECRET` no arquivo `.env`. A URI cadastrada no Google deve corresponder à URI utilizada pela aplicação.

### 6. Preparar o banco de dados

A aplicação espera, entre outras configurações, as seguintes tabelas:

- **`lancamentos`**: contém os dados dos lançamentos financeiros consultados pela aplicação.
- **`grupos_usuarios`**: relaciona os e-mails autorizados aos grupos de acesso. Os grupos presentes no código são `super_admin`, `admin` e `usuario`.

Cadastre apenas contas de teste autorizadas e utilize dados fictícios ou anonimizados em ambientes de desenvolvimento. Não inclua dados reais da empresa no repositório ou em capturas de tela.

### 7. Executar localmente

```bash
python run.py
```

Depois, acesse `http://127.0.0.1:5000` no navegador.

> O arquivo de execução atual habilita o modo de depuração. Utilize essa configuração somente para desenvolvimento local; antes de qualquer implantação, configure um servidor e parâmetros apropriados para produção, com o modo de depuração desativado.

## Segurança e uso de dados

- Não inclua chaves OAuth, senhas, tokens, arquivos `.env` ou dados pessoais/financeiros reais no repositório.
- Utilize credenciais e uma base de dados de teste em ambiente local.
- Antes de redistribuir ou reutilizar o código, confirme que você tem autorização para compartilhar os componentes desenvolvidos no contexto profissional.

## Observação

Este repositório é apresentado para fins de portfólio técnico. Não representa uma oferta de acesso ao sistema em produção nem disponibiliza credenciais ou dados operacionais.
