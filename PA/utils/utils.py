import json


def load_json_file(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
        image_id = data.get("image_id")
        transformations = data.get("transformations")
        output_file = data.get("output_file")
        blur_level = data.get("blur_level")
        brightness_level = data.get("brightness_level")

        return image_id, transformations, output_file, blur_level, brightness_level