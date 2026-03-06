# Canal de Notícias Backend

## Descrição

Este projeto é um backend automatizado para um canal de notícias que agrega feeds RSS de diversas fontes de notícias brasileiras. Ele processa as notícias mais recentes, evita duplicatas e publica automaticamente as novas entradas em um canal do Telegram. Utiliza o Supabase como banco de dados para rastrear os links já publicados.

## Funcionalidades

- **Agregação de Feeds RSS**: Coleta notícias de múltiplas fontes RSS configuradas.
- **Publicação no Telegram**: Envia mensagens formatadas para um canal do Telegram.
- **Controle de Duplicatas**: Verifica e armazena links já publicados para evitar republicações.
- **Limpeza Automática**: Remove links antigos (mais de 30 dias) para manter o banco limpo.
- **Processamento Seguro**: Trata erros de parsing e conexões com retry.

## Pré-requisitos

- Python 3.8 ou superior
- Conta no [Supabase](https://supabase.com/) para o banco de dados
- Bot do Telegram (obtenha o token via [@BotFather](https://t.me/botfather))

## Instalação

1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd canal_de_noticias_backend
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**:
   - No Windows:
     ```bash
     venv\Scripts\activate
     ```
   - No Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuração

### 1. Arquivo de Ambiente (.env)

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
TELEGRAM_TOKEN=seu_token_do_bot_telegram
SUPABASE_URL=sua_url_do_supabase
SUPABASE_KEY=sua_chave_do_supabase
```

- `TELEGRAM_TOKEN`: Token do seu bot do Telegram.
- `SUPABASE_URL`: URL do seu projeto Supabase (encontrada em Settings > API).
- `SUPABASE_KEY`: Chave anon/public do Supabase (encontrada em Settings > API).

### 2. Banco de Dados Supabase

Execute o script SQL `supabase-schema.sql` no seu projeto Supabase para criar a tabela necessária:

- Acesse o painel do Supabase > SQL Editor
- Cole e execute o conteúdo do arquivo `supabase-schema.sql`

### 3. Feeds RSS

O arquivo `feeds.json` contém a lista de feeds a serem monitorados. Você pode editar este arquivo para adicionar ou remover fontes:

```json
{
  "feeds": [
    {
      "name": "Nome da Fonte",
      "url": "https://exemplo.com/feed/"
    }
  ]
}
```

## Uso

Após a configuração, execute o script principal:

```bash
python main.py
```

O bot irá:
- Carregar os links já publicados do Supabase
- Limpar links antigos
- Processar cada feed RSS
- Publicar novas notícias no canal do Telegram
- Salvar os novos links no banco

### Execução Contínua

Para manter o bot rodando continuamente (ex: a cada hora), use um agendador como cron no Linux ou Task Scheduler no Windows.

Exemplo de cron (Linux/Mac):
```bash
0 * * * * /caminho/para/venv/bin/python /caminho/para/main.py
```

## Estrutura do Projeto

- `main.py`: Script principal com a lógica do bot
- `feeds.json`: Configuração dos feeds RSS
- `requirements.txt`: Dependências Python
- `supabase-schema.sql`: Schema do banco de dados
- `README.md`: Este arquivo

## Dependências

- `feedparser`: Para parsing de feeds RSS
- `requests`: Para chamadas à API do Telegram
- `beautifulsoup4`: Para limpeza de HTML nos resumos
- `python-dotenv`: Para carregamento de variáveis de ambiente
- `supabase`: Cliente Python para Supabase

## Logs

O script utiliza logging para registrar atividades. Os logs incluem:
- Conexão com Supabase
- Processamento de feeds
- Envios de mensagens
- Erros e warnings

## Tratamento de Erros

- Retry automático para falhas de envio no Telegram
- Validação de feeds malformados
- Continuação do processamento mesmo com erros em feeds individuais
