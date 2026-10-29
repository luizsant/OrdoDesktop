<p align="center">
  <img src="ordo-desktop.svg" width="96" alt="Logo do Ordo Desktop">
</p>

<h1 align="center">Ordo Desktop</h1>

<p align="center">
  Organizador de área de trabalho para Linux com GNOME: caixas automáticas por tipo de arquivo,
  relógio, clima, notas adesivas e atalhos rápidos.
</p>

<p align="center">
  <a href="https://github.com/luizsant/OrdoDesktop/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/luizsant/OrdoDesktop"></a>
  <a href="LICENSE.md"><img alt="Licença PolyForm Noncommercial" src="https://img.shields.io/badge/licen%C3%A7a-PolyForm%20Noncommercial-blue"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <b>Português</b>
</p>

![Ordo Desktop em uso](docs/screenshot.png)

Inspirado no "Desktop Organizer" do 360 Total Security e no Stardock Fences, o Ordo agrupa o que
está na sua Área de Trabalho em caixas por categoria e as mantém atualizadas em tempo real.
**Ele não move, renomeia nem apaga seus arquivos**: só organiza a visualização.

## Recursos

- **Caixas automáticas**: Aplicativos, Pastas, PDFs, Documentos, Planilhas, Apresentações,
  Imagens, Vídeos, Áudio, Compactados, Instaladores e Outros. Uma caixa só aparece quando tem itens.
- **Do seu jeito**: arraste as caixas pelo título, redimensione pelo canto ◢, recolha com clique
  duplo e arraste um arquivo para outra caixa (a escolha fica salva).
- **4 estilos de caixa**: Padrão, Vidro claro, Contorno colorido e Preto compacto.
- **Card de relógio** com data por extenso e, abaixo dele, os gadgets:
  - clima atual e previsão de 4 dias ([Open-Meteo](https://open-meteo.com), sem cadastro);
  - uso de CPU, memória e disco;
  - atalhos: reorganizar, captura de tela, calculadora, terminal, Downloads, lixeira,
    bloquear tela, não perturbe, timer de foco, recolher caixas, monitor e nova nota.
- **Card de mercado**: Ibovespa, S&P 500, Nasdaq, dólar, euro, Bitcoin e ações (Petrobras, Vale e
  Itaú por padrão — editável), com variação do dia e minigráfico, além de Selic, CDI e IPCA 12 meses
  do Banco Central.
- **Card de notícias**: manchetes gerais de veículos reconhecidos, por país — Brasil (Agência
  Brasil, G1, Folha, BBC News Brasil…), Portugal, Estados Unidos, Reino Unido, Espanha, Argentina e
  Mundo (BBC, DW, France 24, Al Jazeera…). Você escolhe o país e as fontes; clique na manchete para
  abrir no navegador.
- **Notas adesivas** coloridas, salvas automaticamente.
- **Sem ícone na bandeja**: tudo é configurado pelo botão direito sobre qualquer caixa,
  o relógio ou uma nota.
- Inicia com o sistema e oculta os ícones nativos da área de trabalho enquanto está aberto
  (eles voltam quando o Ordo fecha).

## Instalação

### Pacote .deb (Ubuntu, Zorin OS, Pop!_OS, Linux Mint com GNOME, Debian…)

Baixe o arquivo `.deb` mais recente em
[Releases](https://github.com/luizsant/OrdoDesktop/releases/latest) e instale:

```bash
sudo apt install ./ordo-desktop_*_all.deb
```

Depois abra **Ordo Desktop** pelo menu de aplicativos. Na primeira execução ele organiza as caixas
sozinho e passa a iniciar com o sistema.

### Direto do código-fonte

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
git clone https://github.com/luizsant/OrdoDesktop.git
cd OrdoDesktop
python3 ordo_desktop.py
```

### Desinstalar

Feche o Ordo (botão direito → **Sair**) e rode:

```bash
sudo apt remove ordo-desktop
```

Suas configurações ficam em `~/.config/ordo-desktop/`; apague essa pasta se quiser zerar tudo.

## Requisitos

- GNOME (testado no Zorin OS 18 / GNOME 46) em sessão **X11**.
  Em Wayland o Ordo roda via XWayland, ainda em caráter experimental.
- Python 3, PyGObject e GTK 3 (já vêm instalados na maioria das distros com GNOME).
- Opcionais: `xdotool` (botão Captura), `libnotify-bin` (aviso do timer de foco).

Ícones nativos compatíveis com a opção de ocultar: Zorin Desktop Icons, Desktop Icons NG (DING,
padrão do Ubuntu) e Gtk4 Desktop Icons NG.

## Uso rápido

| Ação | Como |
| --- | --- |
| Abrir as configurações | Botão direito no título ou área vazia de uma caixa, no relógio ou numa nota |
| Mover uma caixa ou o relógio | Arrastar pelo título (ou pelo card do relógio) |
| Redimensionar uma caixa | Arrastar o canto ◢ |
| Recolher/expandir uma caixa | Clique duplo no título |
| Trocar um arquivo de caixa | Arrastar para outra caixa, ou botão direito → Mover para a caixa |
| Escolher a cidade do clima | Botão direito no clima |
| Duração do timer de foco | Botão direito no botão Foco |
| Editar os ativos do mercado | Botão direito no card de mercado → Editar ativos |
| Escolher país e fontes das notícias | Botão direito no card de notícias → País e lista de fontes |
| Ocultar o card de mercado ou de notícias | Botão direito no card → Ocultar este card |
| Mostrar de novo | Botão direito em qualquer caixa → Mostrar mercado financeiro / Mostrar notícias |

## Fontes de dados

Todas públicas, gratuitas e sem cadastro nem chave de API:

| Dado | Fonte |
| --- | --- |
| Clima | [Open-Meteo](https://open-meteo.com) |
| Índices, ações e moedas | Endpoint público de gráficos do Yahoo Finance (não oficial, pode ter atraso de até 15 min) |
| Cripto em reais | [AwesomeAPI](https://docs.awesomeapi.com.br) |
| Selic, CDI, IPCA | [API SGS do Banco Central](https://dadosabertos.bcb.gov.br) (oficial) |
| Notícias | Feeds RSS públicos de cada veículo; o Ordo mostra só a manchete e o link para a matéria original |

Os dados de mercado são apenas informativos e não constituem recomendação de investimento.

## Contribuindo

Contribuições são muito bem-vindas: correções, novas categorias, gadgets, estilos, traduções
e suporte a outras distros. Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para preparar o ambiente,
testar e abrir um pull request.

## Licença

[PolyForm Noncommercial 1.0.0](LICENSE.md) © 2026 Luiz Santiago.

Em resumo: você pode usar, copiar, estudar, modificar e redistribuir o Ordo de graça, para fins
**não comerciais**. **Não é permitido vender** o Ordo nem usá-lo, ou versões modificadas, com
fins comerciais. Ao redistribuir, mantenha o arquivo `LICENSE.md` com o aviso de copyright.
Este resumo não substitui o texto da licença.

