// Definicje komend
#define CMD_NONE 0    // Brak rozkazu
#define CMD_FIST 1    // Pięść
#define CMD_PEACE 2   // Gest peace (wskazujący i środkowy palec)

// Zmienna do przechowywania poprzedniej komendy
int lastCommand = -1;

void setup() {
  // Inicjalizacja komunikacji szeregowej
  Serial.begin(9600);
  Serial.println("Arduino gotowe do odbioru komend!");
  Serial.println("0 = Brak rozkazu");
  Serial.println("1 = Pięść");
  Serial.println("2 = Peace");
}

void loop() {
  // Jeśli są dostępne dane do odczytu
  if (Serial.available() > 0) {
    // Odczytaj komendę
    int command = Serial.read();
    
    // Wyświetl informację tylko jeśli komenda się zmieniła
    if (command != lastCommand) {
      lastCommand = command;
      
      // Wyświetl odpowiednią informację
      Serial.print("Otrzymano komendę: ");
      switch (command) {
        case CMD_FIST:
          Serial.println("1 - PIĘŚĆ");
          break;
          
        case CMD_PEACE:
          Serial.println("2 - PEACE");
          break;
          
        case CMD_NONE:
          Serial.println("0 - BRAK ROZKAZU");
          break;
          
        default:
          Serial.print("Nieznana komenda: ");
          Serial.println(command);
          break;
      }
    }
  }
  
  // Małe opóźnienie dla stabilności
  delay(50);
} 