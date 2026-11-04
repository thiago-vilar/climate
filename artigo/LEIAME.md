# Artigo: scripts e produtos

Esta pasta liga o manuscrito à execução do notebook. Os scripts só **leem**
`resultados/<modo>/`: não reajustam modelos, não refazem testes e não alteram o notebook nem os
resultados, que têm manifesto SHA-256 próprio. As tabelas são lidas pelo nome
(`T*_hipotese_tres_metodos.csv`), e não pelo número.

## Como gerar

O `executar_tudo.py` (ou `executar_tudo.bat`) roda os cinco scripts no fim do pipeline. Para
rodá-los à parte, na pasta do repositório:

```powershell
.\.venv\Scripts\python.exe artigo\diagnosticos_artigo.py
.\.venv\Scripts\python.exe artigo\rpss_climatologia.py
.\.venv\Scripts\python.exe artigo\numeros_artigo.py
.\.venv\Scripts\python.exe artigo\figuras_artigo.py
.\.venv\Scripts\python.exe artigo\tabelas_artigo.py
```

Saídas em `artigo/saidas/completo/`:

| arquivo | conteúdo |
|---|---|
| `diagnosticos_previsoes.csv` | RPSS sobre a climatologia N do modelo e do controle; desvio-padrão das probabilidades de Q1 e Q5 no teste; confere o RPSS sobre o controle com a tabela da hipótese |
| `rpss_climatologia.csv` | RPSS de cada modelo e do seu controle sobre a climatologia padrão N, com IC95 (2 000 reamostragens de blocos circulares de 3 anos), e RPSS sobre o controle; referência comum aos três modelos, usada no texto, no resumo gráfico e na Tabela S8 |
| `numeros.json` | todos os números citados no texto, extraídos das tabelas finais |
| `figuras/fig1…fig6`, `resumo_grafico` | figuras do texto principal em PNG (300 dpi) e PDF, com os dados de cada painel em `*_dados.csv` |
| `tab2.json`, `supl.json` | Tabela 2 do texto e Tabelas S1 a S7 do material suplementar (a Tabela S8 vem de `rpss_climatologia.csv`), com as células já formatadas |

## Figuras do texto

| figura | arquivo | conteúdo |
|---|---|---|
| 1 | `fig1_alvos_ciclo` | mapa dos alvos (a) e chuva média mensal de 1981–2010 em cada alvo (b–d), com os meses na ordem do ano hidrológico, a estação chuvosa na cor do alvo e a linha da chuva média mensal do ano |
| 2 | `fig2_perfis_defasagem` | correlação entre cada índice e a posição `u` da chuva em função da defasagem, por alvo e caso |
| 3 | `fig3_mapas_chuvosa` | correlação por pixel na estação chuvosa; é a figura F09 do notebook, copiada sem alteração |
| 4 | `fig4_predominio_defasagem` | índice predominante em cada pixel, com a intensidade dada por \|r\| (a–c), e a defasagem desse índice (d–f); feita a partir do F13 do notebook, com a escala de \|r\| pela mesma regra de cor (intensidade \|r\|/0,5, entre 0,15 e 1). `numeros_artigo.py` grava a área, o \|r\| médio, a defasagem mais frequente e a fração com o sinal esperado de cada índice predominante (tabela `indice_predominante`) |
| 5 | `fig5_habilidade_regional` | RPSS de cada modelo sobre o mesmo modelo sem o índice, com IC95, nas 27 combinações |
| 6 | `fig6_regularizacao_detectabilidade` | calibração, ensaio sintético e variação das probabilidades emitidas |

## Procedimentos e limites que os números pressupõem

- **Cortes temporais.** Cada papel (referência, treino e validação da calibração, teste) é uma janela civil comum aos três alvos, e só entram anos hidrológicos com os 12 meses dentro dela. O notebook para se a escolha compartilhada da calibração usar algum mês posterior ao início do teste de qualquer alvo, e a conferência de publicação verifica os cortes.
- **Grade da Random Forest.** Folha mínima de 30, 20, 10 e 5 % dos meses de treino. A folha de 50 % não entra: com profundidade 1, só permite o corte exatamente na mediana dos meses sorteados, e muitas árvores ficariam sem divisão. O notebook para se algum modelo com índice sair idêntico ao seu controle (item 9 da conferência).
- **Correlação.** Pearson entre o índice bruto e a posição `u` da chuva; o r² refere-se a `u`. A coluna "r sem tendência" é descritiva.
- **Valor q.** O passo de 4 meses dá 130 deslocamentos e p ≥ 1/131. Com Benjamini e Hochberg sobre 27 combinações, um q < 0,05 exige pelo menos cinco combinações do mesmo método com valor-p no piso. Os valores q são mostrados com 3 casas.
- **Tendência comum.** Pela hipótese nula declarada, a tendência conta como informação do índice. As rejeições com índices substitutos que só têm a tendência medem a sensibilidade do teste a ela, e não erro tipo I. Rótulos: "acima de 5 %", "compatível com 5 %", "abaixo de 5 %".
- **Ensaio sintético.** Repete a defasagem, a grade e a regra de um erro-padrão, mantém a forma de entrada dos dados reais, usa uma realização do ruído e não repete o teste de hipótese; não estima poder.
- **Intervalos de confiança.** Condicionais às previsões (configuração, L* e treino fixos), marginais e não simultâneos.
- **Mapas.** RPSS por pixel em escala contínua divergente centrada em zero. Os pixels suspeitos de quebra no CHIRPS ficam nas análises e não são marcados; a lista está em `resultados/<modo>/registros/pixels_suspeitos.csv`.
- **Exposição ao teste.** O período de teste foi examinado durante o desenvolvimento do estudo. As escolhas de configuração foram fixadas com 1981–2010, mas a avaliação não é um teste inteiramente não visto.
