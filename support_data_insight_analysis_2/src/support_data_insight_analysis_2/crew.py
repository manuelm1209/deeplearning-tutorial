from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
import yaml
import os


from dotenv import load_dotenv

load_dotenv()

@CrewBase
class SupportDataInsightAnalysis2():
    """SupportDataInsightAnalysis2 crew"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        # Define file paths for YAML configurations
        self.files = {
            'agents': os.path.join(self.BASE_DIR, 'config', 'agents.yaml'),
            'tasks': os.path.join(self.BASE_DIR, 'config', 'tasks.yaml'),
        }

        # Load configurations from YAML files
        self.agents_config = self.load_yaml(self.files['agents'])
        self.tasks_config = self.load_yaml(self.files['tasks'])
        
        # Tools
        self.csv_tool = FileReadTool(file_path='./support_tickets_data.csv')

    def load_yaml(self, file_path):
        """Load YAML configuration from the specified file path."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading YAML file {file_path}: {e}")
            return {}

    @agent
    def suggestion_generation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['suggestion_generation_agent'],
            tools=[self.csv_tool],
            verbose=True
        )

    @agent
    def reporting_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_agent'],
            tools=[self.csv_tool],
            verbose=True
        )

    @agent
    def chart_generation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['chart_generation_agent'],
            allow_code_execution=True,
            verbose=True
        )

    # @task
    # def suggestion_generation(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['suggestion_generation'],
    #         agent=self.suggestion_generation_agent,
    #     )
    
    @task
    def suggestion_generation(self) -> Task:
		# Ensure that tasks_config['suggestion_generation'] is returning a valid configuration
        suggestion_config = self.tasks_config.get('suggestion_generation', {})

		# Print the suggestion configuration for debugging
        print("Suggestion Generation Config:", suggestion_config)

        return Task(
            config=suggestion_config,
            agent=self.suggestion_generation_agent,
        )



    @task
    def table_generation(self) -> Task:
        return Task(
            config=self.tasks_config['table_generation'],
            agent=self.chart_generation_agent
        )

    @task
    def chart_generation(self) -> Task:
        return Task(
            config=self.tasks_config['chart_generation'],
            agent=self.reporting_agent,
        )

    @task
    def final_report_assembly(self) -> Task:
        return Task(
            config=self.tasks_config['final_report_assembly'],
            agent=self.reporting_agent,
            context=[self.suggestion_generation, self.table_generation, self.chart_generation]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SupportDataInsightAnalysis2 crew"""
        return Crew(
            agents=[self.suggestion_generation_agent, self.reporting_agent, self.chart_generation_agent],  # Added explicit agents
            tasks=[self.suggestion_generation, self.table_generation, self.chart_generation, self.final_report_assembly],  # Added explicit tasks
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # Uncomment to use hierarchical processing
        )