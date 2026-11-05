"""Full climate pipeline, end to end, in the repository folder:

 1. registers the 'climate' kernel for the .venv Python;
 2. pilot (quick code check, a few minutes);
 3. pilot check;
 4. full study (about 5 h 30 min); at the end, climate.ipynb stores the outputs;
 5. release check (9 checks, including the temporal cuts);
 6-10. article scripts, which only read the results: diagnostics, RPSS over climatology,
    numbers, figures and tables.

Stops at the first step with an error. While running, asks Windows not to sleep
(SetThreadExecutionState), without changing any permanent setting.

Usage: executar_tudo.bat (double click) or, in PowerShell, inside the folder:
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
    ('Registering the climate kernel', [PY, '-m', 'ipykernel', 'install', '--user', '--name', 'climate',
                                      '--display-name', 'Python (climate)']),
    ('Pilot (quick code check)', [PY, 'rodar_climate.py', '--modo', 'piloto']),
    ('Pilot check', [PY, 'conferir_publicacao.py', '--modo', 'piloto']),
    ('Full study (about 5 h 30 min)', [PY, 'rodar_climate.py']),
    ('Release check', [PY, 'conferir_publicacao.py']),
    ('Article: forecast diagnostics', [PY, 'artigo/diagnosticos_artigo.py']),
    ('Article: RPSS over climatology', [PY, 'artigo/rpss_climatologia.py']),
    ('Article: numbers in the text', [PY, 'artigo/numeros_artigo.py']),
    ('Article: figures', [PY, 'artigo/figuras_artigo.py']),
    ('Article: tables', [PY, 'artigo/tabelas_artigo.py']),
]


def main():
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # do not sleep
    log = PASTA / 'executar_tudo.log'
    for k, (nome, cmd) in enumerate(ETAPAS, 1):
        linha = f'[{datetime.now():%d/%m %H:%M}] [{k}/{len(ETAPAS)}] {nome}'
        print('\n' + linha, flush=True)
        with open(log, 'a', encoding='utf-8') as f:
            f.write(linha + '\n')
        r = subprocess.run(cmd, cwd=PASTA)
        if r.returncode != 0:
            msg = f'[{datetime.now():%d/%m %H:%M}] stopped with an error at step {k} (code {r.returncode})'
            print('\n' + msg, flush=True)
            with open(log, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
            return r.returncode
    fim = (f'[{datetime.now():%d/%m %H:%M}] all done; report: '
           'conferencia_publicacao_completo.md')
    print('\n' + fim, flush=True)
    with open(log, 'a', encoding='utf-8') as f:
        f.write(fim + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
