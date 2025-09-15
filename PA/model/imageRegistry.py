import os
import shutil


class ImageRegistry:
    def __init__(self):
        self.images = {}
        self.slikaBrojac = 1
        self.image_directory = "./slike"
        self.output_directory = "./output"

        # Inicijalizacija registra učitavanjem postojećih slika
        self.initialize_registry()

    def initialize_registry(self):

        # Učitaj slike iz foldera slike
        if os.path.exists(self.image_directory):
            for image_file in os.listdir(self.image_directory):
                image_path = os.path.join(self.image_directory, image_file)
                if os.path.isfile(image_path):
                    self.register_existing_image(image_path)

        # Učitaj slike iz foldera output
        if os.path.exists(self.output_directory):
            for image_file in os.listdir(self.output_directory):
                image_path = os.path.join(self.output_directory, image_file)
                if os.path.isfile(image_path):
                    self.register_existing_image(image_path)

    def register_existing_image(self, image_path):
        image_id = str(self.slikaBrojac)
        self.slikaBrojac += 1

        self.images[image_id] = {
            "id": image_id,
            "path": image_path,
            "task_id": None,
            "used_in_tasks": [],
            "delete_flag": False,
            "filters": [],
            "processing_time": None,
            "size_before": self.get_image_size(image_path),
            "size_after": None
        }
        #print(f"Učitana postojeća slika: {image_path} sa ID-jem {image_id}")

    def add_image(self, image_path, task_id=None):

        if not os.path.exists(image_path):
            print("Greška! Putanja slike ne postoji.")
            return None

        image_id = str(self.slikaBrojac)
        self.slikaBrojac += 1

        # Odredi novu putanju slike u direktorijumu ./slike
        image_name = os.path.basename(image_path)  # Ime originalne slike
        new_image_path = os.path.join(self.image_directory, f"{image_name}")

        try:
            shutil.copy(image_path, new_image_path)
            print(f"Slika {image_name} je kopirana u direktorijum './slike' sa ID-jem: {image_id}.")
        except IOError as e:
            print(f"Greška prilikom kopiranja slike: {e}")
            return None


        self.images[image_id] = {
            "id": image_id,
            "path": new_image_path,
            "task_id": task_id,
            "used_in_tasks": [],
            "delete_flag": False,
            "filters": [],
            "processing_time": None,
            "size_before": self.get_image_size(image_path),
            "size_after": None
        }
        return image_id

    def set_task_id(self, image_id, task_id):
        """Ažuriraj task_id za sliku kada joj je dodeljen zadatak."""
        if image_id in self.images:
            self.images[image_id]["task_id"] = task_id

    def mark_image_as_used_in_task(self, image_id, task_id):
        """Postavi 'used_in_tasks' na True i dodaj zadatak u listu."""
        if image_id in self.images:
            self.images[image_id]["used_in_tasks"].append(task_id)

    def mark_for_deletion(self, image_id):
        if image_id in self.images:
            self.images[image_id]["delete_flag"] = True

    def delete_image(self, image_id):
        if image_id in self.images:
            image_info = self.images[image_id]
            if image_info["used_in_tasks"]:
                print(f"Slika {image_id} se koristi u zadacima i ne može biti obrisana dok se zadaci ne završe.")
                return False  # Ne može se izbrisati dok zadaci nisu završeni
            image_info = self.images.pop(image_id)
            image_path = image_info["path"]
            if os.path.exists(image_path):
                os.remove(image_path)  # Brišemo sliku sa diska
            print(f"Slika {image_id} je izbrisana iz registra i diska.")
            return True
        return False

    def add_filter_info(self, image_id, filter_name, processing_time, new_size):
        if image_id in self.images:
            self.images[image_id]["filters"].append(filter_name)
            self.images[image_id]["processing_time"] = processing_time
            self.images[image_id]["size_after"] = new_size

    def get_image_size(self, image_path):
        return os.path.getsize(image_path) if os.path.exists(image_path) else None

    def list_images(self):
        return [(image_id, info["path"]) for image_id, info in self.images.items()]

    def describe_image(self, image_id):
        return self.images.get(image_id, None)

    def can_process_image(self, image_id):
        """Check if image is marked for deletion."""
        return not self.images[image_id]["delete_flag"]