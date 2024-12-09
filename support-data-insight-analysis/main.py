# Warning control
import warnings
import os
import yaml
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
from crewai_tools import FileReadTool


warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

print(f"Model: {os.environ['OPENAI_MODEL_NAME']}")

# llm = LLM(
#     model="ollama/llama3.1",
#     base_url="http://localhost:11434"
# )

# Determine the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
## Loading Tasks and Agents YAML files
# Define file paths for YAML configurations
files = {
    'agents': os.path.join(BASE_DIR, 'config','agents.yaml'),
    'tasks': os.path.join(BASE_DIR, 'config','tasks.yaml'),
}

# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
agents_config = configs['agents']
tasks_config = configs['tasks']


## Using FileReadTool
# csv_tool = FileReadTool(file_path='./support-data-insight-analysis/support_tickets_data.csv')
#? TESTING PATH
csv_tool = FileReadTool(file_path=os.path.join(BASE_DIR, 'support_tickets_data.csv'))

## Creating Agents, Tasks and Crew
# Creating Agents
suggestion_generation_agent = Agent(
  config=agents_config['suggestion_generation_agent'],
  tools=[csv_tool]
)

reporting_agent = Agent(
  config=agents_config['reporting_agent'],
  tools=[csv_tool]
)

chart_generation_agent = Agent(
  config=agents_config['chart_generation_agent'],
  allow_code_execution=True
)

# Creating Tasks
suggestion_generation = Task(
  config=tasks_config['suggestion_generation'],
  agent=suggestion_generation_agent
)

table_generation = Task(
  config=tasks_config['table_generation'],
  agent=reporting_agent
)

chart_generation = Task(
  config=tasks_config['chart_generation'],
  agent=chart_generation_agent
)

final_report_assembly = Task(
  config=tasks_config['final_report_assembly'],
  agent=reporting_agent,
  context=[suggestion_generation, table_generation, chart_generation]
)


# Creating Crew
support_report_crew = Crew(
  agents=[
    suggestion_generation_agent,
    reporting_agent,
    chart_generation_agent
  ],
  tasks=[
    suggestion_generation,
    table_generation,
    chart_generation,
    final_report_assembly
  ],
  verbose=True
)

result = support_report_crew.kickoff()


