from __future__ import annotations  # 允许延迟类型注解（Python 3.7+特性）

import asyncio      # 异步IO库
import base64       # Base64编解码
import re           # 正则表达式
from typing import Literal, Tuple  # 类型提示

import nbformat     # Jupyter Notebook格式处理
from nbclient import NotebookClient  # Notebook执行客户端
from nbclient.exceptions import CellTimeoutError, DeadKernelError  # 异常类
from nbformat import NotebookNode   # Notebook节点类型
from nbformat.v4 import new_code_cell, new_markdown_cell, new_output  # 创建Notebook元素
from rich.box import MINIMAL         # 富文本样式
from rich.console import Console, Group  # 控制台输出
from rich.live import Live           # 动态内容显示
from rich.markdown import Markdown   # Markdown渲染
from rich.panel import Panel         # 面板组件
from rich.syntax import Syntax       # 代码高亮

from deepcoder.log import logger      # 日志模块（假设来自自定义模块）

class ExecuteNbCode():
    """execute notebook code block, return result to llm, and display it."""
    # 类属性
    nb: NotebookNode          # Jupyter Notebook对象
    nb_client: NotebookClient # Notebook客户端
    console: Console          # 富文本控制台
    interaction: str          # 交互类型（terminal/ipython）
    timeout: int = 600        # 超时时间（秒）

    def __init__(
        self,
        nb=nbformat.v4.new_notebook(),  # 新建空Notebook
        timeout=600,
    ):
        # 直接初始化属性，而不调用父类的初始化方法
        self.nb = nb
        self.nb_client = NotebookClient(nb, timeout=timeout)
        self.timeout = timeout
        self.console = Console()
        self.interaction = "ipython" if self.is_ipython() else "terminal"

    async def build(self):
        # 创建并启动内核（如果不存在或不活跃）
        if self.nb_client.kc is None or not await self.nb_client.kc.is_alive():
            self.nb_client.create_kernel_manager()
            self.nb_client.start_new_kernel()        # 启动新内核
            self.nb_client.start_new_kernel_client() # 创建客户端连接

    async def terminate(self):
        """kill NotebookClient"""
        # 关闭内核并清理资源
        if self.nb_client.km is not None and await self.nb_client.km.is_alive():
            await self.nb_client.km.shutdown_kernel(now=True)   # 立即关闭内核
            await self.nb_client.km.cleanup_resources()         # 清理资源

            # 停止所有通信通道
            channels = [
                self.nb_client.kc.stdin_channel,   # 标准输入
                self.nb_client.kc.hb_channel,       # 心跳检测
                self.nb_client.kc.control_channel,  # 控制通道
            ]
            for channel in channels:
                if channel.is_alive():
                    channel.stop()

            # 清理引用
            self.nb_client.kc = None
            self.nb_client.km = None

    async def reset(self):
        """reset NotebookClient"""
        await self.terminate()   # 终止现有内核
        await asyncio.sleep(1)   # 等待1秒确保清理完成
        await self.build()       # 重建内核
        self.nb_client = NotebookClient(self.nb, timeout=self.timeout)  # 重置客户端

    def add_code_cell(self, code: str):
        # 添加代码单元格到Notebook
        self.nb.cells.append(new_code_cell(source=code))

    def add_markdown_cell(self, markdown: str):
        # 添加Markdown单元格到Notebook
        self.nb.cells.append(new_markdown_cell(source=markdown))

    def _display(self, code: str, language: Literal["python", "markdown"] = "python"):
        # 使用rich库美化显示代码/Markdown
        if language == "python":
            code = Syntax(code, "python", theme="paraiso-dark", line_numbers=True)
            self.console.print(code)  # 语法高亮打印
        elif language == "markdown":
            display_markdown(code)    # 渲染Markdown
        else:
            raise ValueError(f"Unsupported language: {language}")

    def add_output_to_cell(self, cell: NotebookNode, output: str):
        # 将执行输出添加到单元格
        if "outputs" not in cell:
            cell["outputs"] = []
        cell["outputs"].append(new_output(output_type="stream", name="stdout", text=str(output)))

    def parse_outputs(self, outputs: list[str], keep_len: int = 2000) -> Tuple[bool, str]:
        """解析Notebook执行输出"""
        parsed_output, is_success = [], True
        for output in outputs:
            output_text = ""
            # 处理不同类型的输出
            if output["output_type"] == "stream":
                output_text = output["text"]
            elif output["output_type"] == "display_data":
                if "image/png" in output["data"]:  # 显示图片
                    self.show_bytes_figure(output["data"]["image/png"], self.interaction)
            elif output["output_type"] == "execute_result":
                output_text = output["data"]["text/plain"]
            elif output["output_type"] == "error":  # 错误处理
                output_text, is_success = "\n".join(output["traceback"]), False

            # 处理未执行的协程对象
            if output_text.strip().startswith("<coroutine object"):
                output_text = "Error: Use 'await' for async code."
                is_success = False

            # 清理转义字符并截取有效部分
            output_text = remove_escape_and_color_codes(output_text)
            output_text = output_text[:keep_len] if is_success else output_text[-keep_len:]
            parsed_output.append(output_text)
        return is_success, ",".join(parsed_output)

    def show_bytes_figure(self, image_base64: str, interaction_type: Literal["ipython", None]):
        # 显示Base64编码的图片
        image_bytes = base64.b64decode(image_base64)
        if interaction_type == "ipython":
            # 在Jupyter中显示
            from IPython.display import Image, display
            display(Image(data=image_bytes))
        else:
            # 在终端使用PIL显示
            import io
            from PIL import Image
            image = Image.open(io.BytesIO(image_bytes))
            image.show()

    def is_ipython(self) -> bool:
        try:
            from IPython import get_ipython
            ip = get_ipython()
            return ip is not None and "IPKernelApp" in ip.config
        except (ImportError, AttributeError):
            return False

    async def run_cell(self, cell: NotebookNode, cell_index: int) -> Tuple[bool, str]:
        """执行单个单元格"""
        try:
            await self.nb_client.async_execute_cell(cell, cell_index)  # 异步执行
            return self.parse_outputs(self.nb.cells[-1].outputs)       # 解析输出
        except CellTimeoutError:  # 处理超时
            await self.nb_client.km.interrupt_kernel()
            await asyncio.sleep(1)
            return False, "Timeout Error: Code execution took too long."
        except DeadKernelError:   # 内核死亡
            await self.reset()
            return False, "Kernel Died. Restarted."
        except Exception:         # 其他异常
            return self.parse_outputs(self.nb.cells[-1].outputs)

    async def run(self, code: str, language: Literal["python", "markdown"] = "python") -> Tuple[str, bool]:
        """主执行方法"""
        self._display(code, language)  # 显示代码/Markdown
        if language == "python":
            self.add_code_cell(code)   # 添加代码单元格
            await self.build()         # 准备内核
            cell_index = len(self.nb.cells) - 1
            success, outputs = await self.run_cell(self.nb.cells[-1], cell_index)
            if "!pip" in code:         # 特殊处理pip命令
                success = False
            return outputs, success
        elif language == "markdown":
            self.add_markdown_cell(code)
            return code, True          # Markdown无需执行
        else:
            raise ValueError(f"Unsupported language: {language}")

# 辅助函数
def remove_escape_and_color_codes(input_str: str):
    # 使用正则表达式去除ANSI转义码
    return re.sub(r"\x1b\[[0-9;]*[mK]", "", input_str)

def display_markdown(content: str):
    # 使用rich分块渲染Markdown
    matches = re.finditer(r"```(.+?)```", content, re.DOTALL)
    panels = []
    style = "black on white"
    start_index = 0
    for match in matches:
        # 处理文本和代码块
        text = content[start_index:match.start()].strip()
        if text:
            panels.append(Panel(Markdown(text), style=style, box=MINIMAL))
        code = match.group(0).strip()[3:-3]  # 去除```
        if code:
            panels.append(Panel(Markdown(f"```{code}"), style=style, box=MINIMAL))
        start_index = match.end()
    # 处理剩余文本
    remaining = content[start_index:].strip()
    if remaining:
        panels.append(Panel(Markdown(remaining), style=style, box=MINIMAL))
    # 动态显示
    with Live(auto_refresh=False) as live:
        live.update(Group(*panels))
        live.refresh()