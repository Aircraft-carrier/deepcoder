from typing import Optional, Dict, List, Tuple
from .agent import BaseAgent
from deepcoder.utils import CodeParser
from deepcoder.interpreter import display_code,colors

INSTRUCTIONS = """
**Role**: You are a software programmer.

**Task**: As a programmer, you are required to complete the function. Use a Chain-of-Thought approach to break down the problem, create pseudocode, and then write the code in Python language.

**Instructions**: 
1. **Understand and Clarify**: Make sure you understand the task. 
2. **Algorithm/Method Selection**: Decide on the most efficient way. 
3. **Pseudocode Creation**: Write down the steps you will follow in pseudocode. 
4. **Code Generation**: Translate your pseudocode into executable Python code.
NOTE: Generate usable code by this Chain-of-Thought approach without summarizing or providing test cases.

**Code Formatting**: Please write code in 
```python
[Code]
``` 
format.

"""

PROMPT_TEMPLATE = """
The message is as follows:
# Requirement

{requirement}

---
Now you should start writing the code:
## Write code with triple quote. Do your best to implement THIS IN ONLY ONE FILE.
"""

answer = """
### Code Generation
```python
from typing import List

def sort_numbers(numbers: str) -> str:
    # Mapping of number words to their numerical values
    number_mapping = {
        'zero': 0,
        'one': 1,
        'two': 2,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9
    }
    
    # Split the input string into a list of number words
    number_words = numbers.split()
    
    # Sort the number words based on their numerical values
    sorted_words = sorted(number_words, key=lambda word: number_mapping[word])
    
    # Join the sorted words into a single string with spaces
    sorted_numbers = ' '.join(sorted_words)
    
    return sorted_numbers
```
"""

class CoderAgent(BaseAgent):
    def __init__(self,functions: List[Dict] = None):
        
        super().__init__(
            name="Code Generator",
            instructions=INSTRUCTIONS,
            model = "deepseek-coder",
            functions=functions or []
        )
        self.code_parser = CodeParser()     

    def run(self,requirement) -> str:
        prompt = PROMPT_TEMPLATE.format(requirement=requirement)
        response =  self.ask(prompt=prompt)
        # response =  answer
        code = self.code_parser.parse_code(block="",text = response,lang="python")
        self.update_context({"code":code})
        print(f"---------------------{colors.YELLOW} Code {colors.RESET}---------------------")
        display_code(code)
        return code

