# Contribuindo com o Ordo Desktop

Obrigado pelo interesse! Toda ajuda conta: relatar um bug, sugerir uma ideia, melhorar a
documentação ou enviar código.

## Relatando bugs e sugerindo ideias

Abra uma [issue](https://github.com/luizsant/OrdoDesktop/issues/new/choose) usando um dos
modelos. Para bugs, informe a distro, a versão do GNOME (`gnome-shell --version`), se a sessão é
X11 ou Wayland (`echo $XDG_SESSION_TYPE`) e, se possível, a saída de rodar `ordo-desktop` pelo
terminal.

## Preparando o ambiente

O projeto é um único arquivo Python com GTK 3, sem dependências além do PyGObject:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
git clone https://github.com/<seu-usuario>/OrdoDesktop.git
cd OrdoDesktop
```

Se o Ordo instalado estiver aberto, feche-o antes (botão direito → **Sair**): as duas cópias
usam o mesmo identificador de aplicativo e só uma roda por vez.

```bash
python3 ordo_desktop.py
```

### Testando sem mexer na sua configuração

Use uma pasta de configuração separada. Copie o `user-dirs.dirs` junto, senão a Área de
Trabalho vira `~/Desktop`:

```bash
mkdir -p /tmp/ordo-teste && cp ~/.config/user-dirs.dirs /tmp/ordo-teste/
XDG_CONFIG_HOME=/tmp/ordo-teste python3 ordo_desktop.py
```

Para ver as janelas por cima de tudo (útil para capturas de tela), adicione `ORG_TEST_ABOVE=1`.

### Gerando o pacote .deb

```bash
./build-deb.sh 1.9.0
sudo apt install ./ordo-desktop_1.9.0_all.deb
```

## Enviando um pull request

1. Faça um fork e crie um branch a partir de `main` (`git checkout -b minha-melhoria`).
2. Mantenha o estilo do código: PEP 8, linhas de até 120 caracteres, comentários e textos da
   interface em português.
3. Confira que o arquivo compila: `python3 -m py_compile ordo_desktop.py`.
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
- **Leve e sem dependências pesadas**: um arquivo, GTK 3 e a biblioteca padrão do Python.
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
