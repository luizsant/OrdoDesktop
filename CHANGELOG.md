# Changelog

Todas as mudanças relevantes do Ordo Desktop. O formato segue o
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem o
[Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [2.1.0] - 2026-10-31

### Adicionado
- Menu **Gadgets** para ligar cada card. Novos cards:
  - **Agenda e prazos**: calendário com feriados (calculados sem internet), prazos em dias úteis pelo CPC
    (arts. 219, 220 e 224) com lista do que não foi contado, contagem regressiva, aviso diário dos que
    vencem hoje ou amanhã e lembretes com horário. Por padrão só os feriados nacionais; forenses, do Pará,
    de Belém e datas extras do tribunal são opcionais.
  - **Tarefas**, **Favoritos**, **Área de transferência** (só na memória), **Relógios mundiais**,
    **Conversor** (moedas e unidades), **Tocando agora** (MPRIS, Linux) e **Imagem do dia** (Bing,
    com opção de papel de parede e de restaurar o original).
- No card do relógio: velocidade da rede, bateria e temperatura da CPU.

### Alterado
- "Reorganizar" distribui os cards em colunas ao lado do relógio, sem tirar das caixas o espaço de
  uma coluna, e encolhe (com rolagem) os cards de leitura longa quando a coluna não cabe na tela.

## [2.0.2] - 2026-10-31

### Corrigido
- Windows: o Ordo sumia com "Mostrar área de trabalho" (botão do canto da barra de tarefas e Win+D).
  O Qt desfazia o vínculo das janelas com a área de trabalho logo depois de exibi-las; agora o Ordo
  refaz esse vínculo e fica visível por cima da área de trabalho, como parte dela.

## [2.0.1] - 2026-10-29

### Corrigido
- "Reorganizar" podia deixar caixas abaixo da tela. Agora usa todas as colunas que cabem, divide as
  caixas entre elas de forma equilibrada (na ordem) e, se faltar altura, diminui as mais altas e só
  em último caso recolhe as de baixo — tudo sempre visível, com 16 px entre as janelas.

### Adicionado
- Encaixe magnético: ao arrastar ou redimensionar, as bordas grudam nas das outras caixas, cards,
  notas e relógio (alinhadas ou lado a lado, sempre com o mesmo espaço) e nas margens da tela.

## [2.0.0] - 2026-10-29

### Adicionado
- **Versão para Windows 10 e 11**, com instalador `.exe` (sem administrador, em português, inglês
  ou espanhol). As caixas ficam no nível da área de trabalho: atrás dos programas e visíveis com
  "Mostrar área de trabalho". Lê também a Área de Trabalho pública e atalhos `.lnk`/`.url`, oculta
  os ícones do Explorer enquanto está aberto e inicia com o Windows.
- `ordo-desktop --quit` fecha a instância aberta com segurança (devolvendo os ícones nativos); o
  desinstalador e as atualizações usam esse comando.
- Erros inesperados vão para `ordo-error.log` na pasta de configuração, sem derrubar o app.

### Alterado
- Toda a interface foi refeita em Qt (PySide6), uma base única para Windows e Linux. O `.deb`
  passa a ser `amd64` e traz o próprio Qt; a configuração existente continua valendo.
- "Reorganizar" se adapta ao tamanho da tela: cards ao lado do relógio ou embaixo dele, e caixas
  que não cabem ficam recolhidas. Em telas muito pequenas, mercado e notícias começam desligados.

### Removido
- A versão em GTK (`ordo_desktop.py`).

## [1.12.0] - 2026-10-29

### Adicionado
- Interface em português, inglês e espanhol: caixas, menus, cards, clima, datas, números e
  mensagens. Segue o idioma do sistema ou o escolhido em Configurações → Idioma.
- Cards de mercado e notícias redimensionáveis pelo canto ◢, com rolagem e "Tamanho automático".
- Os cards de mercado e notícias acompanham o estilo escolhido para as caixas.

### Alterado
- "Reorganizar" também posiciona o relógio e os cards de mercado e notícias.

## [1.11.0] - 2026-10-29

### Adicionado
- Busca no card do relógio para achar itens nas caixas, ignorando maiúsculas e acentos. As caixas
  filtram enquanto você digita (as sem resultado ficam apagadas e o contador mostra "1/4"),
  Enter abre o primeiro resultado e Esc limpa.

## [1.10.1] - 2026-10-29

### Corrigido
- Menu dos cards de mercado e notícias ficava longo demais e escondia as opções de exibição.
  Agora tem "Ocultar este card" no topo, e país, fontes e configurações gerais em submenus.

## [1.10.0] - 2026-10-29

### Adicionado
- Card de mercado: índices, moedas, Bitcoin e ações com variação do dia e minigráfico, além de
  Selic, CDI e IPCA 12 meses do Banco Central. Lista de ativos editável.
- Card de notícias gerais por país (Brasil, Portugal, Estados Unidos, Reino Unido, Espanha,
  Argentina e Mundo), com manchetes de feeds RSS públicos de veículos reconhecidos e escolha das
  fontes de cada país. Notícias com mais de 3 dias e chamadas de vídeo são ignoradas.

## [1.9.0] - 2026-10-29

Primeira versão pública.

### Adicionado
- Caixas automáticas por categoria, atualizadas em tempo real, com arrastar, redimensionar,
  recolher e mover arquivos entre caixas.
- Quatro estilos de caixa: Padrão, Vidro claro, Contorno colorido e Preto compacto.
- Card de relógio com gadgets: clima (Open-Meteo), uso do sistema e atalhos rápidos.
- Timer de foco com notificação.
- Notas adesivas coloridas.
- Opção de ocultar os ícones nativos da área de trabalho (Zorin, DING do Ubuntu e Gtk4 DING),
  com restauração automática ao fechar, inclusive após travamento.
- Início automático com o sistema, ligado por padrão.
- Execução via XWayland em sessões Wayland (experimental).
- Pacote `.deb` gerado automaticamente a cada release.
