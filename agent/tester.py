from typing import Optional, Dict, List, Tuple
from .agent import BaseAgent
from deepcoder.utils import CodeParser
from deepcoder.interpreter import display_code,colors

INSTRUCTIONS = """
**Role**: As a tester, your task is to create comprehensive test cases for the incomplete function. 

**Instructions**: 
1. Implement a comprehensive set of test cases following the guidelines above. 
2. Ensure each test case is well-documented with comments explaining the scenario it covers. 
3. Pay special attention to edge cases as they often reveal hidden bugs. 
4. For large-scale tests, focus on the function's efficiency and performance under heavy loads.
NOTE: Only generate the test code section, without creating the specific functions or providing a summary.

- The format of test cases should be:
```python
assert function_name(input) == expected_output, "Test Case Description"
```

"""

PROMPT_TEMPLATE = """
The message is as follows:
# Requirement

{requirement}

---
Now you should start writing test case for the code:
## Write TestCase with triple quote. Do your best to implement THIS IN ONLY ONE FILE.
Test Case : 
"""



class TesterAgent(BaseAgent):
    def __init__(self, functions: List[Dict] = None):
        
        super().__init__(
            name="Test Cases Generator",
            instructions=INSTRUCTIONS,
            model = "deepseek-coder",
            functions=functions or []
        )
        self.code_parser = CodeParser()     
 
    def run(self,requirement) -> str:
        prompt = PROMPT_TEMPLATE.format(requirement=requirement)
        response =  self.ask(prompt=prompt)
        # response =  answer
        test_code = self.code_parser.parse_code(block="",text = response,lang="python")
        self.update_context({"test_code":test_code})
        print(f"---------------------{colors.YELLOW} Test Cases {colors.RESET}---------------------")
        display_code(test_code)
        return test_code

