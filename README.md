# climate

Índices oceânicos (NINO3.4, TSA e AMM) e previsão mensal da chuva do Nordeste do Brasil em quintis: defasagens aferidas, calibração e três modelos (Ridge, Random Forest e rede neural densa).

*English summary.* This repository holds the notebook, runner and checks used to test whether lagged associations between three oceanic indices and monthly CHIRPS rainfall in three regions of Northeast Brazil translate into out-of-sample monthly forecast skill. Each model is compared with the same model without the index. The notebook downloads all input data from the original sources, fixes every random seed and writes a SHA-256 manifest of its outputs.

## O que o estudo pergunta

As associações defasadas entre cada índice e a chuva mensal se traduzem em habilidade de previsão fora da amostra? Cada índice é avaliado sozinho, em três alvos (NNEB, INEB e ENEB), em três casos (ano hidrológico, estação chuvosa e estação seca), no alvo inteiro e em cada pixel de 0,05°.

São avaliadas três famílias de modelos preditivos: regressão linear regularizada (Ridge), conjunto de árvores (Random Forest) e rede neural com uma camada oculta.

O desenho separa três coisas:

- **Associação:** correlação defasada, aferida em 1981–2010.
- **Habilidade preditiva:** RPSS de cada modelo sobre o mesmo modelo sem o índice, em 2011–2025.
- **Interpretação física:** é leitura das evidências, sem efeito causal estimado.

## Resultado principal e limites

Números da execução completa publicada (tabelas em `resultados/completo/tabelas`; conferência em `conferencia_publicacao_completo.md`):

- **Associação (1981–2010):** detectada em 11 das 27 combinações de alvo, caso e índice após correção para testes múltiplos (NINO3.4 em 6, TSA em 4, AMM em 1), com |r| de 0,19 a 0,39.
- **Previsão (2011–2025):** nenhuma das 81 hipóteses de ganho foi confirmada. Os maiores ganhos sobre o controle sem índice ficaram no norte (NNEB), abaixo de 6 % de RPSS, com q ≥ 0,069.
- **Previsões perto da climatologia:** na Ridge e na rede neural, as probabilidades ficam a no máximo 3,9 pontos percentuais de 20 %, e os intervalos de confiança da Ridge (condicionais às previsões, não simultâneos) excluem ganhos maiores que 3,1 % de RPSS. Na configuração avaliada, a Random Forest afasta-se até 20,5 pontos de 20 % e varia de −16,6 % a +5,6 % de RPSS sobre o controle, sem nenhum ganho confirmado.
- **Leitura:** associação defasada não implicou habilidade mensal confirmável com índices isolados, neste protocolo e neste período de teste. Ausência de confirmação não é ausência de efeito.

Os limites estão em "Alcance e limites declarados" e em `artigo/LEIAME.md`.

## Períodos

| uso | anos |
|---|---|
| dados de chuva (CHIRPS v2.0 mensal) | 1981–2025 (45 anos) |
| referência final: quintis, classes, climatologia N, defasagens e ajuste final | jan/1981–dez/2010 |
| calibração interna: entrada e hiperparâmetros | treino jan/1981–dez/1995 e validação jan/1996–dez/2010, com quantis próprios do treino interno |
| teste | jan/2011–dez/2025 |

Cada papel é uma janela civil comum aos três alvos, e só entram anos hidrológicos com os 12 meses dentro dela. Por isso o NNEB (ano de jan a dez) tem 30 anos de referência, 15 + 15 de calibração e 15 de teste, e o INEB (nov a out) e o ENEB (mar a fev) têm 29, 14 + 14 e 14. Nenhum mês de teste de qualquer alvo entra na escolha compartilhada da calibração.

## Alcance e limites declarados

- O período de teste foi examinado durante o desenvolvimento do estudo. As escolhas de configuração foram fixadas com 1981–2010, mas a avaliação não é um teste inteiramente não visto.
- O valor-p da hipótese vem do deslocamento circular do índice, com passo de 4 meses por custo computacional. O menor valor-p possível é 1/131; por isso, com Benjamini e Hochberg sobre 27 combinações, um q < 0,05 exige pelo menos cinco combinações do mesmo método com valor-p no piso.
- O teste por deslocamento foi verificado só com a Ridge, só no alvo inteiro e num cenário com a tendência do índice. Pela hipótese nula declarada, a tendência comum conta como informação do índice; as rejeições nesse cenário medem a sensibilidade do teste à tendência, e não erro tipo I. A verificação não se estende aos outros modelos nem aos mapas.
- A inferência é condicional à configuração escolhida na calibração, e os intervalos de confiança são marginais e não simultâneos.
- Os mapas pixel a pixel são exploratórios: a significância é controlada pela taxa de falsas descobertas e lida junto com a magnitude.

## Conteúdo

| arquivo | o que é |
|---|---|
| `climate.ipynb` | o notebook do estudo, já executado e com todas as saídas (tabelas, figuras e textos): capa metodológica, Aquisição, Seções 1 a 10 e Fechamento |
| `executar_tudo.bat`, `executar_tudo.py` | pipeline completo: kernel, piloto, conferência do piloto, estudo completo, conferência da release e scripts do artigo |
| `rodar_climate.py` | executor do notebook no terminal, com previsão de término de cada seção a cada 2 h; ao fim da execução completa, grava as saídas em `climate.ipynb` |
| `conferir_publicacao.py`, `conferencia_publicacao_completo.md` | conferência da release (ver abaixo) e o seu relatório para esta execução |
| `requirements.txt` | dependências diretas, com versão fixa |
| `requirements-lock-windows.txt` | ambiente completo da execução de referência no Windows |
| `resultados/completo/` | tabelas, figuras, previsões, mapas, registros e manifesto SHA-256 (incluído na release) |
| `dados/registro.json` | URL, data de acesso, tamanho e SHA-256 de cada arquivo de dados usado |
| `artigo/` | scripts que leem os resultados e geram os diagnósticos, os números, as figuras e as tabelas do artigo (`artigo/LEIAME.md`) |
| `LICENSE`, `LICENSE-RESULTADOS.md`, `CITATION.cff` | licenças e citação |

## Ambiente

Execução de referência: Windows 11, Python 3.13.15, PyTorch 2.14.1 de CPU, 12 núcleos. O piloto também foi conferido no Linux com Python 3.13.17.

Os comandos abaixo são para o PowerShell, dentro da pasta do repositório. Eles chamam o Python do ambiente diretamente, sem `Activate.ps1`. No Linux ou no macOS, troque `.\.venv\Scripts\python.exe` por `.venv/bin/python`.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --user --name climate --display-name "Python (climate)"
```

Para reproduzir exatamente o ambiente de referência no Windows, use `requirements-lock-windows.txt` no lugar das duas linhas de instalação do PyTorch e do `requirements.txt`.

Para conferir o kernel, rode os dois comandos abaixo. A linha `climate` precisa aparecer, e o `argv` precisa começar pelo `python.exe` de `.venv`.

```powershell
.\.venv\Scripts\python.exe -m jupyter kernelspec list
.\.venv\Scripts\python.exe -c "from jupyter_client.kernelspec import KernelSpecManager as K; print(K().get_kernel_spec('climate').argv)"
```

O executor também confere isso antes de começar: ele só roda com o Python de `.venv` e com o kernel `climate` apontando para esse mesmo Python.

## Execução

O pipeline inteiro roda com um comando, que para na primeira etapa com erro:

```powershell
.\executar_tudo.bat
```

São nove etapas: kernel, piloto, conferência do piloto, estudo completo, conferência da release e os quatro scripts do artigo (diagnósticos, números, figuras e tabelas). Para rodar só o notebook:

```powershell
.\.venv\Scripts\python.exe rodar_climate.py --modo piloto   # conferência rápida, resultados/piloto
.\.venv\Scripts\python.exe rodar_climate.py                 # estudo completo, resultados/completo
```

- **Dados:** na primeira execução, o notebook baixa os dados das fontes originais (CHIRPS, NOAA PSL e IBGE) para `dados/` e registra cada arquivo. É preciso internet nessa etapa. Nada é lido de fora da pasta.
- **Progresso:** o terminal mostra a previsão de término de cada seção a cada 2 h.
- **Retomada:** Ctrl+C interrompe, e o mesmo comando retoma de onde parou. A pasta de resultados só é reaproveitada se os dados (valores), o código, a configuração, as versões das bibliotecas e o ambiente de execução forem os mesmos. Cada arquivo gravado é conferido pelo conteúdo antes de ser reaproveitado; o que não passa é refeito.
- **Tempo:** o estudo completo leva cerca de 5 h 30 min na máquina de referência (12 núcleos).
- **Saídas no notebook:** ao fim da execução completa, `climate.ipynb` recebe as saídas (tabelas, figuras e sínteses), e uma cópia local (`climate_executado.ipynb`, fora do repositório) serve à conferência.

## Aleatoriedade

- **Sementes:** a semente raiz é 42. Cada tarefa usa uma semente derivada da raiz e do nome da tarefa (SHA-256), igual em qualquer máquina.
- **PyTorch:** roda em modo determinístico estrito (`torch.use_deterministic_algorithms(True)`), na CPU.
- **Registro do ambiente:** o notebook registra o dispositivo e o número de threads do PyTorch, de BLAS/OpenMP e do joblib. Esses valores entram na assinatura da execução.
- **Limite:** sementes iguais não garantem números idênticos entre plataformas ou versões de bibliotecas. Na mesma máquina e com as mesmas versões, os números se repetem. Entre o Windows e o Linux, a rede neural diferiu em até 1e-5 no piloto, sem mudar nenhuma conclusão.

## Procedência

- **Dados:** cada arquivo baixado tem URL, data de acesso e SHA-256 em `dados/registro.json`. Downloads em datas ou sistemas diferentes podem ter bytes diferentes com os mesmos valores; por isso a assinatura da execução usa um SHA-256 dos valores lidos.
- **Resultados:** cada arquivo de `resultados/completo/` está no manifesto SHA-256 (`resultados/completo/registros/manifesto.json`), junto com a configuração, o ambiente e a numeração das tabelas e figuras.

## Conferência da release

Depois da execução completa:

```powershell
.\.venv\Scripts\python.exe conferir_publicacao.py
```

O script confere nove pontos e grava o relatório em `conferencia_publicacao_completo.md`:

1. o notebook rodou sem erro e em ordem;
2. o código do notebook executado é o mesmo do fonte e o da assinatura;
3. o manifesto SHA-256 confere com os arquivos;
4. o RPSS de cada modelo, recalculado das previsões gravadas, é igual ao da tabela da hipótese;
5. o veredito segue a regra declarada;
6. cada figura existe em PNG e PDF;
7. as saídas não contêm caminhos da máquina;
8. os cortes temporais: a escolha compartilhada da calibração termina antes da validação, a validação e o treino final terminam até dez/2010, e o teste de todos os alvos começa depois disso;
9. nenhum modelo com índice é idêntico ao seu controle sem índice (um modelo que não usa o índice não testa a hipótese).

## Citação e licença

Cite pelo `CITATION.cff`. O código está sob a licença MIT, e os resultados sob CC BY 4.0 (`LICENSE-RESULTADOS.md`).
