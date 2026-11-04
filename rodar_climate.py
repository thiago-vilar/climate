r"""Executa o notebook climate nesta pasta e mostra no terminal, a cada 2 horas, a previsão de
término de cada seção (Aquisição, Seções 1 a 10 e Fechamento).

Uso (PowerShell, dentro da pasta do repositório, sem ativar o ambiente):
    .\.venv\Scripts\python.exe rodar_climate.py --modo piloto   # conferência rápida
    .\.venv\Scripts\python.exe rodar_climate.py                 # execução completa

O executor só roda com o Python de .venv desta pasta e com o kernel 'climate' registrado para
esse mesmo Python (ver README); se algum dos dois não conferir, para antes de começar.

Ao fim da execução completa, climate.ipynb recebe as saídas (é a cópia de climate_executado.ipynb),
para que o notebook principal mostre os resultados no próprio corpo.

A execução pode ser interrompida (Ctrl+C) e retomada com o mesmo comando: as unidades já gravadas
em resultados/<modo>/ que passam na conferência do conteúdo não são refeitas. Sementes fixas: a mesma pasta, o mesmo código e as mesmas
versões das bibliotecas dão os mesmos números. Os dados são baixados pelo próprio notebook das
fontes originais para dados/ desta pasta; nada é lido de outras pastas.
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
INTERVALO_VERIFICACAO = 30          # segundos entre leituras do relatório gravado pelo notebook
MARCA_2H = 'relatório a cada 2 h'   # motivo com que o notebook grava o relatório periódico
KERNEL = 'climate'                 # kernel registrado para o Python de .venv desta pasta


def agora():
    return datetime.now().strftime('%d/%m/%Y %H:%M')


def tabela_terminal(texto):
    """Converte o relatório em Markdown gravado pelo notebook em texto simples para o terminal."""
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
    """Interrompe se o executor não estiver no Python de .venv desta pasta ou se o kernel
    'climate' não apontar para esse mesmo Python."""
    venv = (PASTA / '.venv').resolve()
    if Path(sys.prefix).resolve() != venv:
        sys.exit(f'Use o Python do ambiente desta pasta:\n  .\\.venv\\Scripts\\python.exe '
                 f'rodar_climate.py\n(Python atual: {sys.executable})')
    try:
        from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel
        spec = KernelSpecManager().get_kernel_spec(KERNEL)
    except NoSuchKernel:
        sys.exit(f"Kernel '{KERNEL}' não registrado. Registre com:\n"
                 '  .\\.venv\\Scripts\\python.exe -m ipykernel install --user '
                 f'--name {KERNEL} --display-name "Python (climate)"')
    exe = Path(spec.argv[0])
    mesmo = os.path.normcase(os.path.abspath(exe)) == os.path.normcase(os.path.abspath(
        sys.executable))                    # sem seguir atalhos: o caminho do próprio ambiente
    if not exe.is_absolute() or not mesmo:
        sys.exit(f"O kernel '{KERNEL}' aponta para {spec.argv[0]}, e não para {sys.executable}. "
                 'Registre de novo com o comando do README.')
    print(f'  Python: {sys.executable}\n  Kernel: {KERNEL} -> {exe}', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--modo', choices=['completo', 'piloto'], default='completo')
    args = ap.parse_args()
    if not NOTEBOOK.exists():
        sys.exit('climate.ipynb não está nesta pasta.')
    conferir_ambiente()
    registros = PASTA / 'resultados' / args.modo / 'registros'
    atual = registros / 'relatorio_atual.md'
    log_nb = PASTA / f'nbconvert_{args.modo}.log'
    saida = 'climate_executado.ipynb' if args.modo == 'completo' else 'climate_piloto.ipynb'
    env = dict(os.environ, CLIMATE_MODO=args.modo, PYTHONIOENCODING='utf-8')
    cmd = [sys.executable, '-m', 'nbconvert', '--to', 'notebook', '--execute', NOTEBOOK.name,
           '--output', saida, '--ExecutePreprocessor.timeout=-1',
           f'--ExecutePreprocessor.kernel_name={KERNEL}']
    print(f'[{agora()}] Início · modo {args.modo} · pasta {PASTA}', flush=True)
    print(f'  Mensagens do Jupyter: {log_nb.name}. Relatório completo: '
          f'resultados/{args.modo}/registros/relatorio_parcial.md', flush=True)
    print('  A previsão de cada seção aparece aqui a cada 2 h (e uma primeira vez ao fim da '
          'Aquisição).', flush=True)
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
        print(f'\n[{agora()}] Interrompido. Rode o mesmo comando para retomar.', flush=True)
        proc.terminate()
        proc.wait()
        return
    if atual.exists():
        print('\n' + tabela_terminal(atual.read_text(encoding='utf-8')), flush=True)
    if proc.returncode == 0:
        if args.modo == 'completo':
            # o notebook principal passa a guardar no corpo as saídas da execução completa
            # (tabelas, figuras e sínteses); o código e o texto são os mesmos
            shutil.copyfile(PASTA / saida, NOTEBOOK)
        print(f'\n[{agora()}] Execução concluída: {saida} e resultados/{args.modo}/.'
              + (' climate.ipynb atualizado com as saídas.' if args.modo == 'completo' else ''),
              flush=True)
    else:
        print(f'\n[{agora()}] A execução parou com erro (código {proc.returncode}). Últimas linhas '
              f'de {log_nb.name}:', flush=True)
        linhas = log_nb.read_text(encoding='utf-8', errors='replace').splitlines()
        print('\n'.join(linhas[-25:]), flush=True)
        print('Corrija a causa e rode o mesmo comando para retomar.', flush=True)
    sys.exit(proc.returncode)


if __name__ == '__main__':
    main()
