"""Pipeline completo do climate, de ponta a ponta, na pasta do repositorio:

 1. registra o kernel 'climate' para o Python de .venv;
 2. piloto (conferencia rapida do codigo, poucos minutos);
 3. conferencia do piloto;
 4. estudo completo (cerca de 5 h 30 min); ao fim, climate.ipynb passa a guardar as saidas;
 5. conferencia da release (9 verificacoes, inclusive os cortes temporais);
 6-10. scripts do artigo, que so leem os resultados: diagnosticos, RPSS sobre a climatologia,
    numeros, figuras e tabelas.

Para na primeira etapa com erro. Enquanto roda, pede ao Windows para nao suspender
(SetThreadExecutionState), sem alterar nenhuma configuracao permanente.

Uso: executar_tudo.bat (duplo clique) ou, no PowerShell, dentro da pasta:
    .\\.venv\\Scripts\\python.exe executar_tudo.py
"""
import ctypes
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
PY = str(PASTA / '.venv' / 'Scripts' / 'python.exe')
ETAPAS = [
    ('Registrando o kernel climate', [PY, '-m', 'ipykernel', 'install', '--user', '--name', 'climate',
                                      '--display-name', 'Python (climate)']),
    ('Piloto (conferencia rapida do codigo)', [PY, 'rodar_climate.py', '--modo', 'piloto']),
    ('Conferencia do piloto', [PY, 'conferir_publicacao.py', '--modo', 'piloto']),
    ('Estudo completo (cerca de 5 h 30 min)', [PY, 'rodar_climate.py']),
    ('Conferencia da release', [PY, 'conferir_publicacao.py']),
    ('Artigo: diagnosticos das previsoes', [PY, 'artigo/diagnosticos_artigo.py']),
    ('Artigo: RPSS sobre a climatologia', [PY, 'artigo/rpss_climatologia.py']),
    ('Artigo: numeros do texto', [PY, 'artigo/numeros_artigo.py']),
    ('Artigo: figuras', [PY, 'artigo/figuras_artigo.py']),
    ('Artigo: tabelas', [PY, 'artigo/tabelas_artigo.py']),
]


def main():
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # nao suspender
    log = PASTA / 'executar_tudo.log'
    for k, (nome, cmd) in enumerate(ETAPAS, 1):
        linha = f'[{datetime.now():%d/%m %H:%M}] [{k}/{len(ETAPAS)}] {nome}'
        print('\n' + linha, flush=True)
        with open(log, 'a', encoding='utf-8') as f:
            f.write(linha + '\n')
        r = subprocess.run(cmd, cwd=PASTA)
        if r.returncode != 0:
            msg = f'[{datetime.now():%d/%m %H:%M}] parou com erro na etapa {k} (codigo {r.returncode})'
            print('\n' + msg, flush=True)
            with open(log, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
            return r.returncode
    fim = (f'[{datetime.now():%d/%m %H:%M}] tudo concluido; relatorio: '
           'conferencia_publicacao_completo.md')
    print('\n' + fim, flush=True)
    with open(log, 'a', encoding='utf-8') as f:
        f.write(fim + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
