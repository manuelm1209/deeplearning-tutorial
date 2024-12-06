import os
import yaml
from dotenv import load_dotenv
from crewai import Agent, Task, Crew

load_dotenv()

openai_model_name = os.environ.get("OPENAI_MODEL_NAME")
openai_api_key = os.environ.get("OPENAI_API_KEY")
print(f"Model: {openai_model_name}")

# Define file paths for YAML configurations
files = {
    'agents': 'config/agents.yaml',
    'tasks': 'config/tasks.yaml'
}

# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
agents_config = configs['agents']
tasks_config = configs['tasks']