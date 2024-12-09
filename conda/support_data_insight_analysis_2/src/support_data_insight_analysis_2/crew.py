from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool

import os
import yaml

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class SupportDataInsightAnalysis2():
	"""SupportDataInsightAnalysis2 crew"""

	# Learn more about YAML configuration files here:
	# Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
	# Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
 
 	#TODO Try different tool options
	# csv_tool = FileReadTool(file_path='./support_tickets_data.csv')
	# @agent
	# def suggestion_generation_agent(self,csv_tool) -> Agent:
	# 	return Agent(
	# 		config=self.agents_config['suggestion_generation_agent'],
   	# 		tools= [csv_tool],
	# 		verbose=True
	# 	)
	
	@agent
	def suggestion_generation_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['suggestion_generation_agent'],
   			tools= [FileReadTool(file_path='./support_tickets_data.csv')],
			verbose=True
		)

	@agent
	def reporting_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['reporting_agent'],
			tools= [FileReadTool(file_path='./support_tickets_data.csv')],
			verbose=True
		)
  

	# To learn more about structured task outputs, 
	# task dependencies, and task callbacks, check out the documentation:
	# https://docs.crewai.com/concepts/tasks#overview-of-a-task
	@task
	def suggestion_generation(self) -> Task:
		return Task(
			config=self.tasks_config['suggestion_generation'],
		)

	@task
	def table_generation(self) -> Task:
		return Task(
			config=self.tasks_config['table_generation'],
			# output_file='report.md'
		)

  
	@task
	def final_report_assembly(self) -> Task:
		return Task(
			config=self.tasks_config['final_report_assembly'],
     		# context=[suggestion_generation, table_generation, chart_generation]

		)

	@crew
	def crew(self) -> Crew:
		"""Creates the SupportDataInsightAnalysis2 crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
