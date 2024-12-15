# ====== IMPORTOWANIE BIBLIOTEK ======
# OpenCV - biblioteka do przetwarzania obrazu
# cv2 pozwala na:
# - odczyt obrazu z kamery
# - wyświetlanie obrazu
# - rysowanie na obrazie (linie, tekst)
# - przetwarzanie kolorów
import cv2

# MediaPipe - biblioteka Google do wykrywania ciała/twarzy/dłoni
# mp pozwala na:
# - wykrywanie punktów charakterystycznych dłoni
# - śledzenie ruchów dłoni
# - rozpoznawanie gestów
import mediapipe as mp

# NumPy - biblioteka do obliczeń numerycznych
# np pozwala na:
# - operacje na tablicach
# - obliczenia matematyczne
# - przekształcenia danych
import numpy as np

# Math - biblioteka matematyczna
# math pozwala na:
# - funkcje matematyczne (sqrt, pow)
# - stałe matematyczne (pi)
import math

# Serial - biblioteka do komunikacji szeregowej
# serial pozwala na:
# - komunikację z Arduino
# - wysyłanie i odbieranie danych przez USB
import serial
import serial.tools.list_ports  # Narzędzia do znajdowania portów COM

# Time - biblioteka do operacji czasowych
# time pozwala na:
# - opóźnienia w programie
# - pomiar czasu
import time

# ====== FUNKCJE POMOCNICZE ======

def find_arduino_port():
    """
    Znajduje port COM, na którym jest Arduino
    
    Jak to działa:
    1. Pobiera listę wszystkich portów COM
    2. Szuka portu z nazwą zawierającą 'Arduino' lub podobne
    3. Zwraca nazwę znalezionego portu lub None
    
    Returns:
        str: nazwa portu COM (np. 'COM3') lub None jeśli nie znaleziono
    """
    ports = list(serial.tools.list_ports.comports())  # Lista wszystkich portów
    for port in ports:
        # Szukamy charakterystycznych nazw dla Arduino
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            return port.device
    return None

# ====== INICJALIZACJA ARDUINO ======
# Próbujemy nawiązać połączenie z Arduino
arduino = None  # Zmienna do przechowywania połączenia z Arduino
try:
    # Automatyczne wykrywanie portu Arduino
    arduino_port = find_arduino_port()
    if arduino_port:
        print(f"Znaleziono Arduino na porcie: {arduino_port}")
        # Otwieramy połączenie:
        # - prędkość 9600 baudów (musi być taka sama w Arduino)
        # - timeout 1 sekunda (maksymalny czas oczekiwania na dane)
        arduino = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)  # Czekamy 2 sekundy na zresetowanie Arduino
        print("Połączono z Arduino")
    else:
        print("Nie znaleziono Arduino! Sprawdź połączenie.")
except Exception as e:
    print(f"Błąd podczas łączenia z Arduino: {e}")
    print("Program będzie działał bez komunikacji z płytką.")
    arduino = None

# ====== INICJALIZACJA MEDIAPIPE ======
# Moduł do detekcji dłoni z MediaPipe
mp_hands = mp.solutions.hands

# Konfiguracja detektora dłoni
hands = mp_hands.Hands(
    static_image_mode=False,  # False = tryb wideo (szybszy, ale mniej dokładny)
    max_num_hands=1,          # Wykrywanie maksymalnie jednej dłoni (więcej = wolniej)
    min_detection_confidence=0.5,  # Próg pewności dla wykrycia dłoni (0-1)
    min_tracking_confidence=0.5    # Próg pewności dla śledzenia dłoni (0-1)
)

# Moduł do rysowania punktów i linii
mp_draw = mp.solutions.drawing_utils

# ====== ZMIENNE GLOBALNE ======
# Zmienna do przechowywania aktualnego rozkazu
RozkazDrona = 0  # 0 = brak rozkazu, 1 = pięść, 2 = gest peace

# Poprzedni rozkaz - potrzebny do wykrycia zmiany
PoprzedniRozkaz = 0

# ====== STAŁE - PUNKTY CHARAKTERYSTYCZNE DŁONI ======
# MediaPipe wykrywa 21 punktów na dłoni (0-20)
# Każdy palec ma 4 punkty (0 = podstawa, 1-3 = stawy, 4 = czubek)
THUMB_POINTS = [1, 2, 3, 4]        # Kciuk
INDEX_POINTS = [5, 6, 7, 8]        # Wskazujący
MIDDLE_POINTS = [9, 10, 11, 12]    # Środkowy
RING_POINTS = [13, 14, 15, 16]     # Serdeczny
PINKY_POINTS = [17, 18, 19, 20]    # Mały

def send_to_arduino(command):
    """
    Wysyła komendę do Arduino
    
    Jak to działa:
    1. Sprawdza czy Arduino jest podłączone
    2. Konwertuje liczbę na bajty
    3. Wysyła przez port szeregowy
    
    Args:
        command: liczba 0-2 reprezentująca rozkaz
            0 = brak rozkazu
            1 = pięść
            2 = gest peace
    """
    if arduino is not None:
        try:
            arduino.write(bytes([command]))  # Konwersja liczby na bajty i wysłanie
        except:
            print("Błąd podczas wysyłania do Arduino!")

def calculate_distance(p1, p2, img):
    """
    Oblicza odległość między dwoma punktami i rysuje linię
    Args:
        p1, p2: punkty w formacie MediaPipe (x,y są znormalizowane do 0-1)
        img: obraz na którym będzie rysowana linia
    Returns:
        distance: odległość między punktami w pikselach
    """
    # Konwersja współrzędnych znormalizowanych na piksele
    x1, y1 = int(p1.x * img.shape[1]), int(p1.y * img.shape[0])
    x2, y2 = int(p2.x * img.shape[1]), int(p2.y * img.shape[0])
    
    # Rysowanie czerwonej linii między punktami
    cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    # Obliczanie odległości euklidesowej
    distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    return distance

def is_finger_up(finger_points, hand_landmarks):
    """
    Sprawdza czy palec jest wyprostowany (uniesiony do góry)
    Args:
        finger_points: lista indeksów punktów dla danego palca
        hand_landmarks: punkty charakterystyczne dłoni z MediaPipe
    Returns:
        bool: True jeśli palec jest wyprostowany, False w przeciwnym razie
    """
    # Pobieramy punkty palca (podstawa i czubek)
    base = hand_landmarks.landmark[finger_points[0]]
    tip = hand_landmarks.landmark[finger_points[3]]
    
    # Jeśli czubek palca jest wyżej (ma mniejszą współrzędną y) niż podstawa
    # to palec jest wyprostowany (pamiętaj, że w obrazie 0,0 jest w lewym górnym rogu)
    return tip.y < base.y

def detect_gesture(hand_landmarks):
    """
    Wykrywa gesty dłoni i ustawia RozkazDrona
    Args:
        hand_landmarks: punkty charakterystyczne dłoni z MediaPipe
    Returns:
        gesture: nazwa wykrytego gestu
    """
    global RozkazDrona, PoprzedniRozkaz  # Używamy zmiennych globalnych
    
    # Sprawdzamy pozycje palców
    index_up = is_finger_up(INDEX_POINTS, hand_landmarks)    # Czy wskazujący jest wyprostowany
    middle_up = is_finger_up(MIDDLE_POINTS, hand_landmarks)  # Czy środkowy jest wyprostowany
    ring_up = is_finger_up(RING_POINTS, hand_landmarks)      # Czy serdeczny jest wyprostowany
    pinky_up = is_finger_up(PINKY_POINTS, hand_landmarks)    # Czy mały jest wyprostowany
    
    # Pobieranie pozycji końcówek palców
    thumb_tip = hand_landmarks.landmark[4]   # Kciuk - końcówka
    index_tip = hand_landmarks.landmark[8]   # Wskazujący - końcówka
    middle_tip = hand_landmarks.landmark[12] # Środkowy - końcówka
    ring_tip = hand_landmarks.landmark[16]   # Serdeczny - końcówka
    pinky_tip = hand_landmarks.landmark[20]  # Mały - końcówka
    
    # Pobieranie pozycji podstawy dłoni (nadgarstek)
    wrist = hand_landmarks.landmark[0]
    
    # Lista końcówek palców do obliczenia średniej odległości
    finger_tips = [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]
    
    # Obliczanie średniej odległości palców od nadgarstka
    distances = []
    for tip in finger_tips:
        dist = math.sqrt((tip.x - wrist.x)**2 + (tip.y - wrist.y)**2)
        distances.append(dist)
    
    avg_distance = sum(distances) / len(distances)
    
    # Zapamiętujemy poprzedni rozkaz
    PoprzedniRozkaz = RozkazDrona
    
    # Klasyfikacja gestów i ustawienie RozkazDrona
    if avg_distance < 0.2:  # Jeśli palce są blisko nadgarstka - pięść
        RozkazDrona = 1  # Ustawienie rozkazu na 1 gdy wykryto pięść
        gesture = "Pięść"
    elif index_up and middle_up and not ring_up and not pinky_up:  # Tylko wskazujący i środkowy wyprostowane
        RozkazDrona = 2  # Ustawienie rozkazu na 2 dla gestu "peace"
        gesture = "Peace"
    else:
        RozkazDrona = 0  # Reset rozkazu gdy dłoń jest w innej pozycji
        gesture = "Inna pozycja"
    
    # Jeśli rozkaz się zmienił, wysyłamy go do Arduino
    if RozkazDrona != PoprzedniRozkaz:
        send_to_arduino(RozkazDrona)
    
    return gesture

# Inicjalizacja kamery (0 oznacza domyślną kamerę)
cap = cv2.VideoCapture(0)

# Główna pętla programu
while True:
    # Odczyt klatki z kamery
    success, img = cap.read()
    if not success:
        print("Nie można odczytać obrazu z kamery")
        break
    
    # Odbicie obrazu poziomo dla bardziej naturalnego widoku
    img = cv2.flip(img, 1)
    
    # Konwersja obrazu z BGR na RGB (wymagane przez MediaPipe)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Detekcja dłoni
    results = hands.process(img_rgb)
    
    # Jeśli wykryto dłoń
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Rysowanie punktów charakterystycznych dłoni
            mp_draw.draw_landmarks(
                img,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )
            
            # Wykrywanie gestu
            gesture = detect_gesture(hand_landmarks)
            
            # Obliczanie odległości między kciukiem a palcem wskazującym
            thumb_index_distance = calculate_distance(
                hand_landmarks.landmark[4],  # Kciuk
                hand_landmarks.landmark[8],  # Palec wskazujący
                img
            )
            
            # Wyświetlanie informacji na ekranie
            cv2.putText(img, f"Gest: {gesture}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, f"Odleglosc kciuk-wskazujacy: {int(thumb_index_distance)}px",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, f"RozkazDrona: {RozkazDrona}", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        # Jeśli nie wykryto dłoni, resetujemy RozkazDrona
        PoprzedniRozkaz = RozkazDrona
        RozkazDrona = 0
        if RozkazDrona != PoprzedniRozkaz:
            send_to_arduino(RozkazDrona)
        # Wyświetlamy aktualną wartość RozkazDrona
        cv2.putText(img, f"RozkazDrona: {RozkazDrona}", (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Wyświetlenie obrazu
    cv2.imshow("Hand Detector", img)
    
    # Wyjście z programu po naciśnięciu 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Zamknięcie połączenia z Arduino
if arduino is not None:
    arduino.close()

# Zwolnienie zasobów
cap.release()
cv2.destroyAllWindows() 