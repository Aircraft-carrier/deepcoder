import json
from typing import Optional, Dict, List
from openai import OpenAI
from swarm import Swarm, Agent
from deepcoder.log import logger

class BaseAgent:
    def __init__(
        self,
        name: str,
        api_key: str = "sk-1fac7836ded54cfabf056520607a4c4d",
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        instructions: str = "",
        functions: List[Dict] = None,
        stream: bool = True
    ):
        """
        基础Agent类
        :param name: Agent名称
        :param api_key: API密钥
        :param base_url: API基础URL
        :param model: 使用的模型名称
        :param instructions: 系统提示词
        :param functions: 可用函数列表
        :param stream: 是否启用流式输出
        """
        self.openai_client = OpenAI(api_key=api_key, base_url=base_url)
        self.client = Swarm(self.openai_client)
        self.model = model
        self.stream = stream
        
        # 初始化Agent配置
        self.agent = Agent(
            name=name,
            model=self.model,
            instructions=instructions,
            functions=functions or []
        )
        
        # 消息历史记录
        self.messages: List[Dict] = []
        # 上下文变量存储
        self.context_variables: Dict = {}

    def ask(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        debug: bool = False
    ) -> str:
        """
        发起询问并获取响应
        :param prompt: 用户输入的提示词
        :param context: 附加的上下文变量
        :param debug: 是否开启调试模式
        :return: 完整的响应内容
        """
        # 添加用户消息到历史记录
        self._add_message("user", prompt)
        
        # 合并上下文变量
        merged_context = {**self.context_variables, **(context or {})}
        
        # 获取响应
        response = self.client.run(
            agent=self.agent,
            messages=self.messages,
            context_variables=merged_context,
            stream=self.stream,
            debug=debug,
        )
        
        # 处理响应
        if self.stream:
            full_response = self._process_stream(response)
        else:
            full_response = self._process_bulk(response)
        
        # 添加AI响应到历史记录
        self._add_message("assistant", full_response.messages[-1]["content"])
        return full_response.messages[-1]["content"]
    
    def process_stream_response(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        debug: bool = False
    ):
        self._add_message("user", prompt)
        merged_context = {**self.context_variables, **(context or {})}
        response_stream = self.client.run(
            agent=self.agent,
            messages=self.messages,
            context_variables=merged_context,
            stream=True,
            debug=debug,
        )        
            
        full_content = ""
        for chunk in response_stream:
            if "delim" in chunk and chunk["delim"] == "end":
                self._add_message("assistant", full_content)
            if "content" in chunk and chunk["content"]:
                full_content += chunk["content"]
                yield  chunk["content"]

        

    def _add_message(self, role: str, content: str) -> None:
        """添加消息到历史记录"""
        self.messages.append({
            "role": role,
            "content": content
        })
        logger.info(f"{self.agent.name} {'->' if role == 'assistant' else '<-'} {role}")  

    def _process_stream(self, response) -> str:
        """处理流式响应"""
        content = ""
        last_sender = ""
        
        for chunk in response:
            if "sender" in chunk:
                last_sender = chunk["sender"]
            # 处理内容块
            chunk_content = self._process_chunk(chunk, last_sender)
            
            if chunk_content:
                content += chunk_content
                if last_sender:
                    last_sender = ""
                
            # 处理特殊标记
            if chunk.get("delim") == "end" and content:
                print()  # 结束当前消息块
                
            # 获取最终响应对象
            if "response" in chunk:
                return chunk["response"]
        
        return content

    def _process_chunk(self, chunk: Dict, last_sender: str) -> str:
        """处理单个数据块"""
        content = ""
        
        # 处理文本内容
        if "content" in chunk and chunk["content"]:
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]
        
        # 处理工具调用
        if "tool_calls" in chunk and chunk["tool_calls"]:
            for tool_call in chunk["tool_calls"]:
                self._process_tool_call(tool_call)
        
        return content

    def _process_tool_call(self, tool_call: Dict) -> None:
        """处理工具调用"""
        func_info = tool_call["function"]
        name = func_info["name"]
        if name:
            args = json.loads(func_info.get("arguments", "{}"))
            arg_str = ", ".join(f"{k}={v}" for k, v in args.items())
            print(f"\033[95m{name}\033[0m({arg_str})")

    def _process_bulk(self, response) -> str:
        """处理批量响应"""
        full_content = ""
        for message in response.messages:
            if message["role"] == "assistant":
                content = message.get("content", "")
                if content:
                    full_content += content
                    print(f"\033[94m{message['sender']}:\033[0m {content}")
                
                # 处理工具调用
                for tool_call in message.get("tool_calls", []):
                    self._process_tool_call(tool_call)
        
        return full_content

    def clear_history(self) -> None:
        """清空对话历史"""
        self.messages = []

    def remove_last_interaction(self) -> None:  
        """删除最后一对对话（用户的问和助手的答）"""  
        if len(self.messages) >= 2:   
            self.messages = self.messages[:-2]  
        elif len(self.messages) == 1:   
            self.messages = []  

    def update_context(self, new_context: Dict) -> None:
        """更新上下文变量"""
        self.context_variables.update(new_context)

    def get_context(self,key):
        return self.context_variables.get(key)