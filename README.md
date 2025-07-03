# SCHWordCloud

SCHWordCloud é uma ferramenta que cria nuvens de palavras baseadas em resultados de pesquisas obtidas no Google relacionadas a dados obtidos no SCH (Sistema de Certificação e Homologação), o sistema de certificação de produtos da Anatel.

## Visão geral

Este projeto busca dados de certificação de produtos, realiza buscas na web usando as APIs do Google e do Bing e gera nuvens de palavras com base nos resultados da busca. A ferramenta também gerencia anotações e mantém um histórico dos resultados da busca.

## Features

- Baixa e processa o banco de dados SCH da ANATEL
- Realiza buscas na web usando a API de Busca do Google
- Gera nuvens de palavras a partir dos resultados da busca
- Mantém o histórico de anotações dos resultados da busca
- Suporta compartilhamento de anotações baseado em nuvem
- Configurável por meio de arquivos de configuração TOML
- Sistema de registro abrangente

## Instalação

Clone o repositório disponível no GitHub:

```bash
git clone https://github.com/maxwelfreitas/SCHWordCloud.git
cd SCHWordCloud
pip install -e .
```

## Configuração

A aplicação requer um arquivo TOML

## Usage

### Command Line Interface

```bash
schwordcloud [-C CONFIG_FILE] [-V]
```

Options:
- `-C, --config_file`: Path to the configuration file. If not provided, the default config will be used.
- `-V, --verbose`: Increase output verbosity.

### Configuration

O aplicativo requer um arquivo de configuração no formato TOML com as seguintes seções:

1. **Repositório central de arquivos**
   ```toml
   [cloud]
   cloud_annotation_get_folder = "path/to/cloud/annotation/get/folder"
   cloud_annotation_post_folder = "path/to/cloud/annotation/post/folder"
   ```

2. **Credenciais de API**
   ```toml
   [credentials]
   credentials_file = "path/to/credentials/file"
   ```

   O arquivos de credenciais deve contes as chaves de API e demais configurações requeridas pelo mecanismo de busca do Google:
   ```toml
   [api_credentials.google_search]
   api_key = "your-google-api-key"
   engine_id = "your-google-engine-id"

   ```

## Data Structure

The application creates the following directory structure:

```
schwordcloud/                           # A pasta principal para o data_home do schwordcloud
└── datasets/                           # A pasta home dos dados
    ├── annotation/                     # Contém os arquivos de anotação
    |   ├── Annotation.xlsx             # Uma cópia do arquivo de anotação da nuvem
    |   └── AnnotationNull.xlsx         # Uma cópia do arquivo de anotação nula
    ├── sch/                            # Contém o arquivo do banco de dados SCH
    |   └── produtos_certificados.zip   # Arquivo do banco de dados SCH obtido da ANATEL
    └── search_results/                 # Contém os dados dos resultados da pesquisa
        └── search_history.parquet      # Histórico de pesquisa no formato Parquet
```

## Como Funciona

1. O aplicativo baixa o banco de dados SCH mais recente da Anatel
2. Extrai informações de certificação do produto
3. Para cada número de certificação, realiza buscas na web
4. Os resultados da busca são processados ​​para gerar nuvens de palavras
5. Os resultados são salvos como anotações com metadados
6. As anotações podem ser compartilhadas por meio de pastas na nuvem

### Observações
1. O aplicativo somente baixa o banco de dados mais recente da Anatel se o local não foi atualizado há mais de 180 dias. Para forçar a atualização, basta excluir o arquivo local.
2. As pesquisas são feitas pelo número de certificação, são considerados os números ainda não pesquisados de produtos homologados há mais de 180, valor que pode ser ajustado através do arquivo de configuração.

## Desenvolvimento

### Estrutura do Projeto

```
   src/schwordcloud/      # Pacote principal
├─── datamanager/         # Módulos de gerenciamento de dados
├─── websearch/           # Integrações com a API de busca na web
├─── config.py            # Manipulação de configuração
├─── config.toml          # Arquivo de configuração padrão
├─── runschwordcloud.py   # Ponto de entrada da CLI
└─── schwordcloud.py      # Classe principal do aplicativo
```

### Registro

O aplicativo registra informações em um arquivo (`schwordcloud.log`) e no console quando o modo detalhado está ativado.

## Author

Maxwel de Souza Freitas
