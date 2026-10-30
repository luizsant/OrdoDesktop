# Contribuindo com o Ordo Desktop

Obrigado pelo interesse! Toda ajuda conta: relatar um bug, sugerir uma ideia, melhorar a
documentação ou enviar código.

## Relatando bugs e sugerindo ideias

Abra uma [issue](https://github.com/luizsant/OrdoDesktop/issues/new/choose) usando um dos
modelos. Para bugs, informe a distro, a versão do GNOME (`gnome-shell --version`), se a sessão é
X11 ou Wayland (`echo $XDG_SESSION_TYPE`) e, se possível, a saída de rodar `ordo-desktop` pelo
terminal.

## Preparando o ambiente

O Ordo é Python com Qt (PySide6) e roda igual no Windows e no Linux:

```bash
git clone https://github.com/<seu-usuario>/OrdoDesktop.git
cd OrdoDesktop
python3 -m venv .venv
.venv/bin/pip install PySide6        # no Windows: .venv\Scripts\pip install PySide6
.venv/bin/python -m ordo
```

Se o Ordo instalado estiver aberto, feche-o antes (botão direito → **Sair**): só uma cópia roda
por vez em cada usuário.

### Onde fica cada coisa

| Arquivo | O que faz |
| --- | --- |
| `ordo/app.py` | Aplicativo, caixas, menu geral, Reorganizar |
| `ordo/clock.py` | Card do relógio: busca, clima, sistema, atalhos, timer |
| `ordo/cards.py` | Cards de mercado e notícias |
| `ordo/notes.py` | Notas adesivas |
| `ordo/widgets.py` | Base das janelas de fundo de tela, alça de redimensionar, tarefas em segundo plano |
| `ordo/system.py` | Tudo que muda entre Windows e Linux (pastas, abrir arquivos, ícones nativos, atalhos) |
| `ordo/data.py` | Clima, cotações, indicadores e notícias (só biblioteca padrão) |
| `ordo/catalog.py`, `ordo/i18n.py` | Categorias, estilos e as traduções (português, inglês, espanhol) |

Texto novo na interface: escreva em português dentro de `_("…")` e acrescente a tradução em
`TR["en"]` e `TR["es"]` no `ordo/i18n.py`.

### Testando sem mexer na sua configuração

No Linux, use uma pasta de configuração separada (copie o `user-dirs.dirs` junto, senão a Área de
Trabalho vira `~/Desktop`) e desligue a opção de ocultar ícones nativos:

```bash
mkdir -p /tmp/ordo-teste/ordo-desktop && cp ~/.config/user-dirs.dirs /tmp/ordo-teste/
echo '{"hide_native": false, "autostart": false}' > /tmp/ordo-teste/ordo-desktop/config.json
XDG_CONFIG_HOME=/tmp/ordo-teste .venv/bin/python -m ordo
```

`ORDO_TEST_ABOVE=1` deixa as janelas por cima de tudo (útil para capturas de tela).
`ORDO_SELFTEST="captura.png;10"` abre, fotografa a tela depois de 10 s, grava um diagnóstico em
`captura.json` e fecha — é o que o CI usa.

### Gerando os pacotes

- **Linux (.deb):** `./build-deb.sh 2.0.0` → `ordo-desktop_2.0.0_amd64.deb` (baixa o PySide6 e
  leva dentro do pacote).
- **Windows (.exe):** no Windows, com Python 3.12, `pip install PySide6-Essentials pyinstaller pillow`
  e o [Inno Setup 6](https://jrsoftware.org/isinfo.php); depois
  `powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1 -Version 2.0.0`.

O GitHub Actions faz os dois a cada envio: o workflow **Verificação** instala o `.deb` e abre o Ordo
numa tela virtual, e o workflow **Windows** instala o `.exe` numa máquina Windows, fotografa a tela
e desinstala (as capturas ficam nos artefatos da execução).

## Enviando um pull request

1. Faça um fork e crie um branch a partir de `main` (`git checkout -b minha-melhoria`).
2. Mantenha o estilo do código: PEP 8, linhas de até 120 caracteres, comentários e textos da
   interface em português.
3. Confira que o código passa na análise: `python3 -m pyflakes ordo packaging`.
4. Teste a mudança rodando o app e descreva no PR o que mudou e como você testou. Para mudanças
   visuais, inclua uma captura de tela (sem arquivos pessoais aparecendo).
5. Se a mudança for perceptível para quem usa, adicione uma linha em `CHANGELOG.md`, na seção
   **Não lançado**.

## Licença das contribuições

O Ordo usa a licença [PolyForm Noncommercial 1.0.0](LICENSE.md). Ao enviar um pull request, você
concorda que a sua contribuição seja distribuída sob essa mesma licença e que o mantenedor
possa continuar a licenciar o projeto, incluindo a sua contribuição, nesses termos.

## Princípios do projeto

- **Nunca mexer nos arquivos do usuário sem ação explícita**: o Ordo só organiza a visualização.
  Excluir vai sempre para a lixeira.
- **Sempre devolver o desktop como estava**: se o Ordo ocultar algo (como os ícones nativos),
  precisa restaurar ao fechar, inclusive após travar.
- **Leve e sem dependências pesadas**: Qt (PySide6) e a biblioteca padrão do Python.
- **Configuração pelo próprio desktop**: sem ícone na bandeja, tudo pelo botão direito.

## Publicando uma versão (mantenedores)

Atualize o `CHANGELOG.md`, crie a tag e envie:

```bash
git tag v1.9.0
git push origin v1.9.0
```

O GitHub Actions gera o `.deb` e cria a Release com ele anexado.

## Código de conduta

Seja gentil e respeitoso. Críticas são sobre o código, nunca sobre as pessoas.
