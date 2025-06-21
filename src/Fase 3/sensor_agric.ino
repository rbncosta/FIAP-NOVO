/* ROBSON COSTA - RM - 565066

 * Sistema de Irrigação Inteligente - FarmTech Solutions
 * Este código implementa um sistema de monitoramento de solo e controle de irrigação
 * utilizando sensores simulados na plataforma Wokwi.
 
 * Sensores utilizados:
 * - Botão para simular sensor de Fósforo (P)
 * - Botão para simular sensor de Potássio (K)
 * - LDR para simular sensor de pH
 * - Potenciômetro para simular sensor de umidade do solo (substituindo o DHT22)
 
 * Atuadores:
 * - Relé para controle da bomba de irrigação
 * - LED embutido para indicação visual do status da bomba
 */

#include <Arduino.h>

// Definição dos pinos
#define PIN_FOSFORO 17    // Botão para simular sensor de Fósforo
#define PIN_POTASSIO 4    // Botão para simular sensor de Potássio
#define PIN_PH_LDR 21     // LDR para simular sensor de pH
#define PIN_UMIDADE 15    // Potenciômetro para simular sensor de umidade
#define PIN_RELE 2        // Relé para controle da bomba de irrigação
#define PIN_LED 2         // LED embutido para indicação visual

// Variáveis para armazenar os valores dos sensores
bool fosforo_presente = false;
bool potassio_presente = false;
int valor_ph = 0;
float umidade_solo = 0.0;
bool bomba_ativa = false;

// Parâmetros de controle
const float LIMITE_UMIDADE_BAIXA = 30.0;  // Limite inferior de umidade para ativar a bomba
const float LIMITE_UMIDADE_ALTA = 70.0;   // Limite superior de umidade para desativar a bomba
const int LIMITE_PH_BAIXO = 300;          // Valor simulado para pH ácido (valores menores)
const int LIMITE_PH_ALTO = 800;           // Valor simulado para pH alcalino (valores maiores)

// Intervalo de leitura dos sensores (em milissegundos)
const unsigned long INTERVALO_LEITURA = 2000;
unsigned long ultima_leitura = 0;

void setup() {
  // Inicialização da comunicação serial
  Serial.begin(115200);
  Serial.println("Sistema de Irrigação Inteligente - FarmTech Solutions");
  
  // Configuração dos pinos
  pinMode(PIN_FOSFORO, INPUT_PULLUP);  // Botão com resistor de pull-up interno
  pinMode(PIN_POTASSIO, INPUT_PULLUP); // Botão com resistor de pull-up interno
  pinMode(PIN_PH_LDR, INPUT);          // LDR como entrada analógica
  pinMode(PIN_UMIDADE, INPUT);         // Potenciômetro como entrada analógica
  pinMode(PIN_RELE, OUTPUT);           // Relé como saída
  pinMode(PIN_LED, OUTPUT);            // LED como saída
  
  // Inicialização do relé (desligado)
  digitalWrite(PIN_RELE, LOW);
  digitalWrite(PIN_LED, LOW);
  
  delay(1000); // Aguarda estabilização dos sensores
}

void loop() {
  // Verifica se é hora de fazer uma nova leitura
  unsigned long tempo_atual = millis();
  if (tempo_atual - ultima_leitura >= INTERVALO_LEITURA) {
    ultima_leitura = tempo_atual;
    
    // Leitura dos sensores
    lerSensores();
    
    // Análise dos dados e tomada de decisão
    analisarDadosEControlarBomba();
    
    // Exibição dos dados no monitor serial (para armazenamento posterior)
    exibirDados();
  }
}

void lerSensores() {
  // Leitura do sensor de Fósforo (botão)
  // Lógica invertida: LOW quando pressionado (presente), HIGH quando solto (ausente)
  fosforo_presente = !digitalRead(PIN_FOSFORO);
  
  // Leitura do sensor de Potássio (botão)
  // Lógica invertida: LOW quando pressionado (presente), HIGH quando solto (ausente)
  potassio_presente = !digitalRead(PIN_POTASSIO);
  
  // Leitura do sensor de pH (LDR)
  valor_ph = analogRead(PIN_PH_LDR);
  
  // Leitura do sensor de umidade (potenciômetro)
  // Convertendo a leitura analógica (0-4095) para porcentagem (0-100)
  int leitura_umidade = analogRead(PIN_UMIDADE);
  umidade_solo = map(leitura_umidade, 0, 4095, 0, 100);
}

void analisarDadosEControlarBomba() {
  // Lógica de controle da bomba de irrigação
  bool deve_ativar_bomba = false;
  
  // Verifica se a umidade está abaixo do limite mínimo
  if (umidade_solo < LIMITE_UMIDADE_BAIXA) {
    deve_ativar_bomba = true;
  }
  
  // Verifica se a umidade está acima do limite máximo
  if (umidade_solo > LIMITE_UMIDADE_ALTA) {
    deve_ativar_bomba = false;
  }
  
  // Condições adicionais que podem influenciar a decisão
  
  // Se o pH estiver muito ácido ou muito alcalino, evita irrigação
  if (valor_ph < LIMITE_PH_BAIXO || valor_ph > LIMITE_PH_ALTO) {
    deve_ativar_bomba = false;
  }
  
  // Se não houver nutrientes (fósforo e potássio), prioriza a irrigação
  // para melhorar a absorção de nutrientes que serão adicionados
  if (!fosforo_presente && !potassio_presente && umidade_solo < LIMITE_UMIDADE_ALTA) {
    deve_ativar_bomba = true;
  }
  
  // Atualiza o estado da bomba
  if (deve_ativar_bomba != bomba_ativa) {
    bomba_ativa = deve_ativar_bomba;
    digitalWrite(PIN_RELE, bomba_ativa ? HIGH : LOW);
    digitalWrite(PIN_LED, bomba_ativa ? HIGH : LOW);
    
    Serial.print("Status da bomba alterado: ");
    Serial.println(bomba_ativa ? "LIGADA" : "DESLIGADA");
  }
}

void exibirDados() {
  // Formato CSV para facilitar a importação para o banco de dados
  // timestamp,fosforo,potassio,ph,umidade,bomba_status
  
  // Timestamp simulado (segundos desde o início)
  unsigned long timestamp = millis() / 1000;
  
  Serial.print(timestamp);
  Serial.print(",");
  Serial.print(fosforo_presente ? "1" : "0");
  Serial.print(",");
  Serial.print(potassio_presente ? "1" : "0");
  Serial.print(",");
  Serial.print(valor_ph);
  Serial.print(",");
  Serial.print(umidade_solo);
  Serial.print(",");
  Serial.println(bomba_ativa ? "1" : "0");
}
