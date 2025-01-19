import pytest
from backlog_generator import BacklogGenerator

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
    tasks = generator.generate_tasks({'feature': 'machine learning model'})
    
    assert len(tasks) == 3
    assert any('Research machine learning model' in task['task'] for task in tasks)
    assert any('Prototype machine learning model' in task['task'] for task in tasks)
    assert any('Validate machine learning model' in task['task'] for task in tasks)
