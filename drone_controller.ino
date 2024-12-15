/*
 * Program do sterowania portami Arduino na podstawie gestów dłoni
 * 
 * ============= INSTRUKCJA PODŁĄCZENIA =============
 * 
 * Potrzebne elementy:
 * - Arduino (dowolny model)
 * - 4 diody LED (dowolny kolor)
 * - 4 rezystory 220Ω (lub podobne, dla zabezpieczenia LED)
 * - przewody połączeniowe
 * 
 * Schemat podłączenia:
 * 1. LED dla dłoni otwartej:
 *    - Anoda (+, dłuższa nóżka) -> rezystor -> PIN 11
 *    - Katoda (-, krótsza nóżka) -> GND (masa)
 * 
 * 2. LED dla pięści:
 *    - Anoda (+) -> rezystor -> PIN 4
 *    - Katoda (-) -> GND
 * 
 * 3. LED dla gestu peace:
 *    - Anoda (+) -> rezystor -> PIN 7
 *    - Katoda (-) -> GND
 * 
 * 4. LED dla braku dłoni:
 *    - Anoda (+) -> rezystor -> PIN 9
 *    - Katoda (-) -> GND
 * 
 * WAŻNE:
 * - Zawsze używaj rezystorów do zabezpieczenia LED
 * - Sprawdź polaryzację LED (dłuższa nóżka to +)
 * - Upewnij się, że wszystkie masy (GND) są połączone
 * 
 * Działanie:
 * - Dłoń otwarta -> świeci LED na pinie 11
 * - Pięść -> świeci LED na pinie 4
 * - Gest peace -> świeci LED na pinie 7
 * - Brak dłoni -> świeci LED na pinie 9
 * 
 * Test układu:
 * 1. Podłącz Arduino do komputera
 * 2. Wgraj ten kod
 * 3. Po uruchomieniu powinna zaświecić się LED braku dłoni (PIN 9)
 * 4. Uruchom program Python i sprawdź reakcję na gesty
 */

// Komendy otrzymywane z Pythona
const int GEST_DLON_OTWARTA = 0;
const int GEST_PIESC = 1;
const int GEST_PEACE = 2;
const int GEST_BRAK_DLONI = 3;

// Przypisanie portów do gestów
const int PORT_DLON_OTWARTA = 11;  // LED 1 - dłoń otwarta
const int PORT_PIESC = 4;          // LED 2 - pięść
const int PORT_PEACE = 7;          // LED 3 - gest peace
const int PORT_BRAK_DLONI = 9;     // LED 4 - brak dłoni

// Zmienna do przechowywania aktualnej komendy
int aktualnaKomenda = GEST_BRAK_DLONI;

void wylaczWszystkiePorty() {
  digitalWrite(PORT_DLON_OTWARTA, LOW);
  digitalWrite(PORT_PIESC, LOW);
  digitalWrite(PORT_PEACE, LOW);
  digitalWrite(PORT_BRAK_DLONI, LOW);
}

void obsluzKomende(int komenda) {
  wylaczWszystkiePorty();
  
  // Debug - wyświetl otrzymaną komendę
  Serial.print("Otrzymano komende: ");
  Serial.println(komenda);
  
  switch (komenda) {
    case GEST_DLON_OTWARTA:
      digitalWrite(PORT_DLON_OTWARTA, HIGH);
      Serial.println("Aktywuję port 11");
      break;
    case GEST_PIESC:
      digitalWrite(PORT_PIESC, HIGH);
      Serial.println("Aktywuję port 4");
      break;
    case GEST_PEACE:
      digitalWrite(PORT_PEACE, HIGH);
      Serial.println("Aktywuję port 7");
      break;
    case GEST_BRAK_DLONI:
      digitalWrite(PORT_BRAK_DLONI, HIGH);
      Serial.println("Aktywuję port 9");
      break;
    default:
      Serial.print("Nieznana komenda: ");
      Serial.println(komenda);
      break;
  }
}

void setup() {
  Serial.begin(9600);
  
  pinMode(PORT_DLON_OTWARTA, OUTPUT);
  pinMode(PORT_PIESC, OUTPUT);
  pinMode(PORT_PEACE, OUTPUT);
  pinMode(PORT_BRAK_DLONI, OUTPUT);
  
  wylaczWszystkiePorty();
  digitalWrite(PORT_BRAK_DLONI, HIGH);
  
  Serial.println("Ready");
}

void loop() {
  if (Serial.available() > 0) {
    int nowaKomenda = Serial.read();
    
    // Debug - pokaż surową wartość
    Serial.print("Surowa wartość: ");
    Serial.println(nowaKomenda);
    
    if (nowaKomenda != aktualnaKomenda) {
      aktualnaKomenda = nowaKomenda;
      obsluzKomende(aktualnaKomenda);
    }
  }
  delay(500);
} 