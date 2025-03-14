from typing import Optional, Dict, List, Tuple
from .agent import BaseAgent
from deepcoder.utils import CodeParser
from deepcoder.interpreter import display_code,colors

INSTRUCTIONS = """
NOTICE
**Role**: You are a Development Engineer;
Task Overview:   
Steps to Follow:  
1. **Analyze the Feedback**: Carefully review the errors or issues outlined in the feedback.  
2. **Locate the Error**: Determine the specific location and nature of the error in your code.  
3. **Understand the Error**: Explain the reason why the error occurred, considering potential coding mistakes or logical flaws.  
4. **Propose Solutions**: Outline a strategy to correct the error.  
5. **Rewrite the Code**: Revise the code accordingly, ensuring all identified bugs are fixed and that the code functions correctly.  

Important Formatting:  
- Use `##` to separate sections, not `#`.  
- In the section titles that follow ##, only letters (a-z, A-Z) and spaces are allowed.
- Section titles using `##` should precede any test cases or scripts, and should be formatted with double quotes.  

NOTE : Use the above Chain-of-Thought approach to think and provide the answer using the following format at the end of the answer
If there are functions in the Test Cases that are redundantly declared in the Legacy Code, remove that portion In Test Case Part
## Code
```python  
[code]
```

## Test
```python  
[test cases]
```
"""

PROMPT_TEMPLATE = """
The message is as follows:
# Legacy Code
```python
{code}
```
---
# Unit Test Code
```python
{test_code}
```
---
# Console logs
```text
{logs}
```
 the code to rewrite: Write code with triple quote. Do your best to implement THIS IN ONLY ONE FILE.
---
Now you should start rewriting the code:
"""

answer = """
"""

class DebugAgent(BaseAgent):
    def __init__(self,functions: List[Dict] = None):
        # 生成包含需求提示的系统指令
        
        super().__init__(
            name="Debug Error",
            instructions=INSTRUCTIONS,
            # model = "deepseek-coder",
            functions=functions or []
        ) 
        self.code_parser = CodeParser()

    def run(self,code,test_code,output_detail) -> Tuple[str, str]:
        prompt = PROMPT_TEMPLATE.format(code= code, 
                                        test_code=test_code, 
                                        logs=output_detail )
        response = self.ask(prompt=prompt)
        code = self.code_parser.parse_code(block="Code",text = response,lang="python")
        print(f"---------------------{colors.YELLOW} Debug - ReWrited Code {colors.RESET}---------------------")
        display_code(code)
        test_cases = self.code_parser.parse_code(block="Test",text = response,lang="python")
        print(f"---------------------{colors.YELLOW} Debug - ReWrited Test Case {colors.RESET}---------------------")
        display_code(test_cases)
        return code,test_cases

