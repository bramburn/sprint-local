from typing import Dict, Any, Optional
from langchain.schema import BaseLanguageModel
from ..base_node import BaseNode
from ...agents.subagents.static_error import StaticErrorSubagent

class StaticErrorNode(BaseNode):
    def __init__(
        self, 
        llm: BaseLanguageModel,
        static_error_agent: Optional[StaticErrorSubagent] = None
    ):
        """
        Initialize the Static Error Node for LangGraph workflow.
        
        Args:
            llm: Language model for error analysis
            static_error_agent: Optional custom static error agent
        """
        super().__init__(
            name="static_error",
            operation=self._fix_static_error
        )
        
        self.llm = llm
        self.static_error_agent = static_error_agent or StaticErrorSubagent(llm)
    
    async def _fix_static_error(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process static errors in the workflow.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated workflow state with static error results
        """
        if "static_errors" not in state or not state["static_errors"]:
            return state
        
        results = []
        for error in state["static_errors"]:
            try:
                # Analyze error
                analysis = await self.static_error_agent.analyze_error(error)
                
                # Generate fixes
                fixes = await self.static_error_agent.generate_fix(analysis)
                
                # Validate fixes
                valid_fixes = []
                for fix in fixes:
                    if await self.static_error_agent.validate_fix(analysis, fix):
                        valid_fixes.append(fix)
                
                results.append({
                    "analysis": analysis.dict(),
                    "fixes": valid_fixes
                })
            except Exception as e:
                # Log and handle any errors during processing
                results.append({
                    "error": str(e),
                    "original_error": error
                })
        
        state["static_error_results"] = results
        return state
