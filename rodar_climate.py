r"""Runs the climate notebook in this folder and shows in the terminal, every 2 hours, the expected
completion time of each section (Acquisition, Sections 1 to 10 and Closing).

Usage (PowerShell, inside the repository folder, without activating the environment):
    .\.venv\Scripts\python.exe rodar_climate.py --modo piloto   # quick check
    .\.venv\Scripts\python.exe rodar_climate.py                 # full run

The runner only runs with the .venv Python of this folder and with the 'climate' kernel registered
for that same Python (see README); if either does not match, it stops before starting.

At the end of the full run, climate.ipynb receives the outputs (it is the copy of climate_executado.ipynb),
so that the main notebook shows the results in its own body.

The run can be interrupted (Ctrl+C) and resumed with the same command: units already stored
in resultados/<modo>/ that pass the content check are not redone. Fixed seeds: the same folder, the same code and the same
library versions give the same numbers. The data are downloaded by the notebook itself from the
original sources into dados/ in this folder; nothing is read from other folders.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
NOTEBOOK = PASTA / 'climate.ipynb'
INTERVALO_VERIFICACAO = 30          # seconds between reads of the report written by the notebook
MARCA_2H = 'relatório a cada 2 h'   # reason with which the notebook writes the periodic report
KERNEL = 'climate'                 # kernel registered for the .venv Python of this folder


def agora():
    return datetime.now().strftime('%d/%m/%Y %H:%M')


def tabela_terminal(texto):
    """Converts the Markdown report written by the notebook into plain text for the terminal."""
    linhas = []
    for linha in texto.splitlines():
        if linha.startswith('|---'):
            continue
        if linha.startswith('|'):
            celulas = [c.strip() for c in linha.strip('|').split('|')]
            linhas.append(f'  {celulas[0]:<11} {celulas[1]:<12} {celulas[2]:>14}  '
                          f'{celulas[3]:>10}  {celulas[4]:>22}  {celulas[5]:>11}')
        elif linha.startswith('### '):
            linhas.append(linha[4:])
        elif linha.strip():
            linhas.append(linha.replace('`', ''))
    return '\n'.join(linhas)


def conferir_ambiente():
    """Stops if the runner is not on the .venv Python of this folder or if the 'climate'
    kernel does not point to that same Python."""
    venv = (PASTA / '.venv').resolve()
    if Path(sys.prefix).resolve() != venv:
        sys.exit(f'Use the Python of this folder\'s environment:\n  .\\.venv\\Scripts\\python.exe '
                 f'rodar_climate.py\n(current Python: {sys.executable})')
    try:
        from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel
        spec = KernelSpecManager().get_kernel_spec(KERNEL)
    except NoSuchKernel:
        sys.exit(f"Kernel '{KERNEL}' not registered. Register it with:\n"
                 '  .\\.venv\\Scripts\\python.exe -m ipykernel install --user '
                 f'--name {KERNEL} --display-name "Python (climate)"')
    exe = Path(spec.argv[0])
    mesmo = os.path.normcase(os.path.abspath(exe)) == os.path.normcase(os.path.abspath(
        sys.executable))                    # without following links: the environment's own path
    if not exe.is_absolute() or not mesmo:
        sys.exit(f"The kernel '{KERNEL}' points to {spec.argv[0]}, not to {sys.executable}. "
                 'Register it again with the command in the README.')
    print(f'  Python: {sys.executable}\n  Kernel: {KERNEL} -> {exe}', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--modo', choices=['completo', 'piloto'], default='completo')
    args = ap.parse_args()
    if not NOTEBOOK.exists():
        sys.exit('climate.ipynb is not in this folder.')
    conferir_ambiente()
    registros = PASTA / 'resultados' / args.modo / 'registros'
    atual = registros / 'relatorio_atual.md'
    log_nb = PASTA / f'nbconvert_{args.modo}.log'
    saida = 'climate_executado.ipynb' if args.modo == 'completo' else 'climate_piloto.ipynb'
    env = dict(os.environ, CLIMATE_MODO=args.modo, PYTHONIOENCODING='utf-8')
    cmd = [sys.executable, '-m', 'nbconvert', '--to', 'notebook', '--execute', NOTEBOOK.name,
           '--output', saida, '--ExecutePreprocessor.timeout=-1',
           f'--ExecutePreprocessor.kernel_name={KERNEL}']
    print(f'[{agora()}] Start · mode {args.modo} · folder {PASTA}', flush=True)
    print(f'  Jupyter messages: {log_nb.name}. Full report: '
          f'resultados/{args.modo}/registros/relatorio_parcial.md', flush=True)
    print('  The forecast for each section appears here every 2 h (and a first time at the end of the '
          'Acquisition).', flush=True)
    with open(log_nb, 'a', encoding='utf-8') as f:
        proc = subprocess.Popen(cmd, cwd=PASTA, env=env, stdout=f, stderr=subprocess.STDOUT)
    ultimo, primeiro = None, True
    try:
        while proc.poll() is None:
            time.sleep(INTERVALO_VERIFICACAO)
            if not atual.exists():
                continue
            texto = atual.read_text(encoding='utf-8')
            if texto == ultimo:
                continue
            if MARCA_2H in texto or primeiro:
                print('\n' + tabela_terminal(texto), flush=True)
                primeiro = False
            ultimo = texto
    except KeyboardInterrupt:
        print(f'\n[{agora()}] Interrupted. Run the same command to resume.', flush=True)
        proc.terminate()
        proc.wait()
        return
    if atual.exists():
        print('\n' + tabela_terminal(atual.read_text(encoding='utf-8')), flush=True)
    if proc.returncode == 0:
        if args.modo == 'completo':
            # the main notebook stores in its body the outputs of the full run
            # (tables, figures and summaries); the code and the text are the same
            shutil.copyfile(PASTA / saida, NOTEBOOK)
        print(f'\n[{agora()}] Run finished: {saida} and resultados/{args.modo}/.'
              + (' climate.ipynb updated with the outputs.' if args.modo == 'completo' else ''),
              flush=True)
    else:
        print(f'\n[{agora()}] The run stopped with an error (code {proc.returncode}). Last lines '
              f'of {log_nb.name}:', flush=True)
        linhas = log_nb.read_text(encoding='utf-8', errors='replace').splitlines()
        print('\n'.join(linhas[-25:]), flush=True)
        print('Fix the cause and run the same command to resume.', flush=True)
    sys.exit(proc.returncode)


if __name__ == '__main__':
    main()
