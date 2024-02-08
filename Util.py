import os
import platform
import numpy as np
import cv2
import xml.etree.cElementTree as ET
from PIL import Image, ImageDraw, ImageFont

class Util:
    HEIGHT = 640
    WIDTH = 480
    
    HEIGHT_PIC = 1280
    WIDTH_PIC = 960

    @staticmethod
    def to_buffered_image(remote_image_data, height, width):
        buffer = remote_image_data[6]
        data = buffer.array()

        int_array = np.zeros(height * width * 3, dtype=np.uint8)
        for i in range(height * width):
            int_array[i * 3] = data[i * 3 + 2]  # R
            int_array[i * 3 + 1] = data[i * 3 + 1]  # G
            int_array[i * 3 + 2] = data[i * 3]  # B

        img = int_array.reshape((height, width, 3))
        return img

    @staticmethod
    def to_buffered_image_picture(remote_image_data):
        buffer = remote_image_data[6]
        data = buffer.array()

        int_array = np.zeros(Util.HEIGHT_PIC * Util.WIDTH_PIC * 3, dtype=np.uint8)
        for i in range(Util.HEIGHT_PIC * Util.WIDTH_PIC):
            int_array[i * 3] = data[i * 3 + 2]  # R
            int_array[i * 3 + 1] = data[i * 3 + 1]  # G
            int_array[i * 3 + 2] = data[i * 3]  # B

        img = int_array.reshape((Util.HEIGHT_PIC, Util.WIDTH_PIC, 3))
        img = Util.add_text(img)

        return img

    @staticmethod
    def add_text(img, config_file):
        tree = ET.parse(config_file)
        root = tree.getroot()

        image_text = root.find("imageText").text
        image_date = root.find("imageDate").text
        position_x = int(root.find("positionX").text)

        # OpenCV zum Konvertieren von NumPy-Array zu Bild verwenden
        img_pil = Image.fromarray(img)

        # Text zum Bild hinzufügen
        draw = ImageDraw.Draw(img_pil)

        # Schriftart laden
        font_path = "arialn.ttf"  # Pfad zur Schriftart "Arial Narrow" anpassen
        font = ImageFont.truetype(font_path, 50)  # Schriftart und -größe anpassen

        draw.text((position_x, 70), image_text, fill=(255, 255, 255), font=font)  # Position und Farbe anpassen
        draw.text((500, 120), image_date, fill=(255, 255, 255), font=font)  # Position und Farbe anpassen

        # Logo laden und zum Bild hinzufügen
        logo_path = "logo.png"  # Pfad zum Logo anpassen
        logo = Image.open(logo_path)
        img_pil.paste(logo, (0, 0), logo)

        # Bild wieder in NumPy-Array konvertieren und zurückgeben
        img_with_text = np.array(img_pil)
        return img_with_text

    @staticmethod
    def print_image(image):
        # Plattformabhängige Druckbibliothek importieren
        system_platform = platform.system()

        if system_platform == "Windows":
            from win32print import GetDefaultPrinter, OpenPrinter, ClosePrinter, StartDocPrinter, StartPagePrinter, EndPagePrinter, EndDocPrinter, WritePrinter
            from win32ui import CreateDC, CreateBitmap, GetDeviceCaps, StretchBlt, SRCCOPY, DeleteDC

            # Druckereinstellungen
            printer_name = GetDefaultPrinter()
            printer_handle = OpenPrinter(printer_name)
            printer_dc = CreateDC()
            printer_dc.CreatePrinterDC(printer_name)

            # Bild in temporäres Dateiformat konvertieren
            temp_file = "temp_image.bmp"
            cv2.imwrite(temp_file, image)

            # Bitmap erstellen
            bmp = CreateBitmap()
            bmp.CreateCompatibleBitmap(printer_dc, GetDeviceCaps(printer_dc.GetSafeHdc(), HORZRES), GetDeviceCaps(printer_dc.GetSafeHdc(), VERTRES))
            printer_dc.SelectObject(bmp)

            # Druckauftrag starten
            StartDocPrinter(printer_handle, 1, ("Image", None, None))
            StartPagePrinter(printer_dc)

            # Bild drucken
            img = Image.open(temp_file)
            img = img.convert("1")  # Monochrombild für Drucker
            img.save(printer_dc, "bmp")

            # Druckauftrag beenden
            EndPagePrinter(printer_dc)
            EndDocPrinter(printer_dc)

            # Aufräumen
            DeleteDC(printer_dc.GetSafeHdc())
            ClosePrinter(printer_handle)
        elif system_platform == "Linux":
            import cups

            # Drucker suchen
            conn = cups.Connection()
            printers = conn.getPrinters()
            printer_name = list(printers.keys())[0]  # Den ersten verfügbaren Drucker auswählen

            # Bild drucken
            conn.printFile(printer_name, "temp_image.bmp", "Python_Print", {})
        elif system_platform == "Darwin":
            print("Drucken auf macOS wird derzeit nicht unterstützt.")
        else:
            print("Unbekanntes Betriebssystem. Drucken nicht möglich.")

        # Temporäre Datei löschen
        os.remove("temp_image.bmp")
