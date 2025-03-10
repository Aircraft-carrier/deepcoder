import re
from rich.console import Console,Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.box import MINIMAL

def display_code(code: str, language: str = "python"):
    """
    在控制台中高亮显示代码或渲染Markdown内容。
    
    参数:
        code (str): 要显示的代码或Markdown内容
        language (str): 代码语言（如'python', 'javascript'），或'markdown'以渲染Markdown
    """
    console = Console()
    
    if language == "markdown":
        panels = []
        style = "black on white"
        # 分割Markdown中的代码块和普通文本
        parts = re.split(r"(```[\s\S]*?```)", code)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if part.startswith("```"):
                # 处理代码块
                code_block = part[3:-3].strip()  # 移除前后的```
                if '\n' not in code_block:
                    code_lang = 'text'
                    code_content = code_block
                else:
                    # 提取代码语言和内容
                    first_newline = code_block.find('\n')
                    code_lang = code_block[:first_newline].strip() or 'text'
                    code_content = code_block[first_newline+1:].lstrip('\n')
                
                # 高亮代码
                syntax = Syntax(code_content, code_lang, theme="paraiso-dark", line_numbers=True)
                panels.append(Panel(syntax, style=style, box=MINIMAL))
            else:
                # 渲染普通Markdown文本
                panels.append(Panel(Markdown(part), style=style, box=MINIMAL))
        
        # 动态显示所有面板
        with Live(auto_refresh=False) as live:
            live.update(Group(*panels))
            live.refresh()
    else:
        # 直接高亮其他语言代码
        syntax = Syntax(code, language, theme="paraiso-dark", line_numbers=True)
        console.print(syntax)

def stream_display_code(code: str, language: str = "python"):
    """
    流式输出代码/Markdown的带格式字符串生成器
    
    参数:
        code (str): 要处理的代码或Markdown内容
        language (str): 代码语言或'markdown'
        
    Yields:
        str: 带ANSI转义码的渲染结果字符串
    """
    console = Console(record=True)
    
    if language == "markdown":
        # 分割Markdown文本和代码块
        parts = re.split(r"(```[\s\S]*?```)", code)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part.startswith("```"):
                # 处理代码块
                code_block = part[3:-3].strip()  # 移除```
                
                # 解析代码语言
                if '\n' not in code_block:
                    code_lang = 'text'
                    code_content = code_block
                else:
                    first_newline = code_block.find('\n')
                    code_lang = code_block[:first_newline].strip() or 'text'
                    code_content = code_block[first_newline+1:].lstrip('\n')
                
                # 生成代码高亮
                syntax = Syntax(code_content, code_lang, 
                               theme="paraiso-dark", line_numbers=True)
                panel = Panel(syntax, box=MINIMAL)
            else:
                # 生成Markdown段落
                panel = Panel(Markdown(part), box=MINIMAL)
            
            # 捕获渲染结果并重置缓存
            with console.capture() as capture:
                console.print(panel, end="")
            yield capture.get()
            
            # 可选：添加块间隔
            yield "\n\n"
            
    else:
        # 直接生成代码高亮
        syntax = Syntax(code, language, 
                       theme="paraiso-dark", line_numbers=True)
        with console.capture() as capture:
            console.print(syntax)
        yield capture.get()

from typing import Generator, Union
class StreamDisplay:
    """流式代码渲染上下文管理器"""
    def __init__(self, language: str = "python"):
        self.console = Console(record=True)
        self.live = None
        self.language = language
        self.buffer = []
        self.in_code_block = False
        self.current_code = []
        self.current_lang = "text"

    def __enter__(self):
        self.live = Live(auto_refresh=False, console=self.console)
        self.live.__enter__()
        return self

    def __exit__(self, *args):
        self._flush_buffer()
        self.live.__exit__(*args)

    def _render_chunk(self, chunk: str) -> str:
        """渲染单个块并返回ANSI字符串"""
        with self.console.capture() as cap:
            if self.language == "markdown":
                self._process_markdown_chunk(chunk)
            else:
                self.console.print(Syntax(chunk, self.language, 
                                        theme="paraiso-dark", 
                                        line_numbers=True))
        return cap.get()

    def _process_markdown_chunk(self, chunk: str):
        """处理Markdown片段的流式输入"""
        buffer = chunk.split('```')
        
        for i, part in enumerate(buffer):
            if not part:
                continue
            
            # 交替处理文本和代码块
            if i % 2 == 0:
                # 文本部分
                if self.in_code_block:
                    self.current_code.append(part)
                else:
                    self.buffer.append(Panel(Markdown(part), box=MINIMAL))
            else:
                # 代码块分界处理
                if self.in_code_block:
                    # 结束代码块
                    code_content = '\n'.join(self.current_code).strip()
                    syntax = Syntax(code_content, self.current_lang,
                                  theme="paraiso-dark", line_numbers=True)
                    self.buffer.append(Panel(syntax, box=MINIMAL))
                    self.current_code = []
                    self.in_code_block = False
                else:
                    # 开始代码块
                    lang_split = part.split('\n', 1)
                    self.current_lang = lang_split[0].strip() or "text"
                    if len(lang_split) > 1:
                        self.current_code.append(lang_split[1].lstrip('\n'))
                    self.in_code_block = True

    def _flush_buffer(self):
        """渲染缓冲区内容"""
        if self.buffer:
            self.console.print(Group(*self.buffer))
            self.buffer = []

    def update(self, chunk: str):
        """更新流式内容"""
        # 处理当前块
        rendered = self._render_chunk(chunk)
        
        # 动态更新显示
        self.live.update(Group(*self.buffer)) if self.buffer else None
        self.live.refresh()
        
        return rendered

def stream_renderer(code_stream: Union[Generator[str, None, None], str], 
                    language: str = "python") -> Generator[str, None, None]:
    """
    流式代码渲染生成器
    
    参数:
        code_stream: 字符串生成器或普通字符串
        language: 代码语言（支持'markdown'）
        
    生成:
        带ANSI转义码的渲染结果流
    """
    with StreamDisplay(language) as display:
        # 统一处理生成器和普通字符串
        chunks = code_stream if isinstance(code_stream, Generator) else iter([code_stream])
        
        for chunk in chunks:
            rendered = display.update(chunk)
            yield rendered