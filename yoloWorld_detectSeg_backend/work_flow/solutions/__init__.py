import importlib


def load_handler_class(service_name):
    for service_names in service_handle_mapping:
        if service_name in service_names:
            module_path, class_name = service_handle_mapping[service_names]
            module = importlib.import_module(module_path)
            model_class = getattr(module, class_name)
            return model_class
    raise ValueError(f"Unknown model type: {service_name}")



service_handle_mapping = {
    ('上门做饭','煮正餐'): ("work_flow.solutions.cook_handler", "CookHandler")
}