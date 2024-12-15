# ============= IMPORTOWANIE BIBLIOTEK =============
# Każda biblioteka to zestaw gotowych funkcji, które możemy wykorzystać
# Dzięki nim nie musimy pisać wszystkiego od zera

# OpenCV (Computer Vision - Widzenie Komputerowe)
# To jak oczy naszego programu - pozwala "widzieć" przez kamerę
# Biblioteka cv2 umożliwia:
# - włączenie kamery i pobieranie z niej obrazu
# - wyświetlanie okna z podglądem kamery
# - rysowanie na obrazie (linie, tekst, kształty)
# - zmianę kolorów, rozmiaru obrazu itp.
import cv2

# MediaPipe - zaawansowana biblioteka od Google
# To jak mózg rozpoznający kształty - tutaj konkretnie dłonie
# Pozwala na:
# - znalezienie dłoni w obrazie
# - określenie położenia palców (21 punktów na dłoni)
# - śledzenie ruchów dłoni w czasie rzeczywistym
# Używamy jej, bo sama jest już wytrenowana do rozpoznawania dłoni
import mediapipe as mp

# NumPy - biblioteka do obliczeń matematycznych
# To jak kalkulator naszego programu
# Przydaje się do:
# - szybkich obliczeń na wielu liczbach naraz
# - przekształcania danych z kamery
# - operacji matematycznych (średnie, odległości)
import numpy as np

# Math - podstawowa biblioteka matematyczna
# To jak prosty kalkulator - ma podstawowe funkcje matematyczne
# Używamy do:
# - pierwiastków kwadratowych (sqrt)
# - potęgowania (pow)
# - liczby PI i innych stałych matematycznych
import math

# Serial - biblioteka do komunikacji z Arduino
# To jak tłumacz między Pythonem a Arduino
# Pozwala na:
# - znalezienie podłączonego Arduino
# - wysyłanie komend do Arduino
# - odbieranie danych z Arduino
import serial
import serial.tools.list_ports  # Dodatkowe narzędzia do znajdowania Arduino

# Time - biblioteka do operacji związanych z czasem
# To jak zegarek programu
# Używamy do:
# - wprowadzania opóźnień (czekaj X sekund)
# - mierzenia czasu wykonania operacji
import time

# ============= FUNKCJE POMOCNICZE =============

def find_arduino_port():
    """
    Szuka podłączonego Arduino w systemie
    
    Jak to działa:
    1. Sprawdza wszystkie podłączone urządzenia przez USB
    2. Szuka takiego, które w nazwie ma 'Arduino' lub podobne
    3. Jeśli znajdzie - zwraca nazwę portu (np. 'COM3')
    4. Jeśli nie znajdzie - zwraca None (nic)
    
    Po co to robimy:
    - Arduino może być podłączone do różnych portów (COM3, COM4 itd.)
    - Zamiast zgadywać, program sam znajduje właściwy port
    - Dzięki temu użytkownik nie musi nic ustawiać ręcznie
    
    Returns:
        str: nazwa portu COM (np. 'COM3') lub None jeśli nie znaleziono
    """
    # Lista wszystkich podłączonych urządzeń
    ports = list(serial.tools.list_ports.comports())
    
    # Sprawdzamy każde urządzenie
    for port in ports:
        # Szukamy charakterystycznych nazw dla Arduino
        # Arduino może się pokazać jako:
        # - "Arduino Uno"
        # - "CH340" (nazwa układu USB używanego w niektórych Arduino)
        # - "USB Serial" (ogólna nazwa urządzeń szeregowych)
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            return port.device
    # Jeśli nic nie znaleźliśmy - zwracamy None
    return None

# ============= INICJALIZACJA ARDUINO =============
# To jak przygotowanie komunikacji z Arduino
arduino = None  # Na początku nie mamy połączenia

try:  # Próbujemy się połączyć (try - gdyby coś poszło nie tak)
    # Szukamy Arduino
    arduino_port = find_arduino_port()
    
    # Jeśli znaleźliśmy Arduino
    if arduino_port:
        print(f"Znaleziono Arduino na porcie: {arduino_port}")
        # Otwieramy połączenie:
        # - prędkość 9600 bodów (taka sama musi być ustawiona w Arduino)
        # - timeout 1s (maksymalny czas czekania na odpowiedź)
        arduino = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)  # Czekamy 2 sekundy - Arduino resetuje się po połączeniu
        print("Połączono z Arduino")
    else:
        print("Nie znaleziono Arduino! Sprawdź połączenie.")
except Exception as e:  # Jeśli wystąpił jakiś błąd
    print(f"Błąd podczas łączenia z Arduino: {e}")
    print("Program będzie działał bez komunikacji z płytką.")
    arduino = None  # Resetujemy zmienną - działamy bez Arduino

# ============= INICJALIZACJA MEDIAPIPE =============
# Przygotowanie systemu rozpoznawania dłoni

# Tworzymy detektor dłoni
mp_hands = mp.solutions.hands

# Konfigurujemy detektor:
hands = mp_hands.Hands(
    static_image_mode=False,  # False = tryb wideo (szybszy, ale mniej dokładny)
    max_num_hands=1,          # Szukamy tylko jednej dłoni (więcej = wolniej)
    min_detection_confidence=0.5,  # Pewność że to dłoń (0.5 = 50%)
    min_tracking_confidence=0.5    # Pewność podczas śledzenia ruchu
)

# Narzędzie do rysowania punktów i linii
mp_draw = mp.solutions.drawing_utils

# ============= ZMIENNE GLOBALNE =============
# Zmienne dostępne w całym programie

# Aktualny rozkaz dla drona
RozkazDrona = 0  # 0 = nic nie rób, 1 = pięść, 2 = znak V (peace)

# Poprzedni rozkaz - potrzebny do wykrycia zmiany
# (wysyłamy do Arduino tylko gdy rozkaz się zmieni)
PoprzedniRozkaz = 0

# ============= PUNKTY NA DŁONI =============
# MediaPipe wykrywa 21 punktów na dłoni (0-20)
# Każdy palec ma 4 punkty:
# - punkt 0: podstawa (gdzie palec łączy się z dłonią)
# - punkty 1-3: stawy palca
# - punkt 4: czubek palca

# Definiujemy punkty dla każdego palca
# (będziemy ich używać do sprawdzania czy palec jest wyprostowany)
THUMB_POINTS = [1, 2, 3, 4]        # Kciuk
INDEX_POINTS = [5, 6, 7, 8]        # Wskazujący
MIDDLE_POINTS = [9, 10, 11, 12]    # Środkowy
RING_POINTS = [13, 14, 15, 16]     # Serdeczny
PINKY_POINTS = [17, 18, 19, 20]    # Mały

def send_to_arduino(command):
    """
    Wysyła rozkaz do Arduino
    
    Jak to działa:
    1. Sprawdza czy Arduino jest podłączone
    2. Zamienia liczbę (0,1,2) na format który rozumie Arduino
    3. Wysyła przez port szeregowy
    
    Po co to robimy:
    - Arduino musi wiedzieć jaki gest pokazuje użytkownik
    - Wysyłamy liczby: 0 (brak gestu), 1 (pięść), 2 (peace)
    - Arduino może na tej podstawie wykonać różne akcje
    
    Args:
        command: liczba 0-2 reprezentująca rozkaz
            0 = brak rozkazu/reset
            1 = wykryto pięść
            2 = wykryto gest peace
    """
    # Jeśli Arduino jest podłączone
    if arduino is not None:
        try:
            # Wysyłamy komendę
            # bytes([command]) - zamiana liczby na format zrozumiały dla Arduino
            arduino.write(bytes([command]))
        except:
            print("Błąd podczas wysyłania do Arduino!")

def calculate_distance(p1, p2, img):
    """
    Oblicza odległość między dwoma punktami i rysuje linię
    
    Jak to działa:
    1. Zamienia współrzędne z formatu MediaPipe (0-1) na piksele
    2. Rysuje linię między punktami
    3. Oblicza odległość matematyczną między punktami
    
    Po co to robimy:
    - Chcemy widzieć połączenia między punktami na dłoni
    - Potrzebujemy znać odległości między palcami
    
    Args:
        p1, p2: punkty z MediaPipe (x,y w zakresie 0-1)
        img: obraz na którym rysujemy
    Returns:
        distance: odległość w pikselach
    """
    # Konwersja współrzędnych na piksele
    # MediaPipe używa współrzędnych 0-1, mnożymy przez rozmiar obrazu
    x1, y1 = int(p1.x * img.shape[1]), int(p1.y * img.shape[0])
    x2, y2 = int(p2.x * img.shape[1]), int(p2.y * img.shape[0])
    
    # Rysowanie czerwonej linii
    # (0,0,255) to kolor RGB - czerwony
    # 2 to grubość linii
    cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    # Obliczanie odległości (twierdzenie Pitagorasa)
    distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    return distance

def is_finger_up(finger_points, hand_landmarks):
    """
    Sprawdza czy palec jest wyprostowany (podniesiony do góry)
    
    Jak to działa:
    1. Bierze punkt podstawy palca i jego czubek
    2. Porównuje ich pozycję w pionie (współrzędna y)
    3. Jeśli czubek jest wyżej niż podstawa = palec wyprostowany
    
    Po co to robimy:
    - Chcemy wiedzieć które palce są wyprostowane
    - Na tej podstawie rozpoznajemy gesty (np. znak V)
    
    Args:
        finger_points: lista punktów danego palca
        hand_landmarks: wszystkie punkty dłoni z MediaPipe
    Returns:
        bool: True jeśli palec wyprostowany, False jeśli zgięty
    """
    # Pobieramy punkt podstawy i czubka palca
    base = hand_landmarks.landmark[finger_points[0]]  # Podstawa
    tip = hand_landmarks.landmark[finger_points[3]]   # Czubek
    
    # Sprawdzamy czy czubek jest wyżej niż podstawa
    # UWAGA: W obrazie y=0 jest na górze, a y rośnie w dół
    # Dlatego tip.y < base.y oznacza że czubek jest wyżej
    return tip.y < base.y

def detect_gesture(hand_landmarks):
    """
    Wykrywa gest dłoni i ustawia odpowiedni rozkaz
    
    Jak to działa:
    1. Sprawdza pozycję wszystkich palców
    2. Sprawdza odległości między punktami
    3. Na podstawie układu palców określa gest
    4. Ustawia odpowiedni RozkazDrona
    
    Po co to robimy:
    - Chcemy rozpoznać co pokazuje użytkownik
    - Na podstawie gestów sterujemy dronem
    
    Args:
        hand_landmarks: punkty dłoni z MediaPipe
    Returns:
        str: nazwa wykrytego gestu
    """
    global RozkazDrona, PoprzedniRozkaz
    
    # Sprawdzamy które palce są wyprostowane
    index_up = is_finger_up(INDEX_POINTS, hand_landmarks)    # Wskazujący
    middle_up = is_finger_up(MIDDLE_POINTS, hand_landmarks)  # Środkowy
    ring_up = is_finger_up(RING_POINTS, hand_landmarks)      # Serdeczny
    pinky_up = is_finger_up(PINKY_POINTS, hand_landmarks)    # Mały
    
    # Pobieramy pozycje czubków palców
    thumb_tip = hand_landmarks.landmark[4]   # Kciuk
    index_tip = hand_landmarks.landmark[8]   # Wskazujący
    middle_tip = hand_landmarks.landmark[12] # Środkowy
    ring_tip = hand_landmarks.landmark[16]   # Serdeczny
    pinky_tip = hand_landmarks.landmark[20]  # Mały
    
    # Punkt podstawy dłoni (nadgarstek)
    wrist = hand_landmarks.landmark[0]
    
    # Lista wszystkich czubków palców
    finger_tips = [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]
    
    # Obliczamy średnią odległość palców od nadgarstka
    distances = []
    for tip in finger_tips:
        # Dla każdego palca liczymy odległość od nadgarstka
        dist = math.sqrt((tip.x - wrist.x)**2 + (tip.y - wrist.y)**2)
        distances.append(dist)
    
    # Średnia odległość
    avg_distance = sum(distances) / len(distances)
    
    # Zapamiętujemy poprzedni rozkaz
    PoprzedniRozkaz = RozkazDrona
    
    # Rozpoznajemy gest
    if avg_distance < 0.2:  # Mała odległość = zaciśnięta pięść
        RozkazDrona = 1
        gesture = "Pięść"
    elif index_up and middle_up and not ring_up and not pinky_up:  # Znak V (peace)
        RozkazDrona = 2
        gesture = "Peace"
    else:  # Każdy inny układ palców
        RozkazDrona = 0
        gesture = "Inna pozycja"
    
    # Jeśli rozkaz się zmienił - wysyłamy do Arduino
    if RozkazDrona != PoprzedniRozkaz:
        send_to_arduino(RozkazDrona)
    
    return gesture

# ============= GŁÓWNA PĘTLA PROGRAMU =============

# Włączamy kamerę (0 = domyślna kamera)
cap = cv2.VideoCapture(0)

# Nieskończona pętla - program działa aż do naciśnięcia 'q'
while True:
    # Pobieramy klatkę z kamery
    success, img = cap.read()
    if not success:
        print("Nie można odczytać obrazu z kamery")
        break
    
    # Odbijamy obraz poziomo - będzie działać jak lustro
    img = cv2.flip(img, 1)
    
    # Konwertujemy obraz z BGR na RGB
    # (MediaPipe wymaga RGB, a OpenCV używa BGR)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Wykrywamy dłonie w obrazie
    results = hands.process(img_rgb)
    
    # Jeśli wykryto jakieś dłonie
    if results.multi_hand_landmarks:
        # Dla każdej wykrytej dłoni
        for hand_landmarks in results.multi_hand_landmarks:
            # Rysujemy punkty i połączenia
            mp_draw.draw_landmarks(
                img,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )
            
            # Wykrywamy gest
            gesture = detect_gesture(hand_landmarks)
            
            # Mierzymy odległość między kciukiem a palcem wskazującym
            thumb_index_distance = calculate_distance(
                hand_landmarks.landmark[4],  # Kciuk
                hand_landmarks.landmark[8],  # Wskazujący
                img
            )
            
            # Wyświetlamy informacje na ekranie
            cv2.putText(img, f"Gest: {gesture}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, f"Odleglosc kciuk-wskazujacy: {int(thumb_index_distance)}px",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, f"RozkazDrona: {RozkazDrona}", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        # Jeśli nie wykryto dłoni
        PoprzedniRozkaz = RozkazDrona
        RozkazDrona = 0
        if RozkazDrona != PoprzedniRozkaz:
            send_to_arduino(RozkazDrona)
        # Wyświetlamy aktualny rozkaz (0)
        cv2.putText(img, f"RozkazDrona: {RozkazDrona}", (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Wyświetlamy obraz
    cv2.imshow("Hand Detector", img)
    
    # Czekamy na klawisz
    # Jeśli naciśnięto 'q' - kończymy program
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Sprzątamy po zakończeniu
if arduino is not None:
    arduino.close()  # Zamykamy połączenie z Arduino
cap.release()  # Zwalniamy kamerę
cv2.destroyAllWindows()  # Zamykamy wszystkie okna 