import os
from threading import Thread, Lock
from queue import Queue
from multiprocessing import Pool
from datetime import datetime

from PIL import Image
import numpy as np

from model.imageRegistry import ImageRegistry
from model.taskRegistry import TaskRegistry
from utils.transformations import grayscale, gaussian_blur, adjust_brightness
from utils.utils import load_json_file



class CommandProcessor:
    def __init__(self):
        self.image_registry = ImageRegistry()
        self.task_registry = TaskRegistry(self.image_registry)
        self.task_queue = Queue()
        self.output_queue = Queue()
        self.lock = Lock()
        self.stop_signal = False
        self.pool = Pool(processes=4)
        self.finished_tasks = Queue()


    def process_image_task(self, task_id, image_id, transformations, output_file, blur_level=1, brightness_level=1):

        # Proverite da li slika može da se obradi pre nego što zadatak započne
        if not self.image_registry.can_process_image(image_id):
            print(f"Slika {image_id} je označena za brisanje i ne može se obraditi.")
            return

        # Ažuriraj task_id slike pre obrade
        self.image_registry.set_task_id(image_id, task_id)

        image_info = self.image_registry.describe_image(image_id)

        # Proveri da li putanja do slike postoji
        if image_info and os.path.exists(image_info["path"]):

            image_path = image_info["path"]
            image = Image.open(image_path)
            image_array = np.array(image)

            start_time = datetime.now()

            # Primena svake transformacije iz liste
            for transformation in transformations:
                if transformation == "grayscale":
                    image_array = grayscale(image_array)
                elif transformation == "blur":
                    image_array = gaussian_blur(image_array, sigma=blur_level)
                elif transformation == "brightness":
                    image_array = adjust_brightness(image_array, factor=brightness_level)

            # Konvertovanje niza nazad u sliku
            final_image = Image.fromarray(image_array)
            try:
                final_image.save(output_file)  # Sačuvaj na specificiranu putanju
                processing_time = (datetime.now() - start_time).total_seconds()

                # Ažuriraj registar slika sa informacijama o filterima i veličinom nakon obrade
                self.image_registry.add_filter_info(
                    image_id, transformations, processing_time, self.image_registry.get_image_size(output_file)
                )
                self.finished_tasks.put(task_id)  # Obeleži zadatak kao završen

                print(f"Obrađena slika sačuvana na: {output_file}")
            except Exception as e:
                print(f"Greška pri čuvanju slike: {e}")
        else:
            print("Greška: Putanja do slike nije pronađena ili nije validna.")


    def handle_command(self, command):
        parts = command.split()
        if parts[0] == "add":
            image_path = parts[1]
            if os.path.exists(image_path):
                image_id = self.image_registry.add_image(image_path)
                print(f"Slika dodata sa ID: {image_id}")
            else:
                print("Greska! Putanja slike ne postoji.")

        elif parts[0] == "process":
            json_path = parts[1]
            image_id, transformations, output_file, blur_level, brightness_level = load_json_file(json_path)

            image_info = self.image_registry.describe_image(image_id)
            if image_info and os.path.exists(image_info["path"]):
                task_id = self.task_registry.add_task(image_id, transformations)
                self.pool.apply_async(self.process_image_task(task_id, image_id, transformations, output_file, blur_level, brightness_level),callback=lambda _: self.finished_tasks.put(task_id))
            else:
                self.output_queue.put("Greska! Id slike nije pronadjen u registru slika.")

        elif parts[0] == "delete":
            image_id = parts[1]
            image_info = self.image_registry.describe_image(image_id)
            if image_info:
                self.image_registry.mark_for_deletion(image_id)  # Postavljanje oznake za brisanje
                if image_info["used_in_tasks"]:
                    print(f"Slika {image_id} se koristi u zadacima i ne može biti obrisana dok se zadaci ne završe.")
                else:
                    self.image_registry.delete_image(image_id)
                    print(f"Slika {image_id} je oznacena za brisanje.")

        elif parts[0] == "list":
            images = self.image_registry.list_images()
            for img_id, path in images:
                print(f"{img_id}: {path}")

        elif parts[0] == "describe":
            image_id = parts[1]
            description = self.image_registry.describe_image(image_id)
            print(description)

        elif parts[0] == "exit":
            self.stop_signal = True
            self.pool.close()
            self.pool.join()
            self.output_queue.put("Izlazak...")

    def command_listener(self):
        while not self.stop_signal:
            # Provera da li je stop_signal postavljen pre unosa komande
            if self.stop_signal:
                break
            command = input("Unesite komandu: ")
            # Ako je komanda exit, prekidamo sve
            if command.strip().lower() == "exit":
                self.stop_signal = True
                self.task_queue.put(None)  # Dodajemo None da prekinemo command_processor_thread
                self.output_queue.put("Izlazak...")  # Dodajemo poruku za izlaz
                break
            else:
                self.task_queue.put(command)

    def command_processor_thread(self):
        while not self.stop_signal:
            command = self.task_queue.get()
            if command is None:
                break  # Prekida se rad niti kada dobije None
            Thread(target=self.handle_command, args=(command,)).start()

    def output_handler(self):
        while not self.stop_signal:
            try:
                output = self.output_queue.get(timeout=1)
                if output == "Izlazak...":
                    print(output)
                    break
                print(output)
            except:
                continue

    def task_completion_monitor(self):
        while not self.stop_signal:
            try:
                task_id = self.finished_tasks.get(timeout=1)
                if task_id is None:
                    break  # Prekida rad kada dobije None
                self.task_registry.update_task_status(task_id, "finished")
                # Proverava status slike
                image_id = self.task_registry.tasks[task_id]["image_id"]
                image_info = self.image_registry.describe_image(image_id)

                # Ako je slika označena za brisanje i nema više aktivnih zadataka, briše sliku
                if image_info and image_info["delete_flag"] and not image_info["used_in_tasks"]:
                    self.image_registry.delete_image(image_id)
            except:
                continue


    def start(self):
        listener_thread = Thread(target=self.command_listener)
        processor_thread = Thread(target=self.command_processor_thread)
        output_thread = Thread(target=self.output_handler)
        completion_thread = Thread(target=self.task_completion_monitor)

        listener_thread.start()
        processor_thread.start()
        output_thread.start()
        completion_thread.start()

        listener_thread.join()
        processor_thread.join()
        output_thread.join()
        completion_thread.join()

        print("Sve niti su prekinute.")


if __name__ == "__main__":

    if not os.path.exists("output"):
        os.makedirs("output")
    if not os.path.exists("slike"):
        os.makedirs("slike")

    command_processor = CommandProcessor()

    print("PARALELNI SISTEM ZA OBRADU SLIKA")
    print("Dostupne komande: add, process, delete, list, describe, exit")

    command_processor.start()