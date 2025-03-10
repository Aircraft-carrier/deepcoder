from .coder import CoderAgent
from .tester import TesterAgent
from .debug_error import DebugAgent
from .reviewer import ReviewerAgent
from deepcoder.utils import CodeParser
from deepcoder.interpreter import ExecuteNbCode,display_code,execute,colors
from deepcoder.log import logger
from typing import Tuple, Any


class Context():
    def __init__(self):
        self.code = ""
        self.test_code = ""
        self.output_detail = ""
        self.instruction = (
            "quicksort(arr: List[int]) -> List[int]:\n"
            '    """Sorts an array of integers using the quicksort algorithm.\n'
            "    >>> quicksort([3, 6, 8, 10, 1, 2, 1])\n"
            "    [1, 1, 2, 3, 6, 8, 10]\n"
            "    >>> quicksort([5, -1, 7, 3, 2])\n"
            "    [-1, 2, 3, 5, 7]\n"
            "    >>> quicksort([])\n"
            "    []\n"
            "    >>> quicksort([4])\n"
            "    [4]\n"
            '    """'
        )
    def update_instruction(self, new_instruction: str) -> None:  
        """  
        更新 instruction 属性  
        
        Args:  
            new_instruction (str): 新的指令文本  
        """  
        self.instruction = new_instruction  


class MultiAgent():
    def __init__(self):
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        self.debugger = DebugAgent()
        self.reviewer = ReviewerAgent()
        self.code_parser = CodeParser()
        self.execute_code = ExecuteNbCode()
        self.context = Context()

    async def write_and_exec_code(self, max_retry: int = 2) -> Tuple[str, Any, bool]:
        """生成并执行代码，带有自动调试重试机制"""
        counter = 0
        success = False
        final_code = ""
        execution_result = None
        

        while not success and counter < max_retry:
            current_code = self._generate_code(counter)
            logger.info(f"Execution Start (attempt {counter + 1}/{max_retry})")
            execution_result, success = await self.execute_code.run(current_code)
            
            if not success:
                logger.warning(f"Execution failed (attempt {counter + 1}/{max_retry})")

                self.context.output_detail = str(execution_result)
                counter += 1
            else:
                # logger.info(f"Code executed successfully! \n{current_code}")
                final_code = current_code

        if not success:
            logger.error(f"Failed after {max_retry} attempts. Final error: {execution_result}")
        return final_code, execution_result, success
    
    def write_and_exec_code_muti(self, max_retry: int = 3,lang: str = "python") -> Tuple[str, Any, bool]:
        """生成并执行代码，带有自动调试重试机制"""
        counter = 0
        success = False
        final_code = ""
        execution_result = None
        
        while not success and counter < max_retry:
            current_code = self._generate_code(counter)
            logger.info(f"Execution Start (attempt {counter + 1}/{max_retry})")
            execution_result, success = execute(current_code,lang)
            
            if not success:
                logger.warning(f"Execution failed (attempt {counter + 1}/{max_retry})")
                self.context.output_detail = str(execution_result)
                print(f"---------------------{colors.RED} Execution Result {colors.RESET}---------------------")
                display_code(self.context.output_detail)
                counter += 1
            else:
                logger.info("Code executed successfully!")
                final_code = current_code

        if not success:
            logger.error(f"Failed after {max_retry} attempts. Final error: {execution_result}")
        return self.context.code, execution_result, success

    def _generate_code(self, attempt: int) -> str:
        """生成代码逻辑，区分初次生成和调试生成"""
        if attempt == 0:
            self._initial_generation()
        elif attempt == 2:
            self._revised_prompt()
        else:
            self._debug_generation()  
        return self._combine_code()

    def _initial_generation(self):
        """初次生成代码和测试用例"""
        self.context.code = self.coder.run(self.context.instruction)
        logger.info("Initial code generated successfully")
        self.context.test_code = self.tester.run(self.context.instruction)
        logger.info("Initial test case generated successfully")

    def _debug_generation(self):
        """调试模式下的代码生成"""
        self.debugger.clear_history()  
        code,test_code = self.debugger.run(
            self.context.code,
            self.context.test_code,
            self.context.output_detail
        )
        if code:
            self.context.code
        if test_code:
            self.context.test_code
        logger.info("Debug-generated code updated")

    def _revised_prompt(self):
        prompt = self.reviewer.run(self.context.instruction,self.context.output_detail)
        if prompt and "def" in prompt:
            self.reviewer.clear_history()
            self.context.instruction = prompt
        logger.info("Instruction code updated")
        self.coder.remove_last_interaction()
        self.context.code = self.coder.run(self.context.instruction)
        logger.info("Initial code generated successfully")
        

    def _combine_code(self) -> str:
        """合并主代码和测试代码"""
        return f"{self.context.code}\n\n{self.context.test_code}"
    
    def get_answer(self,message: str,lang: str = "python")-> str:
        print(f"---------------------{colors.GREEN} User Question {colors.RESET}---------------------")
        display_code(message)
        self.context.instruction = message
        self.write_and_exec_code_muti(lang=lang)
        return self.context.code