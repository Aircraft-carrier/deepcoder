from typing import Optional, Dict, List, Tuple
from .agent import BaseAgent
from deepcoder.utils import CodeParser
from deepcoder.interpreter import display_code,colors

INSTRUCTIONS = """
**Role**: You are a Prompt Reviewer specialized in code generation tasks.

**Task**: Given an original prompt and test errors from generated code, rewrite the prompt to explicitly prevent recurring failures.
 Do NOT generate code.

**Instructions**:
1. **Error Diagnosis**:
   - Classify the test error type (e.g., ValueError, Logic Error, Edge Case).
   - Identify missing constraints in the original prompt that allowed the error.

2. **Constraint Formalization**:
   - Convert implicit assumptions into explicit requirements.

3. **Prompt Restructuring**:
   - Organize requirements using numbered lists or section headers.
   - Include both positive examples and failure-driven constraints.
   - Preserve core functionality while adding error prevention measures.

Modification Map:
- "[Original phrase]" → "[New constraint]" (Rationale: [Test error context])

**Output Format**: Return ONLY in this format:

## Revised Prompt
```python
[Improved prompt here]
```
"""

PROMPT_TEMPLATE = """
The message is as follows:
# Legacy Prompt
```markdown
{legacy_prompt}
```
---
# Console logs
```text
{logs}
```
---
Now you should start rewriting the prompt:
## Write prompt with ```python [your code]``` format. Do your best to implement THIS IN ONLY ONE FILE.
"""


class ReviewerAgent(BaseAgent):
    def __init__(self,functions: List[Dict] = None):
        
        super().__init__(
            name="Reviewer Generator",
            instructions=INSTRUCTIONS,
            functions=functions or []
        )
        self.code_parser = CodeParser()     

    def run(self,legacy_prompt,logs) -> str:
        prompt = PROMPT_TEMPLATE.format(legacy_prompt=legacy_prompt,logs =logs)
        response =  self.ask(prompt=prompt)
        # response =  answer
        prompt = self.code_parser.parse_code(block="",text = response,lang="python")
        self.update_context({"prompt":prompt})
        print(f"---------------------{colors.YELLOW} Prompt {colors.RESET}---------------------")
        display_code(prompt)
        return prompt

