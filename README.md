# FunFact
Cała aplikacja jest napisana przez AI, niemal brak użycia własnego kodu
Same umiejętności promptowania :D
(chyba AI zabiera mi prace 🤪)
# System Detekcji Gestów Dłoni

## Opis
Program służy do wykrywania gestów dłoni poprzez kamerę i może współpracować z Arduino. System rozpoznaje następujące gesty:
- Pięść (Rozkaz 1)
- Gest "peace" - wskazujący i środkowy palec uniesione (Rozkaz 2)
- Inne pozycje dłoni (Rozkaz 0)

## Wymagania
- Python 3.10.9
- Kamera internetowa
- (Opcjonalnie) Arduino Uno lub podobne

## Instalacja

1. Zainstaluj Python 3.10.9 ze strony: https://www.python.org/downloads/release/python-3109/
   - WAŻNE: Podczas instalacji zaznacz "Add Python to PATH"

2. Zainstaluj wymagane biblioteki:
```bash
python -m pip install opencv-python==4.8.0.74
python -m pip install mediapipe==0.10.20
python -m pip install numpy==1.24.3
python -m pip install pyserial
```

## Uruchomienie

### Tryb bez Arduino:
1. Otwórz terminal/cmd
2. Przejdź do folderu z programem
3. Uruchom:
```bash
python hand_detector.py
```

### Tryb z Arduino:
1. Wgraj kod `drone_controller.ino` do Arduino używając Arduino IDE
2. Podłącz Arduino przez USB
3. Uruchom program Python jak wyżej

## Obsługa
- Program automatycznie wykrywa dłoń w obrazie z kamery
- Wyświetla wykryte gesty i odpowiadające im rozkazy
- Naciśnij 'q' aby zakończyć program

## Struktura projektu
- `hand_detector.py` - główny program Python
- `drone_controller.ino` - kod dla Arduino
- `requirements.txt` - lista wymaganych bibliotek
- `prompts.txt` - zapisane ustawienia Cursor AI
- `INSTRUKCJA.txt` - szczegółowa instrukcja obsługi 
