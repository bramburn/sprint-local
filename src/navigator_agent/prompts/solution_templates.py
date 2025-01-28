from langchain_core.prompts import PromptTemplate

# Strategy-specific prompt templates
strategy_prompt_templates = {
    'direct_problem_solving': PromptTemplate.from_template("""
    Direct Problem-Solving Strategy:
    Generate a solution that directly addresses the core challenges in the problem statement.
    
    Problem: {problem_statement}
    Key Challenges: {key_challenges}
    
    Instructions:
    1. Identify the most critical aspects of the problem.
    2. Propose a straightforward, pragmatic solution.
    3. Explain how the solution directly tackles the primary challenges.
    
    Solution Format:
    - Description: [Concise, direct solution approach]
    - Core Challenge Resolution: [How each key challenge is addressed]
    - Implementation Steps: [Practical, sequential steps]
    """),
    
    'constraint_optimization': PromptTemplate.from_template("""
    Constraint Optimization Strategy:
    Generate a solution that maximizes effectiveness within given constraints.
    
    Problem: {problem_statement}
    Constraints: {constraints}
    
    Instructions:
    1. Analyze the existing constraints carefully.
    2. Design a solution that operates optimally within these limitations.
    3. Highlight resource efficiency and impact maximization.
    
    Solution Format:
    - Description: [Solution that works within constraints]
    - Constraint Alignment: [How each constraint is respected]
    - Resource Optimization: [Efficiency gains and minimized overhead]
    """),
    
    'risk_mitigation': PromptTemplate.from_template("""
    Risk Mitigation Strategy:
    Generate a solution with comprehensive risk management.
    
    Problem: {problem_statement}
    Potential Risks: {risks}
    
    Instructions:
    1. Identify potential risks and failure points.
    2. Design a solution with built-in risk mitigation mechanisms.
    3. Provide contingency plans for each identified risk.
    
    Solution Format:
    - Description: [Robust, risk-aware solution]
    - Risk Identification: [Detailed risk assessment]
    - Mitigation Strategies: [Specific actions to prevent or minimize risks]
    - Contingency Plans: [Backup approaches if primary strategy fails]
    """),
    
    'innovative_approach': PromptTemplate.from_template("""
    Innovative Approach Strategy:
    Generate a groundbreaking solution that challenges conventional thinking.
    
    Problem: {problem_statement}
    Current Approaches: {potential_approaches}
    
    Instructions:
    1. Critically analyze existing problem-solving approaches.
    2. Propose a radically different, innovative solution.
    3. Explain the transformative potential of the approach.
    
    Solution Format:
    - Description: [Highly innovative solution concept]
    - Paradigm Shift: [How this approach differs from traditional methods]
    - Transformative Potential: [Long-term impact and breakthrough possibilities]
    - Proof of Concept: [Initial validation or experimental approach]
    """)
}

# Master solution generation prompt
solution_prompt_template = PromptTemplate.from_template("""
You are an expert problem solver and strategist. Your role is to generate multiple solution strategies for a given problem. Each solution should be detailed, actionable, and address potential risks.

Problem Statement: {problem_statement}

Reflection Insights:
1. Key challenges: {key_challenges}
2. Underlying assumptions: {assumptions}
3. Potential approaches: {potential_approaches}
4. Risks and mitigation strategies: {risks}

Constraints: {constraints}

Instructions:
Generate at least 3 distinct solution strategies using multiple approaches:
1. Direct Problem-Solving
2. Constraint Optimization
3. Risk Mitigation
4. Innovative Approach

For each solution, include:
1. A detailed description of the strategy
2. Estimated implementation complexity (Low/Medium/High)
3. Potential risks and mitigation strategies
4. Expected outcomes or benefits

Output Format:
Solution 1 (Strategy Type):
- Description: [Detailed solution description]
- Complexity: [Low/Medium/High]
- Risks: [Potential risks]
- Mitigation: [Risk mitigation strategies]
- Outcomes: [Expected benefits]

Solution 2 (Different Strategy Type):
...
""")
