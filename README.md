# Aprendizado de Máquina para Detecção de Ataques Mirai em Redes IoT 5G

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Este repositório contém o código-fonte, os scripts e os materiais de suporte para a dissertação de Mestrado intitulada **"Aprendizado de máquina para detecção de ataques Mirai em redes IoT 5G"**, desenvolvida no Programa de Pós-Graduação em Ciência da Computação da Universidade Federal de Juiz de Fora (UFJF).

## Visão Geral

O projeto implementa e valida um Sistema de Deteção de Intrusões (IDS) baseado em fluxos para redes IoT habilitadas por 5G, com foco na identificação de variantes do malware Mirai (GRE-IP, GRE-ETH e UDP Plain). A solução propõe uma arquitetura distribuída **Edge-Fog-Cloud**, inspirada na função NWDAF do 5G, onde a inferência com modelos de Machine Learning (Random Forest e LightGBM) é realizada em tempo real na camada Fog para garantir baixa latência.

A validação prática foi realizada em um testbed 5G funcional, utilizando **Open5GS** para o Core da rede e **UERANSIM** para a emulação do equipamento de utilizador (UE) e da estação rádio-base (gNB).

![Arquitetura do Projeto](figures/arquitetura_detalhada.pdf)


## Estrutura do Repositório

- **/data/**: Deve conter os datasets. Esta pasta é ignorada pelo `.gitignore`, mas a estrutura esperada é `raw/` para capturas `.pcap` e `processed/` para os `.csv` gerados.
- **/notebooks/**: Contém o Jupyter Notebook (`analise_e_treinamento.ipynb`) com todo o processo de análise de dados, treinamento e avaliação dos modelos.
- **/models/**: Contém os ficheiros `.pkl` dos modelos Random Forest e LightGBM já treinados. Ignorado pelo `.gitignore`.
- **/scripts/**: Scripts Python e Shell para as diferentes etapas do projeto.
  - `01_captura_trafego/`: Script para captura contínua de tráfego de rede.
  - `02_extracao_features/`: Scripts para converter PCAP em CSV e para enviar os dados para a API de análise.
  - `03_geracao_trafego/`: Scripts para simular o tráfego benigno e as três variantes de ataque Mirai.
- **/server_ids/**: Código-fonte do servidor de inferência (`app.py`) implementado com Flask.
- **/testbed_config/**: Ficheiros de configuração (`.yaml`) para o ambiente 5G (Open5GS e UERANSIM), essenciais para a reprodutibilidade.
- **/figures/**: Figuras e gráficos de alta qualidade utilizados na dissertação.
- `requirements.txt`: A lista de todas as dependências Python necessárias para executar o projeto.

## Como Reproduzir o Experimento

### Pré-requisitos

- Ambiente de virtualização (ex: VirtualBox) com 3 VMs configuradas.
- Python 3.8+ e `pip`.
- Git.
- Open5GS e UERANSIM instalados e configurados nas respetivas VMs.
- Conhecimento para configurar as interfaces de rede das VMs.

### Passos

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/](https://github.com/)[SEU-USUARIO]/dissertacao-ids-5g-mirai.git
    cd dissertacao-ids-5g-mirai
    ```

2.  **Instale as dependências Python:**
    É recomendado criar um ambiente virtual primeiro.
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # venv\Scripts\activate    # No Windows

    pip install -r requirements.txt
    ```

3.  **Configuração do Testbed 5G:**
    - Utilize os ficheiros de configuração em `/testbed_config/` para configurar o Open5GS (nas VMs do Core e UPF) e o UERANSIM (na VM do Cliente).

4.  **Treinamento dos Modelos (Opcional):**
    - Para treinar os modelos do zero, execute o Jupyter Notebook `notebooks/analise_e_treinamento.ipynb`. Os modelos já treinados estão disponíveis na pasta `/models/`.

5.  **Execução do Pipeline de Deteção:**
    a. Na **VM do Servidor IDS**, inicie a API de inferência:
       ```bash
       python server_ids/app.py
       ```
    b. Na **VM do Core 5G**, inicie a captura de tráfego na interface `ogstun`:
       ```bash
       sudo ./scripts/01_captura_trafego/detect_loop.sh
       ```
    c. Na **VM do Cliente**, execute um dos scripts de geração de tráfego para simular um ataque:
       ```bash
       sudo python scripts/03_geracao_trafego/attack_GRE_IP.py
       ```
    d. Após a captura, processe o ficheiro `.pcap` gerado para obter a classificação:
       ```bash
       python scripts/02_extracao_features/sniffer.py /caminho/para/o/pcap_capturado.pcap
       ```

## Resultados

Os resultados demonstraram que ambos os modelos, Random Forest e LightGBM, alcançaram altíssima eficácia na deteção dos ataques Mirai, com F1-Score superior a 97%. No entanto, o LightGBM provou ser significativamente mais eficiente, com uma latência de inferência média quase 8 vezes menor, tornando-o a escolha ideal para uma implementação em tempo real em ambientes com recursos limitados, como a camada de Fog.

Para uma análise detalhada, consulte a dissertação.

## Citação

Se este trabalho for útil para a sua pesquisa, por favor, cite-o da seguinte forma:

```
Barboza, M. V. Z. (2026). Aprendizado de máquina para detecção de ataques Mirai em redes IoT 5G. [Dissertação de Mestrado, Universidade Federal de Juiz de Fora].
```

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o ficheiro `LICENSE` para mais detalhes.
