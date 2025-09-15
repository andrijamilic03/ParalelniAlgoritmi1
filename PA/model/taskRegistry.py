from threading import Condition



class TaskRegistry:
    def __init__(self, image_registry):
        self.tasks = {}
        self.taskBrojac = 1
        self.condition = Condition()
        self.image_registry = image_registry

    def add_task(self, image_id, transformations):
        task_id = str(self.taskBrojac)
        self.taskBrojac += 1
        self.tasks[task_id] = {
            "id": task_id,
            "image_id": image_id,
            "transformations": transformations,
            "status": "waiting"
        }
        self.image_registry.mark_image_as_used_in_task(image_id, task_id)
        return task_id

    def update_task_status(self, task_id, status):
        with self.condition:
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = status
                self.condition.notify_all()
