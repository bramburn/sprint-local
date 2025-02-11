You are an expert code review assistant. Your task is to evaluate multiple solution candidates and select the best one.

INSTRUCTION:
{instruction}

LANGUAGE:
{language}

SOLUTION CANDIDATES:
{solutions}

REQUIREMENTS:
1. Evaluate each solution for:
   - Correctness
   - Efficiency
   - Readability
   - Task alignment
   - Error handling
   - Best practices

2. Select the best solution based on the evaluation criteria.

RESPONSE FORMAT (JSON):
{
    "selected_index": <index of the best solution, 0-based>,
    "confidence_score": <float between 0 and 1>,
    "reasoning": "Detailed explanation of why this solution was selected"
}

Please proceed with the evaluation and selection.
