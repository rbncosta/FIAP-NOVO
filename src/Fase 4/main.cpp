/*
 * Sistema de Irrigação Inteligente - FarmTech Solutions
 */

#include <Arduino.h>
#include <DHT.h>

// Definição dos pinos
#define PIN_PH_LDR 36     // LDR para simular sensor de pH (pino ADC)
#define PIN_UMIDADE 34    // Potenciômetro para simular umidade do solo (pino ADC)
#define PIN_RELE 2        // Relé para controle da bomba de irrigação
#define PIN_LED 2         // LED embutido para indicação visual

// Configuração do sensor DHT22 (mantido como backup)
#define DHT_TYPE DHT22
DHT dht(15, DHT_TYPE);

// Declaração das funções (protótipos)
void simularCenario();
void lerSensores();
void analisarDadosEControlarBomba();
void exibirDadosCSV();

// Variáveis para armazenar os valores dos sensores
bool fosforo_presente = false;
bool potassio_presente = false;
float valor_ph = 0.0;
float umidade_solo = 0.0;
bool bomba_ativa = false;

// Parâmetros de controle
const float LIMITE_UMIDADE_BAIXA = 30.0;
const float LIMITE_UMIDADE_ALTA = 70.0;
const float LIMITE_PH_BAIXO = 6.0;
const float LIMITE_PH_ALTO = 8.0;

// Variáveis para simulação automática
unsigned long ultima_leitura = 0;
const unsigned long INTERVALO_LEITURA = 3000; // 3 segundos para demonstração
unsigned long contador_medicoes = 0;
int cenario_atual = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=== Sistema de Irrigação Inteligente - FarmTech Solutions ===");
  Serial.println("VERSÃO DEMONSTRAÇÃO AUTOMÁTICA");
  Serial.println("Simulando diferentes cenários automaticamente...");
  
  // Configuração dos pinos
  pinMode(PIN_RELE, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  
  // Inicialização do DHT22
  dht.begin();
  
  // Estado inicial da bomba (desligada)
  digitalWrite(PIN_RELE, LOW);
  digitalWrite(PIN_LED, LOW);
  bomba_ativa = false;
  
  Serial.println("Sistema inicializado!");
  Serial.println("Demonstrando 6 cenários diferentes...");
  Serial.println("=====================================");
  
  ultima_leitura = millis();
}

void loop() {
  unsigned long tempo_atual = millis();
  if (tempo_atual - ultima_leitura >= INTERVALO_LEITURA) {
    ultima_leitura = tempo_atual;
    contador_medicoes++;
    
    // Simular diferentes cenários automaticamente
    simularCenario();
    
    // Leitura dos sensores (reais + simulados)
    lerSensores();
    
    // Análise dos dados e tomada de decisão
    analisarDadosEControlarBomba();
    
    // Exibição dos dados no monitor serial
    exibirDadosCSV();
    
    // Avançar para próximo cenário
    cenario_atual = (cenario_atual + 1) % 6;
    
    Serial.println(""); // Linha em branco para separar cenários
  }
}

void simularCenario() {
  Serial.print(">>> CENÁRIO ");
  Serial.print(cenario_atual + 1);
  Serial.print("/6: ");
  
  switch(cenario_atual) {
    case 0:
      Serial.println("SEM NUTRIENTES + UMIDADE NORMAL");
      fosforo_presente = false;
      potassio_presente = false;
      umidade_solo = 45.0;
      valor_ph = 7.2;
      break;
      
    case 1:
      Serial.println("APENAS FÓSFORO + UMIDADE BAIXA");
      fosforo_presente = true;
      potassio_presente = false;
      umidade_solo = 25.0;
      valor_ph = 7.0;
      break;
      
    case 2:
      Serial.println("APENAS POTÁSSIO + UMIDADE ALTA");
      fosforo_presente = false;
      potassio_presente = true;
      umidade_solo = 75.0;
      valor_ph = 6.8;
      break;
      
    case 3:
      Serial.println("AMBOS NUTRIENTES + pH ÁCIDO");
      fosforo_presente = true;
      potassio_presente = true;
      umidade_solo = 40.0;
      valor_ph = 5.5; // pH muito ácido
      break;
      
    case 4:
      Serial.println("AMBOS NUTRIENTES + pH ALCALINO");
      fosforo_presente = true;
      potassio_presente = true;
      umidade_solo = 50.0;
      valor_ph = 8.5; // pH muito alcalino
      break;
      
    case 5:
      Serial.println("CONDIÇÕES IDEAIS");
      fosforo_presente = true;
      potassio_presente = true;
      umidade_solo = 55.0;
      valor_ph = 7.0; // pH ideal
      break;
  }
}

void lerSensores() {
  // Leitura do sensor de pH (LDR) - valor real do potenciômetro
  int leitura_ldr = analogRead(PIN_PH_LDR);
  float ph_ldr = map(leitura_ldr, 0, 4095, 0, 1400) / 100.0;
  
  // Leitura do sensor de umidade (potenciômetro) - valor real
  int leitura_umidade_pot = analogRead(PIN_UMIDADE);
  float umidade_pot = map(leitura_umidade_pot, 0, 4095, 0, 100);
  
  // Mostrar valores reais dos sensores físicos (para referência)
  Serial.print("Sensores físicos - pH LDR: ");
  Serial.print(ph_ldr, 1);
  Serial.print(" | Umidade POT: ");
  Serial.print(umidade_pot, 1);
  Serial.println("%");
  
  // Usar valores simulados para demonstração
  // (os valores já foram definidos na função simularCenario)
  
  // Tentativa de leitura do DHT22 como backup
  float umidade_dht = dht.readHumidity();
  if (!isnan(umidade_dht)) {
    Serial.print("DHT22 funcionando - Umidade: ");
    Serial.print(umidade_dht, 1);
    Serial.println("%");
  }
}

void analisarDadosEControlarBomba() {
  bool deve_ativar_bomba = false;
  String motivo_decisao = "";
  
  // Lógica principal: controle baseado na umidade
  if (umidade_solo < LIMITE_UMIDADE_BAIXA) {
    deve_ativar_bomba = true;
    motivo_decisao = "Umidade baixa (" + String(umidade_solo, 1) + "%)";
  } else if (umidade_solo > LIMITE_UMIDADE_ALTA) {
    deve_ativar_bomba = false;
    motivo_decisao = "Umidade alta (" + String(umidade_solo, 1) + "%)";
  } else {
    motivo_decisao = "Umidade normal (" + String(umidade_solo, 1) + "%)";
  }
  
  // Se o pH estiver fora da faixa ideal, bloqueia irrigação
  if (valor_ph < LIMITE_PH_BAIXO) {
    deve_ativar_bomba = false;
    motivo_decisao = "pH muito ácido (" + String(valor_ph, 1) + ") - irrigação bloqueada";
  } else if (valor_ph > LIMITE_PH_ALTO) {
    deve_ativar_bomba = false;
    motivo_decisao = "pH muito alcalino (" + String(valor_ph, 1) + ") - irrigação bloqueada";
  }
  
  // Se não houver nutrientes, força irrigação
  if (!fosforo_presente && !potassio_presente) {
    deve_ativar_bomba = true;
    motivo_decisao = "SEM NUTRIENTES - Irrigação forçada para preparar solo";
  }
  
  // Se houver apenas um nutriente, liga bomba também
  if ((fosforo_presente && !potassio_presente) || (!fosforo_presente && potassio_presente)) {
    deve_ativar_bomba = true;
    motivo_decisao = "Nutriente parcial - Irrigação para balanceamento";
  }
  
  // Atualiza o estado da bomba
  bomba_ativa = deve_ativar_bomba;
  digitalWrite(PIN_RELE, bomba_ativa ? HIGH : LOW);
  digitalWrite(PIN_LED, bomba_ativa ? HIGH : LOW);
  
  // Log detalhado
  Serial.println("=== ANÁLISE DOS SENSORES ===");
  Serial.print("Fósforo: ");
  Serial.println(fosforo_presente ? "PRESENTE" : "AUSENTE");
  Serial.print("Potássio: ");
  Serial.println(potassio_presente ? "PRESENTE" : "AUSENTE");
  Serial.print("pH: ");
  Serial.println(valor_ph, 2);
  Serial.print("Umidade: ");
  Serial.print(umidade_solo, 1);
  Serial.println("%");
  Serial.print("BOMBA: ");
  Serial.println(bomba_ativa ? "LIGADA ⚡" : "DESLIGADA");
  Serial.print("Motivo: ");
  Serial.println(motivo_decisao);
  Serial.println("============================");
}

void exibirDadosCSV() {
  // Formato CSV para importação no banco de dados
  Serial.print(contador_medicoes);
  Serial.print(",");
  Serial.print(fosforo_presente ? "1" : "0");
  Serial.print(",");
  Serial.print(potassio_presente ? "1" : "0");
  Serial.print(",");
  Serial.print(valor_ph, 2);
  Serial.print(",");
  Serial.print(umidade_solo, 1);
  Serial.print(",");
  Serial.println(bomba_ativa ? "1" : "0");
}

