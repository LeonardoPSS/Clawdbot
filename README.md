# 🤖 Antigravity Job Bot

O **Antigravity Job Bot** é um assistente autônomo e inteligente projetado para automatizar a busca e candidatura a vagas de emprego, imitando o comportamento humano para garantir segurança e eficiência.

## ✨ Funcionalidades

- **Configuração Flexível**: Defina cargos, localizações e palavras-chave obrigatórias/proibidas no `settings.yaml`.
- **Leitura de Currículo**: Extração automática de dados de arquivos PDF e DOCX (testado com sucesso).
- **Busca Inteligente**: Varredura no LinkedIn (Guest Mode) para encontrar vagas recentes sem necessidade de login imediato.
- **Comportamento Humano**: Delays aleatórios, simulação de rolagem (smooth scroll) e movimentos de mouse para evitar detecção.
- **Log e Controle**: Registro de todas as ações em um banco de dados CSV (`data/applied.csv`).
- **Dashboard**: Visualização rápida de estatísticas e status das candidaturas.

## 📁 Estrutura do Projeto

- `src/config.py`: Validação e carregamento das configurações (Pydantic).
- `src/resume_parser.py`: Leitura e extração de informações do currículo.
- `src/job_searcher.py`: Automação da busca de vagas (Playwright).
- `src/applicant.py`: Lógica de visita e "inscrição" nas vagas.
- `src/behavior.py`: Simulador de comportamento humano.
- `src/storage.py`: Persistência de dados das candidaturas.
- `src/main.py`: Orquestrador principal do bot.
- `dashboard.py`: Script para visualização do status do bot.

## 🚀 Como Usar

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure seu perfil**:
   Edite o arquivo `config/settings.yaml` com suas preferências de vaga.

3. **Adicione seu currículo**:
   Coloque seu currículo em PDF na pasta `assets` e aponte o caminho no `settings.yaml`.

4. **Execute o Bot**:
   ```bash
   python -m src.main
   ```

5. **Veja os resultados**:
   ```bash
   python dashboard.py
   ```

## 🛠️ Tecnologias
- **Python 3.10+**
- **Playwright** (Automação de Browser)
- **Pydantic** (Validação de Dados)
- **PyYAML** (Configuração)
- **PDFMiner / Python-Docx** (Processamento de documentos)
- **Pandas** (Análise de dados para Dashboard)

---
*Desenvolvido com ❤️ por Antigravity.*
