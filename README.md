# 🌌 Nexara (Antigravity Bot)

**Nexara** é uma Inteligência Digital Pessoal projetada para rodar localmente no seu PC, oferecendo automação, controle e companhia. Originalmente um bot de empregos, ela evoluiu para um assistente persistente e autônomo.

## ✨ Funcionalidades Principais

- **🧠 Assistente Sempre Online**: Roda em segundo plano e responde instantaneamente no Telegram (`/ping`, `/start`).
- **💬 Chatbot Persistente**: Converse com a Nexara a qualquer momento sem abrir janelas pesadas.
- **🖥️ Controle do PC**: Execute comandos, abra programas e tire screenshots remotamente (via comandos `/pc`).
- **🛡️ Modo Seguro**: Busca de vagas e automações de LinkedIn desativadas por padrão para foco total em assistência.
- **🚀 Inicialização Automática**: Se integra ao Windows Task Scheduler para iniciar junto com o sistema.

## 📁 Estrutura do Projeto

- `bot_manager.py`: Gerenciador de inicialização (Monitora e reinicia o bot se necessário).
- `run_telegram_bot.py`: Núcleo leve da Nexara (Chatbot Only).
- `src/main.py`: Núcleo completo (com navegador) - *Opcional*.
- `config/settings.yaml`: Central de controle e preferências.

## 🚀 Instalação e Uso

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure**:
   - Renomeie `.env.example` para `.env` e adicione seu Token do Telegram.
   - Ajuste o `config/settings.yaml` conforme necessário.

3. **Inicie a Nexara**:
   Para rodar e configurar a inicialização automática no Windows:
   ```powershell
   ./start_bot.ps1
   ```
   *Ela iniciará silenciosamente e enviará uma mensagem no Telegram quando estiver pronta.*

## 🛠️ Comandos do Telegram

- `/ping`: Verifica se a Nexara está ouvindo.
- `/pc <comando>`: Executa um comando no terminal do PC.
- `/look`: Pede para a Nexara "olhar" a tela (screenshot + análise).
- `/room <cena>`: Controla dispositivos inteligentes (se configurado).

---
*Evoluindo a cada dia.* 🌟
