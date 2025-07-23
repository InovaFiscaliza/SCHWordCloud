# SCHWordCloud

SCHWordCloud é uma ferramenta que cria nuvens de palavras baseadas em resultados de pesquisas obtidas no Google relacionadas a dados obtidos no SCH (Sistema de Certificação e Homologação), o sistema de certificação de produtos da Anatel.

## Visão geral

Este projeto busca dados de certificação de produtos, realiza buscas na web usando as APIs do Google e do Bing e gera nuvens de palavras com base nos resultados da busca. A ferramenta também gerencia anotações e mantém um histórico dos resultados da busca.

## Como funciona

1. O aplicativo baixa o banco de dados SCH mais recente da Anatel
2. Extrai informações de certificação do produto
3. Para cada número de certificação, realiza buscas na web
4. Os resultados da busca são processados ​​para gerar nuvens de palavras
5. Os resultados são salvos como anotações com metadados
6. As anotações são consolidadas por meio de pastas na nuvem

### Outras características do funcionamento:

- Mantém o histórico de anotações dos resultados da busca
- Configurável por meio de arquivos de configuração TOML

### Observações
- O aplicativo somente baixa o banco de dados mais recente da Anatel se o local não foi atualizado há mais de 180 dias. Para forçar a atualização, basta excluir o arquivo local.
- As pesquisas são feitas pelo número de certificação, por padrão são considerados os números ainda não pesquisados de produtos homologados há mais de 180, valor que pode ser ajustado através da configuração do período de graça (```grace_period```) do arquivo de configuração.

## Instalação

### Crie o arquivo de configuração

O aplicativo requer um arquivo de configuração no formato TOML com as seguintes seções:

```toml
# Repositório local de arquivos
data_home = "path/to/local/datasets/folder"

# Repositório central de arquivos
[cloud]
cloud_annotation_get_folder = "path/to/cloud/annotation/get/folder"
cloud_annotation_post_folder = "path/to/cloud/annotation/post/folder"

# Credenciais de API
[credentials]
credentials_file = "path/to/credentials/file"

# Configurações opcionais de busca
[search_params]
category = 2         # categoria de produtos para buscar
grace_period = 120   # período de graça
shuffle = true       # ordena aleatoriamente os números de homologação antes da busca
```

### Crie o arquivo de credenciais

O arquivos de credenciais deve conter as chaves de API e demais configurações requeridas pelos mecanismos de busca:

```toml
[google_search]
google_search_api_key = "google/search/api/key"
google_search_engine_id = "google/search/engine/id"
google_search_endpoint = "https://www.googleapis.com/customsearch/v1"
```

### Clone o repositório disponível no GitHub e crie o ambiente virtual:

```bash
git clone https://github.com/maxwelfreitas/SCHWordCloud.git
cd SCHWordCloud
uv sync
```

### Execute o aplicativo

```bash
uv run schwordcloud [-C CONFIG_FILE] [-V]
```

Argumentos:
- `-C, --config_file`: Caminho para o arquivo de configuração. Se não for fornecido, a configuração padrão será usada.
- `-V, --verbose`: Se ativado, aumenta a quantidade de informações exibida no console.


#### Observações
1. A versão atual do aplicativo realiza buscas apenas no Google

## Estrutura de dados

O aplicativo cria a seguinte estrutura de diretório:

```
schwordcloud/                           # A pasta principal para o data_home do schwordcloud
└── datasets/                           # A pasta home dos dados
    ├── annotation/                     # Contém os arquivos de anotação
    |   ├── Annotation.xlsx             # Uma cópia do arquivo de anotação da nuvem
    |   └── AnnotationNull.parquet      # Uma cópia do arquivo de anotação nula
    ├── sch/                            # Contém o arquivo do banco de dados SCH
    |   └── produtos_certificados.zip   # Arquivo do banco de dados SCH obtido da ANATEL
    └── search_results/                 # Contém os dados dos resultados da pesquisa
        └── search_history.parquet      # Histórico de pesquisa no formato Parquet
```


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

## Autor

Maxwel de Souza Freitas