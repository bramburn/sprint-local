### Purpose

You are an expert developer tasked with analyzing the structure of a coding project and creating a detailed plan of action to execute a specific coding task.

Create a detailed backlog for the following requirement in my project, including user stories, actions to undertake, references between files, list of files being created, acceptance criteria, testing plan, and any other relevant details.

The backlog should include the following elements:

1. **User Story**: Write a clear and concise user story that describes the desired functionality or feature, including the user's role, goal, and expected outcome.
2. **Actions to Undertake**: Break down the user story into specific, actionable tasks that need to be completed to deliver the desired functionality. These tasks should be described in detail, including any necessary steps, inputs, and outputs.
3. **References between Files**: Identify any relationships or dependencies between files that will be created as part of the project, including data flows, APIs, or other integrations.
4. **List of Files being Created**: Provide a comprehensive list of all files that will be created as part of the project, including code files, documentation files, and any other relevant artifacts.
5. **Acceptance Criteria**: Define clear and measurable acceptance criteria for each user story, including any specific requirements or constraints that must be met.
6. **Testing Plan**: Describe the testing approach and methodology that will be used to validate the acceptance criteria, including any test cases, test data, and testing tools.
7. **Assumptions and Dependencies**: Identify any assumptions or dependencies that are being made as part of the project, including any external dependencies or third-party libraries.
8. **Non-Functional Requirements**: Describe any non-functional requirements that are relevant to the project, including performance, security, or usability considerations.

The backlog should be written in a clear and concise manner, with proper formatting and headings to facilitate easy reading and understanding.

Please include the following sections in the backlog:

* **Introduction**
* **User Stories**
* **Actions to Undertake**
* **References between Files**
* **List of Files being Created**
* **Acceptance Criteria**
* **Testing Plan**
* **Assumptions and Dependencies**
* **Non-Functional Requirements**
* **Conclusion**

Use the following format for each user story:

* **User Story [Number]**: [ Brief description of the user story]
	+ **Description**: [Detailed description of the user story]
	+ **Actions to Undertake**: [List of specific tasks to complete]
	+ **References between Files**: [List of relationships or dependencies between files]
	+ **Acceptance Criteria**: [Clear and measurable criteria for acceptance]
	+ **Testing Plan**: [Description of the testing approach and methodology]

Use the following format for each file being created:

* **File [Number]**: [File name and description]
	+ **Purpose**: [ Brief description of the file's purpose]
	+ **Contents**: [Detailed description of the file's contents]
	+ **Relationships**: [List of relationships or dependencies with other files]

Use the following format for each test case:

* **Test Case [Number]**: [ Brief description of the test case]
	+ **Test Data**: [Description of the test data used]
	+ **Expected Result**: [Description of the expected result]
	+ **Testing Tool**: [Description of the testing tool used]

Please provide a comprehensive and detailed backlog that covers all aspects of the project, including user stories, actions to undertake, references between files, list of files being created, acceptance criteria, testing plan, assumptions and dependencies, and non-functional requirements.

**Output Format**: Please provide the backlog in a markdown format, with proper headings, subheadings, and formatting to facilitate easy reading and understanding.


[start of requirements]

### Instructions

- Analyze the directory structure of the project provided in the `directory-list`.
- Understand the task specified in the `task`.
- Based on the analysis of the project structure and the task, develop a comprehensive plan of action.
- The plan should include steps to navigate the project directories, any necessary file modifications, and how to integrate the task into the existing codebase.
- Ensure the plan is logical, detailed, and tailored to the project's structure and the task's requirements.

### Sections

#### Directory List
{directory_structure}

#### Task
{task}

### Examples

#### Example 1

**Directory List:**
```
project/
├── src/
│   ├── main.py
│   ├── utils/
│   │   ├── helper.py
│   │   └── config.py
│   └── models/
│       └── model.py
└── tests/
    ├── test_main.py
    └── test_utils/
        └── test_helper.py
```

**Task:**
Add a new function to `helper.py` that processes data from `config.py`.

**Plan of Action:**
1. Navigate to `project/src/utils/`.
2. Open `helper.py` and review the existing functions.
3. Open `config.py` to understand the data format.
4. Add a new function in `helper.py` that reads data from `config.py`.
5. Test the new function by running `test_helper.py` in `project/tests/test_utils/`.
6. If tests pass, commit changes and push to the repository.

#### Example 2

**Directory List:**
```
project/
├── src/
│   ├── app.py
│   ├── services/
│   │   ├── service1.py
│   │   └── service2.py
│   └── db/
│       └── database.py
└── docs/
    └── README.md
```

**Task:**
Implement a new service in `services/` to handle user authentication.

**Plan of Action:**
1. Navigate to `project/src/services/`.
2. Create a new file `auth_service.py`.
3. In `auth_service.py`, implement user authentication logic.
4. Modify `app.py` to integrate the new `auth_service.py`.
5. Update `database.py` to include any necessary schema changes for user authentication.
6. Document the new service in `project/docs/README.md`.
7. Test the new service and commit changes.

#### Example 3

**Directory List:**
```
project/
├── src/
│   ├── main.cpp
│   ├── include/
│   │   └── headers.h
│   └── lib/
│       └── library.cpp
└── bin/
    └── executable
```

**Task:**
Optimize the performance of `main.cpp` using functions from `library.cpp`.

**Plan of Action:**
1. Navigate to `project/src/`.
2. Open `main.cpp` and identify performance bottlenecks.
3. Open `library.cpp` and review available optimization functions.
4. Implement optimizations in `main.cpp` using functions from `library.cpp`.
5. Recompile and run the `executable` in `project/bin/` to test performance improvements.
6. Document changes and commit to the repository.

### User Prompt
produce a detailed plan of action to execute the following task: {task}

Your plan of action:
