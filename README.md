# Sistema de Irrigação Inteligente - FarmTech Solutions
## Projeto Acadêmico Completo - Fases 3 e 4

**Autor:** FarmTech Solutions  
**Data:** Junho 2025  
**Versão:** 4.0 Completa

---

## 📋 Índice

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Fase 3 - Entrega 1: Sistema ESP32](#fase-3---entrega-1-sistema-esp32)
3. [Fase 3 - Entrega 2: Sistema de Coleta de Dados](#fase-3---entrega-2-sistema-de-coleta-de-dados)
4. [Fase 4: Integração ESP32 + Oracle Database](#fase-4-integração-esp32--oracle-database)
5. [Instalação e Configuração](#instalação-e-configuração)
6. [Como Executar](#como-executar)
7. [Demonstração em Vídeo](#demonstração-em-vídeo)
8. [Tecnologias Utilizadas](#tecnologias-utilizadas)

---

# 🎯 Visão Geral do Projeto

Este projeto implementa um **Sistema de Irrigação Inteligente** completo que evoluiu através de múltiplas fases acadêmicas, integrando hardware simulado, software de gestão e banco de dados Oracle. O sistema utiliza sensores para monitorar as condições do solo e controlar automaticamente uma bomba de irrigação.

## Evolução do Projeto

- **Fase 3 - Entrega 1:** Sistema de sensores e controle com ESP32
- **Fase 3 - Entrega 2:** Sistema de armazenamento de dados em banco Oracle
- **Fase 4:** Integração completa ESP32 + Oracle com preservação da estrutura existente

---

# 🔧 Fase 3 - Entrega 1: Sistema ESP32

## Descrição do Sistema

O sistema foi implementado utilizando ESP32 e simulado na plataforma Wokwi. É responsável pela leitura dos sensores e controle do relé da bomba de irrigação através de uma lógica inteligente.

## Descrição do Circuito

O circuito foi construído na plataforma Wokwi utilizando os seguintes componentes:

- **ESP32**: Microcontrolador principal
- **Botão 1**: Simula o sensor de Fósforo (P)
- **Botão 2**: Simula o sensor de Potássio (K)
- **LDR (Light Dependent Resistor)**: Simula o sensor de pH
- **DHT22**: Simula o sensor de umidade do solo
- **Relé**: Controla a bomba de irrigação
- **LED embutido**: Indica visualmente o status da bomba

### Imagem do Circuito

![Circuito Wokwi](Circuito-img.png)

## Lógica de Controle

O sistema implementa a seguinte lógica para controle da bomba de irrigação:

1. **Monitoramento contínuo**: Os sensores são lidos a cada 2 segundos.
2. **Controle baseado em umidade**: 
   - Se a umidade estiver abaixo de 30%, a bomba é ativada.
   - Se a umidade estiver acima de 70%, a bomba é desativada.
3. **Condições adicionais**:
   - Se o pH estiver fora da faixa ideal (muito ácido ou muito alcalino), a irrigação é evitada.
   - Se não houver nutrientes (fósforo e potássio) detectados, a irrigação é priorizada para melhorar a absorção de nutrientes que serão adicionados posteriormente.

## Funcionamento do Código

O código em C/C++ está estruturado da seguinte forma:

1. **Inicialização**: Configura os pinos, inicia a comunicação serial e o sensor DHT22.
2. **Loop principal**: Executa leituras periódicas dos sensores e toma decisões de controle.
3. **Funções específicas**:
   - `lerSensores()`: Realiza a leitura de todos os sensores.
   - `analisarDadosEControlarBomba()`: Implementa a lógica de controle da bomba.
   - `exibirDados()`: Formata e exibe os dados no monitor serial para posterior armazenamento.

Os dados são enviados pelo monitor serial em formato CSV para facilitar a importação para o banco de dados:
```
timestamp,fosforo,potassio,ph,umidade,bomba_status
```

---

# 🗃️ Fase 3 - Entrega 2: Sistema de Coleta de Dados

## Descrição do Sistema

Este sistema implementa a coleta de dados de sensores agrícolas que simula o armazenamento e manipulação de informações sobre culturas, sensores, medições, sugestões e aplicações em um banco de dados Oracle.

## Modelo Relacional

O sistema é baseado no seguinte modelo relacional:

![Modelo Relacional](Modelo_Relacional.png)

O modelo consiste em cinco tabelas principais:

1. **T_CULTURAS**: Armazena informações sobre as culturas agrícolas.
2. **T_SENSORES**: Registra os sensores instalados e suas características.
3. **T_MEDICOES**: Contém as medições realizadas pelos sensores.
4. **T_SUGESTOES**: Armazena sugestões baseadas nas medições.
5. **T_APLICACOES**: Registra as aplicações realizadas com base nas sugestões.

## Relação com o MER da Fase 2

O banco de dados implementado segue fielmente o Modelo Entidade-Relacionamento (MER) desenvolvido na Fase 2 do projeto. As principais correspondências são:

### Entidades e Tabelas

Cada entidade do MER foi mapeada para uma tabela correspondente no banco de dados:

- A entidade **Cultura** é representada pela tabela `T_CULTURAS`
- A entidade **Sensor** é representada pela tabela `T_SENSORES`
- A entidade **Medição** é representada pela tabela `T_MEDICOES`
- A entidade **Sugestão** é representada pela tabela `T_SUGESTOES`
- A entidade **Aplicação** é representada pela tabela `T_APLICACOES`

### Relacionamentos

Os relacionamentos do MER foram implementados através de chaves estrangeiras:

- Um sensor pertence a uma cultura: `T_SENSORES.cod_cultura` referencia `T_CULTURAS.cod_cultura`
- Uma medição é realizada por um sensor: `T_MEDICOES.cod_sensor` referencia `T_SENSORES.cod_sensor`
- Uma sugestão é baseada em uma medição: `T_SUGESTOES.cod_medicao` e `T_SUGESTOES.cod_sensor` referenciam `T_MEDICOES.cod_medicao` e `T_MEDICOES.cod_sensor`
- Uma aplicação é baseada em uma sugestão: `T_APLICACOES.cod_sugestao`, `T_APLICACOES.cod_medicao` e `T_APLICACOES.cod_sensor` referenciam `T_SUGESTOES.cod_sugestao`, `T_SUGESTOES.cod_medicao` e `T_SUGESTOES.cod_sensor`
- Uma aplicação é realizada em uma cultura: `T_APLICACOES.cod_cultura` referencia `T_CULTURAS.cod_cultura`

## Arquivos CSV de Exemplo

Os arquivos CSV contêm dados de exemplo para cada tabela do modelo relacional:

### t_culturas.csv
Contém informações sobre diferentes culturas agrícolas, como soja, milho e café, incluindo tamanho e data prevista de colheita.

### t_sensores.csv
Contém dados de sensores instalados, incluindo tipo (umidade, pH, temperatura), fabricante, modelo e localização.

### t_medicoes.csv
Registra medições realizadas pelos sensores, com data/hora, valor e unidade de medida.

### t_sugestoes.csv
Contém sugestões baseadas nas medições, como irrigação ou aplicação de fertilizantes.

### t_aplicacoes.csv
Registra aplicações realizadas com base nas sugestões, incluindo produto utilizado, quantidade e responsável.

## Operações CRUD Implementadas

O sistema implementa operações CRUD (Create, Read, Update, Delete) para todas as tabelas do modelo relacional:

### Create (Criar)
Métodos para inserir novos registros em cada tabela:
- `create_cultura()`: Insere uma nova cultura
- `create_sensor()`: Insere um novo sensor
- `create_medicao()`: Insere uma nova medição
- `create_sugestao()`: Insere uma nova sugestão
- `create_aplicacao()`: Insere uma nova aplicação

### Read (Ler)
Métodos para recuperar dados das tabelas:
- `read_cultura()`: Recupera dados de culturas
- `read_sensor()`: Recupera dados de sensores
- `read_medicao()`: Recupera dados de medições
- `read_sugestao()`: Recupera dados de sugestões
- `read_aplicacao()`: Recupera dados de aplicações

### Update (Atualizar)
Métodos para atualizar registros existentes:
- `update_cultura()`: Atualiza dados de uma cultura
- `update_sensor()`: Atualiza dados de um sensor
- `update_medicao()`: Atualiza dados de uma medição
- `update_sugestao()`: Atualiza dados de uma sugestão
- `update_aplicacao()`: Atualiza dados de uma aplicação

### Delete (Excluir)
Métodos para remover registros:
- `delete_cultura()`: Remove uma cultura
- `delete_sensor()`: Remove um sensor
- `delete_medicao()`: Remove uma medição
- `delete_sugestao()`: Remove uma sugestão
- `delete_aplicacao()`: Remove uma aplicação

Todas as operações CRUD implementam verificações de integridade referencial para garantir a consistência dos dados.

## Consultas Analíticas

Além das operações CRUD básicas, o sistema implementa consultas analíticas para obter insights dos dados:

- `get_medicoes_by_cultura()`: Recupera medições associadas a uma cultura específica
- `get_aplicacoes_by_cultura()`: Recupera aplicações associadas a uma cultura específica
- `get_sugestoes_by_sensor()`: Recupera sugestões associadas a um sensor específico

## Justificativa da Estrutura de Dados

Para este projeto, optamos por uma estrutura de dados relacional implementada em Oracle, que oferece um equilíbrio ideal entre robustez, desempenho e fidelidade ao modelo entidade-relacionamento (MER) original. A escolha do Oracle como sistema de gerenciamento de banco de dados se justifica pelos seguintes fatores:

1. **Robustez**: O Oracle é um SGBD de nível empresarial, capaz de lidar com grandes volumes de dados e operações complexas.
2. **Confiabilidade**: Oferece recursos avançados de recuperação e alta disponibilidade, essenciais para dados críticos agrícolas.
3. **Segurança**: Fornece mecanismos robustos de controle de acesso e proteção de dados.
4. **Suporte completo a linguagem Transact-Oracle**: Permite implementar todas as operações CRUD e consultas complexas necessárias.
5. **Integridade referencial**: Suporta chaves estrangeiras e restrições de integridade, essenciais para manter a consistência do modelo relacional.
6. **Funções avançadas de data/hora**: Oferece funções como TO_DATE e TO_TIMESTAMP que facilitam o trabalho com dados temporais, importantes para registros de medições e aplicações.

---

# 🚀 Fase 4: Integração ESP32 + Oracle Database

## Visão Geral da Fase 4

A Fase 4 representa a **continuação e integração** das fases anteriores, implementando um sistema completo que conecta o hardware simulado (ESP32) com o sistema de gestão de dados (Oracle Database), preservando toda a estrutura desenvolvida na Fase 3.

## Arquitetura Integrada

```
┌─────────────────┐    CSV    ┌─────────────────┐    Oracle    ┌─────────────────┐
│   ESP32 + Wokwi │  ──────►  │  Sistema Python │  ──────►  │  Oracle Database│
│                 │           │                 │           │   (Fase 3)      │
│ • Sensores      │           │ • CRUD          │           │ • T_CULTURAS    │
│ • Lógica        │           │ • Importação    │           │ • T_SENSORES    │
│ • Dados CSV     │           │ • Estatísticas  │           │ • T_MEDICOES    │
└─────────────────┘           └─────────────────┘           └─────────────────┘
```

## Objetivos Alcançados

✅ **Continuidade perfeita** da Fase 3  
✅ **Sistema ESP32 funcional** no Wokwi  
✅ **Operações CRUD completas** no Oracle  
✅ **Integração de dados** entre hardware e software  
✅ **Preservação da estrutura** do banco existente  
✅ **Interface intuitiva** para demonstração  

## Fluxo de Dados Integrado

1. **ESP32** coleta dados dos sensores (fósforo, potássio, pH, umidade)
2. **Lógica inteligente** decide se aciona a bomba de irrigação
3. **Dados são exportados** em formato CSV
4. **Sistema Python** importa e processa os dados
5. **Dados são inseridos** na estrutura Oracle da Fase 3
6. **Relatórios e estatísticas** são gerados automaticamente

## Adaptação à Estrutura da Fase 3

O sistema **não cria novas tabelas**, mas adapta os dados ESP32 à estrutura existente:

### Sensores Criados Automaticamente:
- **Sensor Fósforo ESP32** (tipo: FO) - valores 0/1
- **Sensor Potássio ESP32** (tipo: PO) - valores 0/1
- **Sensor pH ESP32** (tipo: PH) - valores 0-14
- **Sensor Umidade ESP32** (tipo: UM) - valores 0-100%
- **Sensor Bomba ESP32** (tipo: BO) - valores 0/1

### Mapeamento de Dados:
```
CSV: 1,0,1,7.25,45.30,0
↓
5 inserções na T_MEDICOES:
- Medição 1, Sensor Fósforo: 0
- Medição 1, Sensor Potássio: 1
- Medição 1, Sensor pH: 7.25
- Medição 1, Sensor Umidade: 45.30
- Medição 1, Sensor Bomba: 0
```

## Componentes da Fase 4

### Entrega 1 - Sistema ESP32 Atualizado

| Componente | Função | Pino GPIO |
|------------|--------|-----------|
| ESP32 DevKit V1 | Microcontrolador principal | - |
| Switch Verde | Sensor de Fósforo | GPIO 18 |
| Switch Azul | Sensor de Potássio | GPIO 19 |
| LDR | Sensor de pH (luz) | GPIO 36 |
| Potenciômetro | Sensor de Umidade | GPIO 34 |
| LED + Relé | Bomba de Irrigação | GPIO 2 |

### Entrega 2 - Sistema Python Adaptado

#### Funcionalidades Implementadas:

1. **CREATE** - Inserção de Dados
   - Inserção manual de medições
   - Importação automática de CSV
   - Criação automática de sensores ESP32

2. **READ** - Consulta de Dados
   - Listagem de medições recentes
   - Visualização por tipo de sensor
   - Consultas filtradas por período

3. **UPDATE** - Atualização de Dados
   - Modificação de medições existentes
   - Atualização de configurações de sensores

4. **DELETE** - Exclusão de Dados
   - Remoção de medições específicas
   - Limpeza de dados antigos

5. **ANALYTICS** - Análises e Relatórios
   - Estatísticas por sensor
   - Médias, mínimos e máximos
   - Percentuais de ativação da bomba
   - Exportação de relatórios

---

# ⚙️ Instalação e Configuração

## Pré-requisitos

### Software Necessário:
- **Python 3.11+**
- **Oracle Database** (da Fase 3)
- **VS Code** com extensões:
  - PlatformIO IDE
  - Wokwi Simulator
- **Navegador web** (para Wokwi)

### Bibliotecas Python:
```bash
pip install oracledb
```

## Configuração do Ambiente

### 1. Oracle Database
- Certifique-se que o Oracle está rodando
- Serviço: `localhost:1522/ORCLPDB`
- Usuário: `RCOSTA` / Senha: `Rcosta@1980`
- Tabelas da Fase 3 devem existir

### 2. Verificação da Instalação
```bash
# Testar conexão Oracle
python -c "import oracledb; print('Oracle DB OK')"

# Testar conexão ao banco
python farmtech_fase3_adaptado.py
# Escolher opção 7 - Verificar tabelas
```

---

# 🚀 Como Executar

## Execução da Fase 3 - Entrega 1 (ESP32)

### 1. Configurar Projeto Wokwi
- Abra o VS Code
- Crie novo projeto PlatformIO
- Copie arquivos da `entrega1/`
- Configure `platformio.ini` para ESP32

### 2. Executar Simulação
```bash
# No VS Code:
1. Abrir src/main.cpp
2. Compilar (Ctrl+Alt+B)
3. Iniciar simulação Wokwi
4. Monitorar serial (Ctrl+Alt+M)
```

### 3. Interagir com Sensores
- **Switches:** Mover para simular nutrientes
- **Potenciômetro:** Ajustar para umidade
- **LDR:** Cobrir/descobrir para pH
- **LED:** Observar status da bomba

## Execução da Fase 3 - Entrega 2 (Sistema CRUD)

### 1. Executar Sistema Original
```bash
cd Entrega-2/
python Fase3_Cap1_Ent2_CRUD.py
```

### 2. Operações Disponíveis
- Importar dados dos arquivos CSV
- Executar operações CRUD básicas
- Realizar consultas analíticas
- Demonstrar integridade referencial

## Execução da Fase 4 (Sistema Integrado)

### 1. Executar Sistema Integrado
```bash
cd entrega2/
python farmtech_fase3_adaptado.py
```

### 2. Menu de Operações
```
=== MENU PRINCIPAL ===
1. Visualizar medicoes recentes ESP32
2. Importar dados CSV do ESP32
3. Inserir nova medicao ESP32 manualmente
4. Exibir estatisticas dos sensores ESP32
5. Exportar dados ESP32 para CSV
6. Verificar sensores ESP32 criados
7. Verificar tabelas da Fase 3
8. CRIAR SENSORES ESP32 (EXECUTAR PRIMEIRO)
0. Sair
```

### 3. Sequência de Primeira Execução
```bash
# 1. Criar sensores ESP32
Escolher opção: 8

# 2. Verificar criação
Escolher opção: 6

# 3. Importar dados CSV
Escolher opção: 2
Arquivo: dados_exemplo.csv

# 4. Visualizar resultados
Escolher opção: 1

# 5. Ver estatísticas
Escolher opção: 4
```

---

### 🎬 Demonstração em Vídeo

# Assista à Demonstração do CRUD que está na pasta "assets" - WokWi_CRUD.mkv
# Assista à Demonstração de Machine Learning que está na pasta "assets" - WokWi_CRUD.mkv
---

# 💻 Tecnologias Utilizadas

## Hardware (Simulado)
- **ESP32 DevKit V1** - Microcontrolador principal
- **Sensores digitais** - Switches para nutrientes
- **Sensores analógicos** - LDR e potenciômetro
- **Atuadores** - LED e módulo relé

## Software
- **C++** - Programação do ESP32
- **Python 3.11** - Sistema de gestão
- **Oracle Database** - Armazenamento de dados
- **Oracle** - Consultas e operações CRUD

## Ferramentas de Desenvolvimento
- **VS Code** - IDE principal
- **PlatformIO** - Framework ESP32
- **Wokwi** - Simulador de hardware
- **Oracle Oracle Developer** - Gestão do banco

## Bibliotecas e Dependências

### ESP32 (C++)
```cpp
#include <WiFi.h>
#include <DHT.h>
```

### Python
```python
import oracledb      # Conexão Oracle
import csv           # Processamento CSV
import logging       # Sistema de logs
import datetime      # Manipulação de datas
```

---

# 📊 Resultados Alcançados

## Métricas de Sucesso

### Funcionalidade
- ✅ **100% das operações CRUD** implementadas
- ✅ **5 tipos de sensores** funcionando
- ✅ **Lógica inteligente** de irrigação
- ✅ **Integração completa** ESP32 ↔ Oracle

### Compatibilidade
- ✅ **Estrutura Fase 3** preservada
- ✅ **Relacionamentos** mantidos
- ✅ **Integridade referencial** respeitada
- ✅ **Dados históricos** preservados

### Performance
- ✅ **Importação CSV:** 20 registros → 100 inserções
- ✅ **Tempo de resposta:** < 2 segundos por operação
- ✅ **Conexões Oracle:** Estáveis e confiáveis
- ✅ **Simulação Wokwi:** Tempo real

## Dados de Teste

### Exemplo de Estatísticas Geradas:
```
ESTATISTICAS DOS SENSORES ESP32:
FOSFORO: 20 medicoes | Media: 0.5 | Min: 0 | Max: 1
POTASSIO: 20 medicoes | Media: 0.6 | Min: 0 | Max: 1
PH: 20 medicoes | Media: 7.13 | Min: 5.9 | Max: 8.2
UMIDADE: 20 medicoes | Media: 47.8 | Min: 19.7 | Max: 75.2
BOMBA: 20 medicoes | Media: 0.3 | Min: 0 | Max: 1
```

---

# 🔧 Solução de Problemas

## Problemas Comuns e Soluções

### 1. Erro de Conexão Oracle
```
Erro: ORA-12541: TNS:no listener
```
**Solução:**
- Verificar se Oracle está rodando
- Confirmar porta 1522 disponível
- Testar credenciais RCOSTA/Rcosta@1980

### 2. Sensores ESP32 não encontrados
```
AVISO: Sensor Sensor Fosforo ESP32 nao encontrado!
```
**Solução:**
- Executar opção 8 (Criar sensores ESP32)
- Verificar com opção 6
- Confirmar criação bem-sucedida

### 3. Problemas no Wokwi
```
Botões não respondem
```
**Solução:**
- Usar switches ao invés de botões
- Verificar conexões no diagram.json
- Reiniciar simulação

---

# 📈 Conclusão

Este projeto demonstra a evolução completa de um sistema de irrigação inteligente, desde a implementação básica de sensores até a integração completa com banco de dados empresarial. A preservação da estrutura da Fase 3 garante continuidade e robustez, enquanto as novas funcionalidades da Fase 4 agregam valor prático e demonstram a aplicação de tecnologias modernas na agricultura.

## Principais Conquistas

- **Integração bem-sucedida** entre hardware simulado e software de gestão
- **Preservação total** da estrutura de dados da Fase 3
- **Sistema funcional** pronto para demonstração
- **Documentação completa** para replicação e manutenção
- **Base sólida** para futuras expansões e melhorias

---

**🌱 FarmTech Solutions - Inovação em Agricultura Inteligente 🚀**

