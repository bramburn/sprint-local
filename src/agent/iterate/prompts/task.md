### Purpose

You are an expert developer tasked with analyzing the structure of a coding project and creating a detailed plan of action to execute a specific coding task.

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
