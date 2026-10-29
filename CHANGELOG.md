# Changelog

Todas as mudanças relevantes do Ordo Desktop. O formato segue o
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem o
[Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

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
