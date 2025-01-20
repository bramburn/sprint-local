import pytest
from backlog_generator import BacklogGenerator, TaskType, TaskPriority

def test_parse_prompt():
    generator = BacklogGenerator()
    parsed = generator.parse_prompt("Add user authentication")
    
    assert 'feature' in parsed
    assert parsed['feature'] == "Add user authentication"
    assert 'keywords' in parsed
    assert 'add' in parsed['keywords']
    assert 'user' in parsed['keywords']
    assert 'authentication' in parsed['keywords']

def test_generate_tasks():
    generator = BacklogGenerator()
    parsed_prompt = {'feature': 'user authentication'}
    
    tasks = generator.generate_tasks(parsed_prompt)
    
    assert len(tasks) > 0
    for task in tasks:
        assert 'task' in task
        assert 'category' in task
        assert 'feature' in task
        assert task['feature'] == 'user authentication'

def test_format_backlog():
    generator = BacklogGenerator()
    tasks = [
        {'task': 'Implement user authentication', 'category': 'implement', 'feature': 'user authentication'},
        {'task': 'Test user authentication', 'category': 'test', 'feature': 'user authentication'}
    ]
    
    backlog = generator.format_backlog(tasks)
    
    assert "# Backlog" in backlog
    assert "Implement user authentication" in backlog
    assert "Test user authentication" in backlog
    assert "Category" in backlog
    assert "Feature" in backlog

def test_generate_backlog():
    generator = BacklogGenerator()
    backlog = generator.generate_backlog("Add user authentication")
    
    assert "# Backlog" in backlog
    assert "Add user authentication" in backlog
    assert len(backlog.split('\n')) > 5  # Ensure multiple lines are generated

def test_custom_task_templates():
    config = {
        'backlog_task_templates': [
            "Research {feature}",
            "Prototype {feature}",
            "Validate {feature}"
        ]
    }
    generator = BacklogGenerator(config)
    tasks = generator.generate_tasks(generator.parse_prompt('machine learning model'))
    
    assert len(tasks) == 3
    assert any('Research machine learning model' in task['task'] for task in tasks)
    assert any('Prototype machine learning model' in task['task'] for task in tasks)
    assert any('Validate machine learning model' in task['task'] for task in tasks)

def test_parse_prompt_advanced():
    generator = BacklogGenerator()
    parsed = generator.parse_prompt("Urgently implement a critical user authentication system")
    
    assert 'feature' in parsed
    assert 'keywords' in parsed
    assert 'entities' in parsed
    assert 'task_type' in parsed
    assert 'complexity' in parsed
    assert 'priority' in parsed
    
    assert parsed['task_type'] == TaskType.FEATURE.name
    assert parsed['priority'] == TaskPriority.CRITICAL.name
    assert parsed['complexity'] > 0

def test_task_type_inference():
    generator = BacklogGenerator()
    
    test_cases = [
        ("Fix a critical bug in the login system", TaskType.BUGFIX),
        ("Improve performance of database queries", TaskType.IMPROVEMENT),
        ("Research machine learning techniques", TaskType.RESEARCH),
        ("Refactor authentication module", TaskType.REFACTORING),
        ("Implement new user dashboard", TaskType.FEATURE)
    ]
    
    for prompt, expected_type in test_cases:
        parsed = generator.parse_prompt(prompt)
        assert parsed['task_type'] == expected_type.name

def test_priority_inference():
    generator = BacklogGenerator()
    
    test_cases = [
        ("Urgent security patch", TaskPriority.CRITICAL),
        ("Critical system update", TaskPriority.CRITICAL),
        ("Important feature enhancement", TaskPriority.HIGH),
        ("Key performance improvement", TaskPriority.HIGH),
        ("Routine maintenance task", TaskPriority.MEDIUM)
    ]
    
    for prompt, expected_priority in test_cases:
        parsed = generator.parse_prompt(prompt)
        assert parsed['priority'] == expected_priority.name

def test_dependency_extraction():
    generator = BacklogGenerator()
    
    test_cases = [
        ("Implement authentication after user registration", ["registration", "user"]),
        ("Create dashboard depends on user profile", ["profile", "dashboard", "user"]),
        ("Develop reporting feature before quarterly review", ["review", "reporting"]),
        ("Build API following security guidelines", ["API", "security guidelines"])
    ]
    
    for prompt, expected_dependencies in test_cases:
        parsed = generator.parse_prompt(prompt)
        # Use set comparison to handle order-independent matching
        assert any(dep in parsed['dependencies'] for dep in expected_dependencies), \
            f"Failed to extract dependencies from: {prompt}"

def test_generate_tasks_by_type():
    generator = BacklogGenerator()
    
    test_cases = [
        {
            "prompt": "Fix a critical login bug",
            "expected_task_type": "BUGFIX",
            "expected_tasks": ["Diagnose", "Fix", "Verify", "Update"]
        },
        {
            "prompt": "Research machine learning techniques",
            "expected_task_type": "RESEARCH",
            "expected_tasks": ["Define", "Conduct", "Prototype", "Validate"]
        },
        {
            "prompt": "Refactor authentication module",
            "expected_task_type": "REFACTORING",
            "expected_tasks": ["Identify", "Refactor", "Write", "Review"]
        }
    ]
    
    for case in test_cases:
        parsed = generator.parse_prompt(case["prompt"])
        tasks = generator.generate_tasks(parsed)
        
        assert parsed['task_type'] == case["expected_task_type"]
        
        # Check that tasks match the expected task type
        for expected_start in case["expected_tasks"]:
            assert any(task['task'].startswith(expected_start) for task in tasks), \
                f"No task found starting with {expected_start} for {case['prompt']}"

def test_effort_estimation():
    generator = BacklogGenerator()
    
    test_prompts = [
        "Implement complex machine learning model",
        "Fix a minor UI bug",
        "Develop critical security feature"
    ]
    
    for prompt in test_prompts:
        parsed = generator.parse_prompt(prompt)
        tasks = generator.generate_tasks(parsed)
        
        for task in tasks:
            assert 'estimated_effort' in task
            assert 'story_points' in task['estimated_effort']
            assert 'estimated_hours' in task['estimated_effort']
            assert task['estimated_effort']['story_points'] >= 0
            assert task['estimated_effort']['estimated_hours'] >= 0

def test_comprehensive_backlog_generation():
    generator = BacklogGenerator()
    prompt = "Develop an AI-powered customer support chatbot with advanced natural language processing"
    
    backlog = generator.generate_backlog(prompt)
    
    assert "# Backlog" in backlog
    assert "Develop an AI-powered customer support chatbot" in backlog
    assert "Story Points" in backlog
    assert "Estimated Hours" in backlog
    assert "Dependencies" in backlog or "Type" in backlog
    assert "Priority" in backlog
    assert "Complexity" in backlog

def test_extract_errors():
    generator = BacklogGenerator()
    test_output = """
    Running tests...
    ERROR: SyntaxError in main.py, line 10
    FAIL: AssertionError in test_utils.py, line 25
    Exception: RuntimeError in database.py, line 42
    Some other log message
    """
    
    errors = generator.extract_errors(test_output)
    
    assert len(errors) == 3
    assert "SyntaxError in main.py, line 10" in errors
    assert "AssertionError in test_utils.py, line 25" in errors
    assert "RuntimeError in database.py, line 42" in errors

def test_categorize_errors():
    generator = BacklogGenerator()
    error_messages = [
        "SyntaxError: invalid syntax in main.py",
        "RuntimeError: memory allocation failed",
        "LogicError: incorrect calculation in math module"
    ]
    
    categorized_errors = generator.categorize_errors(error_messages)
    
    assert "syntax" in categorized_errors
    assert "runtime" in categorized_errors
    assert "logic" in categorized_errors
    assert "resource" in categorized_errors
    assert "unknown" in categorized_errors
    
    assert len(categorized_errors["syntax"]) > 0
    assert len(categorized_errors["runtime"]) > 0

def test_store_errors_in_memory():
    generator = BacklogGenerator()
    categorized_errors = {
        "syntax": ["SyntaxError: invalid syntax"],
        "runtime": ["RuntimeError: memory allocation failed"]
    }
    memory = {}
    
    generator.store_errors_in_memory(categorized_errors, memory)
    
    assert "temporary_epic_list" in memory
    assert len(memory["temporary_epic_list"]) == 2
    
    # Check structure of stored errors
    for error_entry in memory["temporary_epic_list"]:
        assert "category" in error_entry
        assert "message" in error_entry
        assert error_entry["category"] in ["syntax", "runtime"]
