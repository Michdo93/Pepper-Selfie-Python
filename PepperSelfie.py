import os
import time
import cv2
import numpy as np
import qi
import xml.etree.ElementTree as ET

# Laden der lokalen Hilfsdateien
from Util import Util
from ImagePlayer import ImagePlayer

# Konfigurationsdatei
CONFIG_FILE = "config.xml"

class PepperSelfie:
    def __init__(self, application, session, xml):
        self.application = application
        self.session = session
        
        self.front_pressed = False
        self.stop_requested = False # Boolean-Variable, um die Anwendung zu stoppen
        self.image_taken = False # Boolean-Variable, um das aufgenommene Bild zu kennzeichnen
        self.frame = None # JFrame-Objekt
        self.image_cropped = None
        self.list_of_phrases = [] # Liste von Phrasen für die Spracherkennung

        # Handle für die Kamera
        self.camera_handle = None
        self.camera_handle_picture = None

        # Konfigurationen auslesen
        self.image_width = xml.find('IMAGE_WIDTH').text
        self.image_height = xml.find('IMAGE_HEIGHT').text
        self.number_images = xml.find('NUMBER_IMAGES').text
        self.logo_path = xml.find('LOGO_PATH').text
        self.word_recoginition_threshold = float(xml.find('WORD_RECOGNITION_THRESHOLD').text)
        self.stream_resolution = int(xml.find('STREAM_RESOLUTION').text)
        self.frame_rate = int(xml.find('FRAME_RATE').text)
        self.picture_resolution = int(xml.find('PICTURE_RESOLUTION').text)
        self.camera = int(xml.find('CAMERA').text)
        self.colorspace = int(xml.find('COLORSPACE').text)
        self.take_picture_keyword = xml.find('TAKE_PICTURE_KEYWORD').text
        self.application_handle = xml.find('APPLICATION_HANDLE').text
        self.window_name= xml.find('WINDOW_NAME').text
        self.caption = xml.find('CAPTION').text

        # Pepper-Roboter-Proxy-Objekte
        self.motion = session.service("ALMotion")
        self.animated_speech = session.service("ALAnimatedSpeech")
        self.video = session.service("ALVideoDevice")
        self.video = session.service("ALVideoDevice")
        self.al_memory = session.service("ALMemory")
        self.posture = session.service("ALRobotPosture")
        self.speech_recognition = session.service("ALSpeechRecognition")
        self.behavior_manager = session.service("ALBehaviorManager")

        self.list_of_phrases.append(self.take_picture_keyword)
        self.speech_recognition.setVocabulary(self.list_of_phrases, False)

        self.image_window = ImagePlayer(self.window_name, self.caption) # Fensterobjekt für die Bildanzeige

        self.al_memory.subscribeToEvent("FrontTactilTouched", self.application_handle, "on_front_tactil_touched")
        self.al_memory.subscribeToEvent("RearTactilTouched", self.application_handle, "on_rear_tactil_touched")

        self.motion.wakeUp()
        self.posture.goToPosture("StandInit", 1.0)

        self.animated_speech.say("Hallo nochmal! Zum Abschluss würde ich gerne zur Erinnerung noch ein Foto von Ihnen allen machen.")
        self.animated_speech.say("Ich selbst kann es mir natürlich in meinem Speicher anschauen, aber für die Menschen im Labor schicke ich das Bild zusätzlich an den Drucker.")
        self.animated_speech.say("Zum Starten der Anwendung berühren Sie mich bitte vorne am Kopf, zum Beenden hinten.")

    # Starten der Anwendung
    def start(self):
        try:
            # Die Kopfkamera von Pepper aktivieren
            self.camera_handle = self.video.subscribeCamera(self.application_handle, self.camera, self.stream_resolution, self.colorspace, self.frame_rate)
            self.camera_handle_picture = self.video.subscribeCamera(self.application_handle, self.camera, self.picture_resolution, self.colorspace, self.frame_rate)
            
            # Warum gibt es keine Callback-Methode die anzeigt, wann ein neues Frame verfuegbar ist???
		    # Individuelle Loesung...
            self.update_picture()
            
            self.animated_speech.say("Bitte für das Foto in Position gehen. Sagen Sie " + self.take_picture_keyword + ", wenn alle in Position sind.")
            self.posture.goToPosture("StandInit", 1.0)
            
            # Starte Spracherkennung
            self.speech_recognition.subscribe(self.application_handle)

            # Callback-Funktion für das Ereignis "WordRecognized"
            self.al_memory.subscribeToEvent("WordRecognized", self.application_handle, "on_word_recognized")
        except Exception as e:
            print("start() failed!")
            print(e)

    # Stoppen der Anwendung
    def stop(self):
        try:
            self.image_window.dispose()
            self.motion.rest()
            self.video.unsubscribe(self.camera_handle)
            self.video.unsubscribe(self.camera_handle_picture)
            self.behavior_manager.stopAllBehaviors()
            self.application.stop()
            os._exit(0)
        except Exception as e:
            print("stop() failed!")
            print(e)

    # Callback-Funktion für die Berührung des vorderen Tastsensors
    def on_front_tactil_touched(self, value):
        if value == 1.0 and not self.front_pressed:
            try:
                self.front_pressed = True
                self.start()
            except Exception as e:
                print("start() failed!")
                print(e)

    # Callback-Funktion für die Berührung des hinteren Tastsensors
    def on_rear_tactil_touched(self, value):
        if value == 1.0:
            try:
                self.speech_recognition.unsubscribe(self.application_handle)
                self.stop_requested = True
                self.animated_speech.say("Es hat mich sehr gefreut, Sie hier im Labor begrüßen zu dürfen. Ich wünsche Ihnen noch einen schönen Tag!")
                self.stop()
            except Exception as e:
                print("stop() failed!")
                print(e)

    # Auf das Ereignis "WordRecognized" reagieren
    def on_word_recognized(self, words):
        # Verarbeitung des erkannten Wortes
        # Hier können Sie Ihre Logik implementieren, um auf das erkannte Wort zu reagieren
        word = words[0]
        probability = words[1]

        if probability > 0.30 and not self.image_taken:
            try:
                self.animated_speech.say("Ok, ich mache ein Bild")
                # Beenden der Spracherkennung, um Mehrfacherkennungen zu vermeiden
                self.speech_recognition.unsubscribe(self.application_handle)
                # Unterbrechen des Live-Streams
                self.stop_requested = True
                # Bild aufnehmen
                self.take_picture()
            except Exception as e:
                print("takePicture() failed!")
                print(e)

    # Callback-Funktion für das Ereignis "RightBumperPressed"
    def on_right_bumper_pressed(self, touch):
        if touch == 1.0 and self.image_taken:
            try:
                self.image_taken = False
                self.animated_speech.say("Ok, ich schicke das Bild an den Drucker.")
                self.frame.dispose()

                Util.print_image(self.image_cropped, self.image_width, self.image_height, self.number_images)

                # Sprachsteuerung wieder starten
                self.speech_recognition.subscribe(self.application_handle)

                # Stream wieder starten
                self.stop_requested = False
                self.update_picture()
            except Exception as e:
                print("print_image() failed!")
                print(e)

    # Callback-Funktion für das Ereignis "LeftBumperPressed"
    def on_left_bumper_pressed(self, touch):
        if touch == 1.0 and self.image_taken:
            try:
                self.image_taken = False
                self.animated_speech.say("Ok, ich lösche das Bild.")
                self.frame.dispose()

                # Sprachsteuerung wieder starten
                self.speech_recognition.subscribe(self.application_handle)

                # Stream wieder starten
                self.stop_requested = False
                self.update_picture()
            except Exception as e:
                print("print_image() failed!")
                print(e)

    # Aktualisieren der Live-Bildausgabe
    def update_picture(self):
        try:
            remote_image_data = self.video.getImageRemote(self.camera_handle)
            buffered_image = Util.to_buffered_image(remote_image_data, self.image_height, self.image_width)

            self.image_window.update(buffered_image)

            if not self.stop_requested:
                time.sleep(1.0 / self.frame_rate)
                self.update_picture()
        except Exception as e:
            print("update_picture() failed!")
            print(e)

    # Aufnahme eines Bildes
    def take_picture(self):
        try:
            self.image_taken = True
            self.posture.goToPosture("StandInit", 1.0)

            time.sleep(1)

            self.behavior_manager.runBehavior("PlayCamera")

            remote_image_data = self.video.getImageRemote(self.camera_handle_picture)
            image = Util.to_buffered_image_picture(remote_image_data)
            self.image_cropped = image.crop((0, 0, image.width, 853))

            self.frame = self.image_window.display(self.image_cropped, "Aufgenommenes Bild")
            self.animated_speech.say("Gefällt Ihnen das aufgenommene Bild? Berühren Sie meinen rechten Bumper, wenn ich es ausdrucken soll, und meinen linken, wenn ich es löschen soll.")

            # Abonnement der Ereignisse
            self.al_memory.subscribeToEvent("RightBumperPressed", self.application_handle, "on_right_bumper_pressed")
            self.al_memory.subscribeToEvent("LeftBumperPressed", self.application_handle, "on_left_bumper_pressed")
        except Exception as e:
            print("take_picture() failed!")
            print(e)

if __name__ == "__main__":
    # Implementierung der Logik zum Laden der Konfigurationsdatei
    xml = ET.parse(CONFIG_FILE).getroot()

    ROBOT_URL = xml.find('PEPPER_IP').text
    ROBOT_PORT = xml.find('PEPPER_PORT').text

    app = qi.Application(["--qi-url=" + "tcp://" + ROBOT_URL + ":" + ROBOT_PORT])
    app.start()

    pepper = PepperSelfie(app, app.session, xml)

    app.run()
