import os
import yaml
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

## Importing Tools
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

## Creating Complete Sales Flow
from crewai import Flow
from crewai.flow.flow import listen, start

## Create Pydantic Models for Structured Output
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Set, Tuple

# For usage metrics and costs
import pandas as pd

import textwrap

import asyncio


load_dotenv()

llm = LLM(
    model="ollama/llama3.1",
    base_url="http://localhost:11434"
)

# Determine the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
## Loading Tasks and Agents YAML files
# Define file paths for YAML configurations
files = {
    'lead_agents': os.path.join(BASE_DIR, 'config','lead_qualification_agents.yaml'),
    'lead_tasks': os.path.join(BASE_DIR, 'config','lead_qualification_tasks.yaml'),
    'email_agents': os.path.join(BASE_DIR, 'config','email_engagement_agents.yaml'),
    'email_tasks': os.path.join(BASE_DIR, 'config','email_engagement_tasks.yaml')
}

# Load configurations from YAML files
configs = {}
for config_type, file_path in files.items():
    with open(file_path, 'r') as file:
        configs[config_type] = yaml.safe_load(file)

# Assign loaded configurations to specific variables
lead_agents_config = configs['lead_agents']
lead_tasks_config = configs['lead_tasks']
email_agents_config = configs['email_agents']
email_tasks_config = configs['email_tasks']


## Create Pydantic Models for Structured Output

class LeadPersonalInfo(BaseModel):
    name: str = Field(..., description="The full name of the lead.")
    job_title: str = Field(..., description="The job title of the lead.")
    role_relevance: int = Field(..., ge=0, le=10, description="A score representing how relevant the lead's role is to the decision-making process (0-10).")
    professional_background: Optional[str] = Field(..., description="A brief description of the lead's professional background.")

class CompanyInfo(BaseModel):
    company_name: str = Field(..., description="The name of the company the lead works for.")
    industry: str = Field(..., description="The industry in which the company operates.")
    company_size: int = Field(..., description="The size of the company in terms of employee count.")
    revenue: Optional[float] = Field(None, description="The annual revenue of the company, if available.")
    market_presence: int = Field(..., ge=0, le=10, description="A score representing the company's market presence (0-10).")

class LeadScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="The final score assigned to the lead (0-100).")
    scoring_criteria: List[str] = Field(..., description="The criteria used to determine the lead's score.")
    validation_notes: Optional[str] = Field(None, description="Any notes regarding the validation of the lead score.")

class LeadScoringResult(BaseModel):
    personal_info: LeadPersonalInfo = Field(..., description="Personal information about the lead.")
    company_info: CompanyInfo = Field(..., description="Information about the lead's company.")
    lead_score: LeadScore = Field(..., description="The calculated score and related information for the lead.")
    
    

## Lead Qualification Crew, Agents and Tasks
# Creating Agents
lead_data_agent = Agent(
  config=lead_agents_config['lead_data_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()]
)

cultural_fit_agent = Agent(
  config=lead_agents_config['cultural_fit_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()]
)

scoring_validation_agent = Agent(
  config=lead_agents_config['scoring_validation_agent'],
  tools=[SerperDevTool(), ScrapeWebsiteTool()]
)

# Creating Tasks
lead_data_task = Task(
  config=lead_tasks_config['lead_data_collection'],
  agent=lead_data_agent
)

cultural_fit_task = Task(
  config=lead_tasks_config['cultural_fit_analysis'],
  agent=cultural_fit_agent
)

scoring_validation_task = Task(
  config=lead_tasks_config['lead_scoring_and_validation'],
  agent=scoring_validation_agent,
  context=[lead_data_task, cultural_fit_task],
  output_pydantic=LeadScoringResult
)

# Creating Crew
lead_scoring_crew = Crew(
  agents=[
    lead_data_agent,
    cultural_fit_agent,
    scoring_validation_agent
  ],
  tasks=[
    lead_data_task,
    cultural_fit_task,
    scoring_validation_task
  ],
  verbose=True
)


## Email Engagement Crew
# Creating Agents
email_content_specialist = Agent(
  config=email_agents_config['email_content_specialist']
)

engagement_strategist = Agent(
  config=email_agents_config['engagement_strategist']
)

# Creating Tasks
email_drafting = Task(
  config=email_tasks_config['email_drafting'],
  agent=email_content_specialist
)

engagement_optimization = Task(
  config=email_tasks_config['engagement_optimization'],
  agent=engagement_strategist
)

# Creating Crew
email_writing_crew = Crew(
  agents=[
    email_content_specialist,
    engagement_strategist
  ],
  tasks=[
    email_drafting,
    engagement_optimization
  ],
  verbose=True
)


## Creating Complete Sales Flow

class SalesPipeline(Flow):
    @start()
    def fetch_leads(self):
        # Pull our leads from the database
        leads = [
            {
                "lead_data": {
                    "name": "João Moura",
                    "job_title": "Director of Engineering",
                    "company": "Clearbit",
                    "email": "joao@clearbit.com",
                    "use_case": "Using AI Agent to do better data enrichment."
                },
            },
        ]
        return leads

    @listen(fetch_leads)
    def score_leads(self, leads):
        # Kickoff the crew for each one of the "leads"
        scores = lead_scoring_crew.kickoff_for_each(leads)
        # Every flow has a state. We are saving all the scores inside the state.
        self.state["score_crews_results"] = scores
        return scores

    @listen(score_leads)
    def store_leads_score(self, scores):
        # Here we would store the scores in the database
        print("\n===STORING SCORES IN THE DATABASE===")
        return scores

    @listen(score_leads)
    def filter_leads(self, scores):
        return [score for score in scores if score['lead_score'].score > 70]

    @listen(filter_leads)
    def write_email(self, leads):
        scored_leads = [lead.to_dict() for lead in leads]
        emails = email_writing_crew.kickoff_for_each(scored_leads)
        return emails

    @listen(write_email)
    def send_email(self, emails):
        # Here we would send the emails to the leads
        print("\n===SENDING EMAILS===")
        self.state["emails_crews_results"] = emails
        return emails


flow = SalesPipeline()


## Plotting the Flow
flow.plot()


## Flow Kickoff
async def main():
    emails = await flow.kickoff_async()
    return emails
    
asyncio.run(main())

# print(flow.state["score_crews_results"])
# print("\n")
# print(flow.state["emails_crews_results"])


## Usage Metrics and Costs

# Convert UsageMetrics instance to a DataFrame
# The following line with .dict() was deprecarted - Replaced with .model_dump()
# df_usage_metrics = pd.DataFrame([flow.state["score_crews_results"][0].token_usage.dict()])
df_usage_metrics = pd.DataFrame([flow.state["score_crews_results"][0].token_usage.model_dump()])

# Calculate total costs
costs = 0.150 * df_usage_metrics['total_tokens'].sum() / 1_000_000
print(f"\nTotal costs: ${costs:.4f}")

# Display the DataFrame
print(df_usage_metrics)



# Convert UsageMetrics instance to a DataFrame
# Extract token usage from each CrewOutput in the results
email_results = flow.state["emails_crews_results"]

# Convert token usage to a DataFrame
df_usage_metrics = pd.DataFrame([result.token_usage.model_dump() for result in email_results])

# Calculate total costs
costs = 0.150 * df_usage_metrics['total_tokens'].sum() / 1_000_000
print(f"\nTotal costs: ${costs:.4f}")

# Display the DataFrame
print(df_usage_metrics)


## Inspecting Results
scores = flow.state["score_crews_results"]

print(f"\nFinal Score Answer: \n{scores[0].pydantic}\n")

lead_scoring_result = scores[0].pydantic

# Create a dictionary with the nested structure flattened
data = {
    'Name': lead_scoring_result.personal_info.name,
    'Job Title': lead_scoring_result.personal_info.job_title,
    'Role Relevance': lead_scoring_result.personal_info.role_relevance,
    'Professional Background': lead_scoring_result.personal_info.professional_background,
    'Company Name': lead_scoring_result.company_info.company_name,
    'Industry': lead_scoring_result.company_info.industry,
    'Company Size': lead_scoring_result.company_info.company_size,
    'Revenue': lead_scoring_result.company_info.revenue,
    'Market Presence': lead_scoring_result.company_info.market_presence,
    'Lead Score': lead_scoring_result.lead_score.score,
    'Scoring Criteria': ', '.join(lead_scoring_result.lead_score.scoring_criteria),
    'Validation Notes': lead_scoring_result.lead_score.validation_notes
}

# Convert the dictionary to a DataFrame
df = pd.DataFrame.from_dict(data, orient='index', columns=['Value'])
print("\ndf-1:")
print(df)

# Reset the index to turn the original column names into a regular column
df = df.reset_index()
print("\ndf-2:")
print(df)

# Rename the index column to 'Attribute'
df = df.rename(columns={'index': 'Attribute'})
print("\ndf-3:")
print(df)





## Results
result_text = flow.state["emails_crews_results"][0].raw
wrapped_text = textwrap.fill(result_text, width=80)
print(f"\n{wrapped_text}")

print(f"\n{flow.state['emails_crews_results'][0]}")

print(f"\n{flow.state['score_crews_results']}")
