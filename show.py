import sys
sys.path.append("E:/A25cun/coder")
import gradio as gr
from deepcoder.agent.coder import CoderAgent
from deepcoder.agent.tester import TesterAgent
from deepcoder.agent.debug_error import DebugAgent
from deepcoder.agent.reviewer import ReviewerAgent
from deepcoder.utils import CodeParser
from deepcoder.interpreter import display_code,execute,colors
from deepcoder.interpreter import execute
from deepcoder.log import logger
from typing import Tuple, Any
import html

coder = CoderAgent()
tester = TesterAgent()
debug = DebugAgent()
reviewer = ReviewerAgent()
code_parser = CodeParser()

DEBUG_PROMPT_TEMPLATE = """
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

CODER_PROMPT_TEMPLATE = """
The message is as follows:
# Requirement

{requirement}

---
Now you should start writing the code:
## Write code with triple quote. Do your best to implement THIS IN ONLY ONE FILE.
"""

TESTER_PROMPT_TEMPLATE = """
The message is as follows:
# Requirement

{requirement}

---
Now you should start writing test case for the code:
Note : Generate up to 5 test cases.
## Write TestCase with triple quote. Do your best to implement THIS IN ONLY ONE FILE.
Test Case : 
"""

REVIEWER_PROMPT_TEMPLATE = """
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
## Write prompt with triple quote. Do your best to implement THIS IN ONLY ONE FILE.
"""

class AgentState:
    def __init__(self):
        self.current_input = ""
        self.coder_step = ""
        self.tester_step = ""
        self.execution = ""
        self.final_output = ""

def create_response(history, block, state):  
    if history[-1]["role"] == "assistant":
        history[-1]["content"] = block 
        return history,state
    return history + [{"role": "assistant", "content": block}], state  

def modify_state(name,content,state):
    if name == "Coder":
        code = code_parser.parse_code(block="",text = content,lang="python")
        print(f"---------------------{colors.YELLOW} Code {colors.RESET}---------------------")
        if code:
            display_code(code)
            state.coder_step = code
    elif name == "Tester":
        test_code = code_parser.parse_code(block="",text = content,lang="python")
        print(f"---------------------{colors.YELLOW} Test Cases {colors.RESET}---------------------")
        if test_code:
            display_code(test_code)
            state.tester_step = test_code
    elif name == "Reviewer":
        prompt = code_parser.parse_code(block="",text = content,lang="python")
        print(f"---------------------{colors.YELLOW} Prompt {colors.RESET}---------------------")
        if prompt:
            display_code(prompt)
            state.current_input = prompt
    elif name == "Debug":
        code = code_parser.parse_code(block="ReWrited Code",text = content,lang="python")
        print(f"---------------------{colors.YELLOW} Debug - ReWrited Code {colors.RESET}---------------------")
        if code:
            state.coder_step = code
            display_code(code)
        test_cases = code_parser.parse_code(block="ReWrited Test Case",text = content,lang="python")
        print(f"---------------------{colors.YELLOW} Debug - ReWrited Test Case {colors.RESET}---------------------")
        if test_cases:
            state.tester_step = test_cases
            display_code(test_cases)
    return state

def _handle_agent(history, state: AgentState, agent, process_stream_response):  
    """通用处理函数，实现动态更新"""  
    try:  
        full_content = ""  
        pre_block = history[-1]["content"] if history[-1]["role"] == "assistant" else ""  
        
        # 处理流式响应  
        for partial_content in process_stream_response(agent['prompt']):  
            full_content += partial_content  
            updated_block = wrap_thinking(agent["processing"], f"\n{full_content}", is_open=True)  
            yield create_response(history, pre_block + updated_block, state)  
        
        # 完成时收起折叠块  
        final_block = wrap_thinking(agent["completion"], f"\n {agent['name']} \n{full_content}\n --由 deepcoder 生成")   
        state = modify_state(agent['name'],full_content,state)
        yield create_response(history, pre_block + final_block, state)  

    except Exception as e:  
        error_block = wrap_thinking(agent["error"], f"\n错误信息：{str(e)}")  
        yield create_response(history, pre_block + error_block, state)  

def handle_coder_agent(history, state: AgentState):  
    """代码生成阶段（流式更新）"""  
    prompt = CODER_PROMPT_TEMPLATE.format(requirement=state.current_input)
    agent_info = {  
        "name": "Coder",  
        "processing": "代码生成中...",  
        "completion": "✅ 代码生成完成（点击查看详情）",  
        "error": "❌ 代码生成出错",
        "prompt": prompt
    }  
    coder.clear_history()
    yield from _handle_agent(history, state, agent_info, coder.process_stream_response)  

def handle_tester_agent(history, state: AgentState):  
    """测试生成阶段（流式更新）"""  
    prompt = TESTER_PROMPT_TEMPLATE.format(requirement=state.current_input)
    agent_info = {  
        "name": "Tester",  
        "processing": "测试生成中...",  
        "completion": "✅ 测试用例生成完成（点击查看详情）",  
        "error": "❌ 测试生成出错",
        "prompt": prompt
    }  
    tester.clear_history()
    yield from _handle_agent(history, state, agent_info, tester.process_stream_response)  

def handle_debug_agent(history, state: AgentState):  
    """调试阶段（流式更新）"""  
    prompt = DEBUG_PROMPT_TEMPLATE.format(code=state.coder_step,  
                                          test_code=state.tester_step,  
                                          logs=state.execution)  
    agent_info = {  
        "name": "Debug",  
        "processing": "调试进行中...",  
        "completion": "✅ 调试完成（点击查看详情）",  
        "error": "❌ 调试生成出错",
        "prompt": prompt  
    }  
    debug.clear_history()
    yield from _handle_agent(history, state, agent_info, debug.process_stream_response) 

def hand_reviewer_agent(history, state: AgentState):  
    """调试阶段（流式更新）"""  
    prompt = REVIEWER_PROMPT_TEMPLATE.format(legacy_prompt=state.current_input,
                                             logs =state.execution)  
    agent_info = {  
        "name": "Reviewer",  
        "processing": "优化 Prompt 进行中...",  
        "completion": "✅ 优化完成（点击查看详情）",  
        "error": "❌ 优化过程出错",
        "prompt": prompt  
    }  
    reviewer.clear_history()
    yield from _handle_agent(history, state, agent_info, debug.process_stream_response) 

def handle_write_and_exec_code(history, state: AgentState):
    """执行阶段生成阶段（流式更新）"""
    counter = 0
    max_retry = 3
    sucess = False

    while not sucess and counter < max_retry:
        if counter == 0:
            for updated_history, updated_state in handle_coder_agent(history,state):
                yield updated_history, updated_state
            history, state = updated_history, updated_state
            for updated_history, updated_state in handle_tester_agent(history,state):
                yield updated_history, updated_state
            history, state = updated_history, updated_state
        elif counter == 2:
            for updated_history, updated_state in hand_reviewer_agent(history,state):
                yield updated_history, updated_state
            history, state = updated_history, updated_state
            for updated_history, updated_state in handle_coder_agent(history,state):
                yield updated_history, updated_state
            history, state = updated_history, updated_state
        else:
            for updated_history, updated_state in handle_debug_agent(history,state):
                yield updated_history, updated_state
            history, state = updated_history, updated_state

        current_code = f"{state.coder_step}\n\n{state.tester_step}"
        execution_result, success = execute(current_code,"python")
        pre_block = history[-1]["content"] if history[-1]["role"] == "assistant" else ""  

        if not success:
            execution_block = wrap_thinking(f"执行失败 (attempt {counter + 1}/{max_retry})", f"\n{execution_result}")  
            history, state = create_response(history, pre_block + execution_block, state)
            yield history, state
            state.execution = current_code + "\n" + str(execution_result) 
        else:
            execution_block = wrap_thinking(f"执行成功 (attempt {counter + 1}/{max_retry})", f"\n{execution_result}")  
            history, state = create_response(history, pre_block + execution_block, state)
            yield history, state
        print(f"---------------------{colors.RED} Execution Result {colors.RESET}---------------------")
        display_code(state.execution)
        counter += 1
    
    yield history + [
        {"role": "assiatant","content": f"生成代码如下 ： \n```python\n{state.coder_step}\n```"}
    ],state


css = """
:root {
    --thinking-bg: #f0f8ff;       
    --thinking-border: #c3dafe;   
    --text-dark: #333333;        
    --summary-blue: #1e90ff;     
}

/* 折叠容器 */
.thinking-process {
    background: var(--thinking-bg);
    border: 1px solid var(--thinking-border);
    border-radius: 8px;
    margin: 12px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
}

/* 展开状态 */
.thinking-process[open] {
    background: #e6f2ff;  
    border-color: #a0c4ff;
}

/* 摘要栏 */
.thinking-process summary {
    color: var(--summary-blue);
    padding: 10px 16px;
    font-weight: 600;
    font-size: 0.95em;
    cursor: pointer;
    transition: color 0.2s;
}

/* 悬停效果 */
.thinking-process summary:hover {
    color: #0066cc;
}

/* 内容区域 */
.thinking-content {
    padding: 12px 16px;
    color: var(--text-dark);
    line-height: 1.6;
    background: linear-gradient(to bottom, #f8fbff, #f0f8ff);
    border-radius: 0 0 6px 6px;
    font-family: 'Consolas', monospace;
    font-size: 0.9em;
    white-space: pre-wrap;  
    word-break: break-word;  
    overflow-wrap: anywhere; 
}

.content-block br {
    margin-bottom: 0.8em;  
    display: block;       
    content: "";          
}

[data-testid="bot"] > :not(.thinking-process) {
    background: var(--thinking-bg);
    border: 1px solid var(--thinking-border);
    padding: 14px;
    border-radius: 8px;
    color: var(--text-dark);
}
"""

with gr.Blocks(theme=gr.themes.Soft(), title="DeepSeek Multi-Agent",css=css) as demo:
    gr.Markdown("## DeepSeek大模型代码生成助手")
    
    # 聊天窗口（使用新版messages格式）
    chatbot = gr.Chatbot(
        value=[],
        bubble_full_width=False,
        render_markdown=True,
        height=600,
        avatar_images=(None, None),
        show_copy_button=True,
        layout="panel",
        type="messages" 
    )
    
    # 状态存储
    state = gr.State(AgentState())
    
    # 输入组件
    with gr.Row():
        msg = gr.Textbox(
            scale=4,
            placeholder="输入消息...",
            container=False,
            autofocus=True
        )
        submit_btn = gr.Button("发送", variant="primary")
        clear_btn = gr.ClearButton([msg, chatbot])

    def process_message(message, history, state: AgentState):
        """处理消息并清空输入框"""
        state.current_input = message
        return "", history + [{"role": "user", "content": message}],state
    
    def format_content(text):
        """预处理文本内容"""
        # 转义HTML特殊字符
        text = html.escape(text)
        # 将换行符转换为HTML换行（双保险）
        text = text.replace('\n', '<br>')
        # 添加段落间距
        return f'<div class="content-block">{text}</div>'

    def wrap_thinking(title, content, is_open=False):
        """带状态的折叠块包装"""
        # content = format_content(content) if is_open else content
        content = format_content(content)
        open_attr = "open" if is_open else ""
        return f"""
    <details {open_attr} class='thinking-process'>
        <summary>🔍 {title}</summary>
        <div class="thinking-content">{content}</div>
    </details>
    """

    # 调整事件处理链
    msg.submit(
        process_message,
        inputs=[msg, chatbot, state],  
        outputs=[msg, chatbot, state],      
        queue=False
    ).then(
        handle_write_and_exec_code,
        inputs=[  
            chatbot, 
            state
        ],
        outputs=[chatbot, state]
    )
    # .then(
    #     handle_coder_agent,
    #     inputs=[  
    #         chatbot, 
    #         state
    #     ],
    #     outputs=[chatbot, state]
    # ).then(
    #     handle_tester_agent,
    #     inputs=[  
    #         chatbot, 
    #         state
    #     ],
    #     outputs=[chatbot, state]
    # )

    
    submit_btn.click(
        process_message,
        inputs=[msg, chatbot, state],  
        outputs=[msg, chatbot, state],      
        queue=False
    ).then(
        handle_write_and_exec_code,
        inputs=[  
            chatbot, 
            state
        ],
        outputs=[chatbot, state]
    )

if __name__ == "__main__":
    demo.queue().launch()