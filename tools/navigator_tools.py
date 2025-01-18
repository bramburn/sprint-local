from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from llm_wrapper import LLMWrapper
from langchain.prompts import ChatPromptTemplate

@dataclass
class RefinedProblem:
    original_description: str
    refined_description: str
    clarifications: List[str]
    requirements: List[str]

@dataclass
class RiskAssessment:
    risk_name: str
    severity: str  # "Low", "Medium", "High"
    probability: str  # "Low", "Medium", "High"
    impact: str
    mitigation_strategy: str

@dataclass
class PlanEvaluation:
    plan_id: str
    score: float
    strengths: List[str]
    weaknesses: List[str]
    reasoning: str

@dataclass
class ArchitectureDecision:
    decision: str
    context: str
    consequences: List[str]
    alternatives: List[str]
    rationale: str

@dataclass
class TechnicalConstraint:
    constraint_type: str  # "Performance", "Security", "Scalability", etc.
    description: str
    impact: str
    mitigation_options: List[str]

class NavigatorTools:
    def __init__(self, llm: LLMWrapper):
        self.llm = llm
        self._init_prompts()

    def _init_prompts(self):
        """Initialize ChatPromptTemplates for all tools."""
        self.refine_problem_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at analyzing and refining problem descriptions."},
            {"role": "user", "content": """Given this problem description: "{problem_description}"
            
            1. Analyze the description for missing details or ambiguities
            2. Generate clarifying questions if needed
            3. Provide a refined, detailed description
            4. List specific requirements
            
            Format your response as JSON with these fields:
            - refined_description: string
            - clarifications: list of strings
            - requirements: list of strings"""}
        ])

        self.analyze_risks_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at identifying and analyzing project risks."},
            {"role": "user", "content": """Analyze this solution plan for potential risks: "{solution_plan}"
            
            Consider these risk categories:
            1. Technical risks
            2. Scalability risks
            3. Security risks
            4. Operational risks
            5. Integration risks
            
            For each identified risk, provide:
            - Risk name
            - Severity (Low/Medium/High)
            - Probability (Low/Medium/High)
            - Impact description
            - Mitigation strategy
            
            Format your response as a JSON list of risk objects."""}
        ])

        self.compare_plans_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at evaluating and comparing solution plans."},
            {"role": "user", "content": """Compare and rank these solution plans:

{plans_text}

Evaluate each plan based on:
1. Feasibility
2. Scalability
3. Maintainability
4. Cost-effectiveness
5. Time to implement

For each plan provide:
- Numerical score (0-10)
- List of strengths
- List of weaknesses
- Reasoning for the score

Format your response as a JSON list of plan evaluation objects."""}
        ])

        self.identify_constraints_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert at identifying technical constraints and limitations."},
            {"role": "user", "content": """Analyze this problem description and identify technical constraints:

{problem_description}

Consider these constraint categories:
1. Performance requirements
2. Security requirements
3. Scalability needs
4. Resource limitations
5. Technical dependencies

For each constraint provide:
- Constraint type
- Description
- Impact on the solution
- Possible mitigation options

Format your response as a JSON list of constraint objects."""}
        ])

        self.architecture_decision_prompt = ChatPromptTemplate.from_messages([
            {"role": "system", "content": "You are an expert software architect."},
            {"role": "user", "content": """Make an architecture decision for this problem:

Problem: {problem_description}

Technical Constraints:
{constraints_text}

Consider:
1. Different architectural patterns
2. Trade-offs between alternatives
3. How well each option addresses constraints
4. Long-term maintainability and evolution

Provide:
- A clear architecture decision
- Context that influenced the decision
- Consequences (both positive and negative)
- Alternative options considered
- Detailed rationale

Format your response as a JSON object."""}
        ])

    async def refine_problem(self, problem_description: str) -> RefinedProblem:
        """Refines a vague or incomplete problem description into a detailed, actionable format."""
        prompt = self.refine_problem_prompt.format(problem_description=problem_description)
        response = await self.llm.aask(prompt)
        try:
            parsed = self.llm.parse_json(response)
            return RefinedProblem(
                original_description=problem_description,
                refined_description=parsed["refined_description"],
                clarifications=parsed["clarifications"],
                requirements=parsed["requirements"]
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def analyze_risks(self, solution_plan: str) -> List[RiskAssessment]:
        """Analyzes potential risks in a solution plan and provides mitigation strategies."""
        prompt = self.analyze_risks_prompt.format(solution_plan=solution_plan)
        response = await self.llm.aask(prompt)
        try:
            risks = self.llm.parse_json(response)
            return [
                RiskAssessment(
                    risk_name=risk["risk_name"],
                    severity=risk["severity"],
                    probability=risk["probability"],
                    impact=risk["impact"],
                    mitigation_strategy=risk["mitigation_strategy"]
                )
                for risk in risks
            ]
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def compare_plans(self, plans: List[Dict[str, str]]) -> List[PlanEvaluation]:
        """Compares multiple solution plans and ranks them based on various criteria."""
        plans_text = "\n".join(f"Plan {p['plan_id']}: {p['plan_description']}" for p in plans)
        prompt = self.compare_plans_prompt.format(plans_text=plans_text)
        response = await self.llm.aask(prompt)
        try:
            evaluations = self.llm.parse_json(response)
            return [
                PlanEvaluation(
                    plan_id=eval["plan_id"],
                    score=float(eval["score"]),
                    strengths=eval["strengths"],
                    weaknesses=eval["weaknesses"],
                    reasoning=eval["reasoning"]
                )
                for eval in evaluations
            ]
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def identify_constraints(self, problem_description: str) -> List[TechnicalConstraint]:
        """Identifies technical constraints and limitations for a given problem."""
        prompt = self.identify_constraints_prompt.format(problem_description=problem_description)
        response = await self.llm.aask(prompt)
        try:
            constraints = self.llm.parse_json(response)
            return [
                TechnicalConstraint(
                    constraint_type=constraint["constraint_type"],
                    description=constraint["description"],
                    impact=constraint["impact"],
                    mitigation_options=constraint["mitigation_options"]
                )
                for constraint in constraints
            ]
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def make_architecture_decision(
        self, 
        problem_description: str,
        constraints: List[TechnicalConstraint]
    ) -> ArchitectureDecision:
        """Makes and justifies high-level architecture decisions."""
        constraints_text = "\n".join(
            f"- {c.constraint_type}: {c.description} (Impact: {c.impact})"
            for c in constraints
        )
        prompt = self.architecture_decision_prompt.format(
            problem_description=problem_description,
            constraints_text=constraints_text
        )
        response = await self.llm.aask(prompt)
        try:
            decision = self.llm.parse_json(response)
            return ArchitectureDecision(
                decision=decision["decision"],
                context=decision["context"],
                consequences=decision["consequences"],
                alternatives=decision["alternatives"],
                rationale=decision["rationale"]
            )
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def validate_solution_completeness(
        self, 
        problem_description: str,
        solution_plan: str,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """
        Validates whether a solution plan completely addresses all requirements.
        
        Args:
            problem_description: Original problem description
            solution_plan: Proposed solution plan
            requirements: List of requirements to validate against
            
        Returns:
            Dict containing validation results and any gaps identified
        """
        prompt = f"""Validate this solution plan against requirements:

Problem: {problem_description}

Solution Plan:
{solution_plan}

Requirements to validate:
{chr(10).join(f"- {req}" for req in requirements)}

Analyze:
1. Coverage of each requirement
2. Any missing aspects
3. Potential implementation gaps
4. Edge cases not addressed

Format your response as a JSON object with:
- covered_requirements: list of strings
- missing_aspects: list of strings
- implementation_gaps: list of strings
- unhandled_edge_cases: list of strings
- completeness_score: float (0-1)
- recommendations: list of strings
"""
        
        response = await self.llm.aask(prompt)
        try:
            return self.llm.parse_json(response)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    async def estimate_implementation_effort(
        self,
        solution_plan: str,
        team_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimates the implementation effort required for a solution plan.
        
        Args:
            solution_plan: The solution plan to estimate
            team_context: Optional context about the team's capabilities
            
        Returns:
            Dict containing effort estimates and breakdown
        """
        team_context_str = ""
        if team_context:
            team_context_str = "\n".join(f"{k}: {v}" for k, v in team_context.items())
            team_context_str = f"\nTeam Context:\n{team_context_str}"
        
        prompt = f"""Estimate implementation effort for this solution plan:

{solution_plan}{team_context_str}

Provide estimates for:
1. Overall complexity (Low/Medium/High)
2. Time estimation (in person-days)
3. Required skills and expertise
4. Risk factors affecting the timeline
5. Major implementation phases

Break down the effort into:
- Design phase
- Implementation phase
- Testing phase
- Deployment phase
- Buffer for unknowns

Format your response as a JSON object with detailed breakdowns.
"""
        
        response = await self.llm.aask(prompt)
        try:
            return self.llm.parse_json(response)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}") 