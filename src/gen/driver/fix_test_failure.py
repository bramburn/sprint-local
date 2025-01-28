from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from src.navigator_agent.config.test_failure_config import test_failure_config
from src.monitoring.metrics import TestFailureMetrics
from src.security.execution_sandbox import SafeExecutionEnvironment, ExecutionResult

class ErrorType(Enum):
    SYNTAX_ERROR = auto()
    RUNTIME_ERROR = auto()
    LOGIC_ERROR = auto()
    TIMEOUT_ERROR = auto()

@dataclass
class TestFailureContext:
    """Context for a test failure, tracking recovery attempts."""
    original_code: str
    error_type: ErrorType
    error_message: str
    attempts: int = 0
    solution_history: list = field(default_factory=list)
    
    def add_solution(self, solution: str):
        """Add a potential solution to history."""
        self.solution_history.append(solution)
        self.attempts += 1

class ProblemState(BaseModel):
    """
    State model for tracking problem-solving process during test failure correction.
    """
    code_recent_solution: str = Field(default="")
    error_trace: str = Field(default="")
    error_class: str = Field(default="")
    solution_history: list = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0, le=5)
    test_failure_context: TestFailureContext = Field(default_factory=TestFailureContext)
    
    class Config:
        arbitrary_types_allowed = True

class TestFailureCorrector:
    def __init__(self, chat_model):
        """
        Initialize the test failure correction workflow.
        
        :param chat_model: LLM for generating code fixes
        """
        self.chat_model = chat_model
        self.graph = self._build_graph()
        self.test_failure_handler = TestFailureHandler()
    
    def _build_graph(self):
        """
        Construct the LangGraph workflow for test failure correction.
        """
        builder = StateGraph(ProblemState)
        
        # Define nodes
        builder.add_node("detect_failure", self._classify_error)
        builder.add_node("analyze_trace", self._analyze_error_trace)
        builder.add_node("generate_fix", self._generate_code_fix)
        builder.add_node("validate_fix", self._validate_solution)
        builder.add_node("handle_test_failure", self._handle_test_failure)
        
        # Set entry point
        builder.set_entry_point("detect_failure")
        
        # Define edges
        builder.add_edge("detect_failure", "analyze_trace")
        builder.add_edge("analyze_trace", "generate_fix")
        builder.add_edge("generate_fix", "validate_fix")
        builder.add_edge("validate_fix", "handle_test_failure")
        
        # Conditional edges for retry mechanism
        builder.add_conditional_edges(
            "generate_fix", 
            self._should_retry,
            {
                "CONTINUE": "validate_fix", 
                "RETRY": "analyze_trace",
                "END": END
            }
        )
        
        # Final validation edge
        builder.add_edge("handle_test_failure", END)
        
        return builder.compile()
    
    def _classify_error(self, state: ProblemState) -> ProblemState:
        """
        Classify the type of error based on the error trace.
        """
        error_classifiers = {
            "RUNTIME_ERROR": lambda trace: "RuntimeError" in trace,
            "LOGIC_ERROR": lambda trace: "AssertionError" in trace,
            "TIMEOUT": lambda trace: "timed out" in trace,
        }
        
        for error_type, classifier in error_classifiers.items():
            if classifier(state.error_trace):
                state.error_class = error_type
                break
        
        return state
    
    def _analyze_error_trace(self, state: ProblemState) -> ProblemState:
        """
        Analyze the error trace to provide context for fix generation.
        """
        # Placeholder for more sophisticated error trace analysis
        # Could integrate with static analysis tools or LLM-based trace interpretation
        return state
    
    def _generate_code_fix(self, state: ProblemState) -> ProblemState:
        """
        Generate a code fix based on the error analysis.
        """
        messages = [
            SystemMessage(content=f"""
            You are a Python Code Repair Specialist. 
            Analyze and fix {state.error_class} in the following code.
            
            Guidelines:
            1. Preserve original function signature
            2. Only modify necessary sections
            3. Explicitly handle identified error case
            """),
            HumanMessage(content=f"""
            Current Code:
            ```python
            {state.code_recent_solution}
            ```
            
            Error Trace:
            {state.error_trace}
            
            Error Classification: {state.error_class}
            
            Generate a minimal, targeted fix that resolves the specific error.
            """)
        ]
        
        response = self.chat_model.invoke(messages)
        
        # Extract code from response (assuming code is in markdown code block)
        import re
        code_match = re.search(r'```python\n(.*?)```', response.content, re.DOTALL)
        if code_match:
            state.code_recent_solution = code_match.group(1)
        
        state.solution_history.append(state.code_recent_solution)
        state.retry_count += 1
        
        return state
    
    def _validate_solution(self, state: ProblemState) -> ProblemState:
        """
        Validate if the generated solution resolves the original error.
        
        In a real implementation, this would involve running tests or 
        performing static analysis.
        """
        # Placeholder for solution validation
        return state
    
    def _handle_test_failure(self, state: ProblemState) -> ProblemState:
        """
        Handle test failure using the TestFailureHandler.
        """
        recovered_code = self.test_failure_handler.handle_test_failure(state.code_recent_solution, {"error": state.error_trace})
        
        if recovered_code:
            state.code_recent_solution = recovered_code
        
        return state
    
    def _should_retry(self, state: ProblemState) -> str:
        """
        Determine whether to continue fixing, retry, or end the process.
        """
        if state.retry_count >= 3:
            return "END"
        
        # Add more sophisticated retry logic based on error type and previous attempts
        return "CONTINUE"
    
    async def run(self, problem_state: ProblemState):
        """
        Execute the test failure correction workflow.
        
        :param problem_state: Initial problem state
        :return: Final problem state after workflow execution
        """
        return await self.graph.arun(problem_state)

class TestFailureHandler:
    """Manages test failure detection, analysis, and recovery."""
    
    def __init__(
        self, 
        config=test_failure_config,
        metrics=TestFailureMetrics
    ):
        self.config = config
        self.metrics = metrics
        self.sandbox = SafeExecutionEnvironment()
    
    async def handle_test_failure(
        self, 
        code: str, 
        test_results: Dict[str, Any]
    ) -> Optional[str]:
        """
        Primary method to handle test failures.
        
        Args:
            code (str): Original code with failure
            test_results (dict): Test execution results
        
        Returns:
            Optional recovered/fixed code
        """
        # Classify error
        error_type = self._classify_error(test_results)
        
        # Create failure context
        context = TestFailureContext(
            original_code=code,
            error_type=error_type,
            error_message=test_results.get('error', '')
        )
        
        # Start metrics tracking
        self.metrics.record_recovery_attempt(error_type.name)
        start_time = time.time()
        
        # Attempt recovery
        try:
            recovered_code = await self._recover_code(context)
            
            # Record success metrics
            recovery_time = time.time() - start_time
            self.metrics.record_recovery_time(recovery_time)
            
            return recovered_code
        
        except Exception as e:
            # Log failure
            self.metrics.update_success_rate(0)
            return None
    
    def _classify_error(self, test_results: Dict[str, Any]) -> ErrorType:
        """
        Classify the type of error based on test results.
        
        Args:
            test_results (dict): Detailed test execution results
        
        Returns:
            ErrorType classification
        """
        error_message = test_results.get('error', '').lower()
        
        if 'syntax error' in error_message:
            return ErrorType.SYNTAX_ERROR
        elif 'timeout' in error_message:
            return ErrorType.TIMEOUT_ERROR
        elif 'runtime error' in error_message:
            return ErrorType.RUNTIME_ERROR
        else:
            return ErrorType.LOGIC_ERROR
    
    async def _recover_code(self, context: TestFailureContext) -> Optional[str]:
        """
        Attempt to recover code based on error type.
        
        Args:
            context (TestFailureContext): Failure context
        
        Returns:
            Optional recovered code
        """
        # Limit retry attempts
        if context.attempts >= self.config.max_retry_attempts:
            return None
        
        # Strategy selection based on error type
        recovery_strategies = {
            ErrorType.SYNTAX_ERROR: self._fix_syntax_error,
            ErrorType.RUNTIME_ERROR: self._fix_runtime_error,
            ErrorType.LOGIC_ERROR: self._fix_logic_error,
            ErrorType.TIMEOUT_ERROR: self._fix_timeout_error
        }
        
        strategy = recovery_strategies.get(context.error_type, self._generic_recovery)
        
        # Apply recovery strategy
        recovered_code = await strategy(context)
        
        if recovered_code:
            context.add_solution(recovered_code)
            
            # Validate recovered code
            validation_result = await self.sandbox.execute_safely(recovered_code)
            
            return recovered_code if validation_result.success else None
        
        return None
    
    async def _fix_syntax_error(self, context: TestFailureContext) -> Optional[str]:
        """Fix syntax errors."""
        # Placeholder for syntax error correction logic
        return None
    
    async def _fix_runtime_error(self, context: TestFailureContext) -> Optional[str]:
        """Fix runtime errors."""
        # Placeholder for runtime error correction logic
        return None
    
    async def _fix_logic_error(self, context: TestFailureContext) -> Optional[str]:
        """Fix logic errors."""
        # Placeholder for logic error correction logic
        return None
    
    async def _fix_timeout_error(self, context: TestFailureContext) -> Optional[str]:
        """Fix timeout errors."""
        # Placeholder for timeout error correction logic
        return None
    
    async def _generic_recovery(self, context: TestFailureContext) -> Optional[str]:
        """Generic fallback recovery strategy."""
        # Placeholder for generic recovery logic
        return None
