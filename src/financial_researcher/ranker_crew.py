from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class StockRankerCrew():
    """Stock ranking and investment analysis crew for Indian equities"""

    agents_config = 'config/ranker_agents.yaml'
    tasks_config = 'config/ranker_tasks.yaml'

    @agent
    def fundamental_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['fundamental_analyst'],
            verbose=True,
        )

    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_analyst'],
            verbose=True,
        )

    @agent
    def portfolio_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['portfolio_advisor'],
            verbose=True,
        )

    @task
    def fundamental_scoring_task(self) -> Task:
        return Task(
            config=self.tasks_config['fundamental_scoring_task'],
        )

    @task
    def risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config['risk_assessment_task'],
        )

    @task
    def ranking_and_recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['ranking_and_recommendation_task'],
            output_file='output/STOCK_RANKING_REPORT.md',
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
