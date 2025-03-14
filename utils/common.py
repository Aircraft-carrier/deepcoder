from __future__ import annotations

import ast
import re
from deepcoder.log import logger

class CodeParser:  
    @classmethod  
    def parse_block(cls, block: str, text: str) -> str:  
        """  
        根据给定的块标题从文本中提取对应的内容块。  
        
        Args:  
            block (str): 要查找的块标题  
            text (str): 源文本内容  
        
        Returns:  
            str: 匹配的块内容，如果未找到则返回空字符串  
        """  
        blocks = cls.parse_blocks(text)  
        for k, v in blocks.items():  
            if block in k:  
                return v  
        return ""  

    @classmethod  
    def parse_blocks(cls, text: str):  
        """  
        将文本按"##"分割成多个内容块，并组织成字典。  
        
        Args:  
            text (str): 源文本内容  
        
        Returns:  
            dict: 以块标题为键，块内容为值的字典  
        """  
        # 首先根据"##"将文本分割成不同的block  
        blocks = text.split("##")  

        # 创建一个字典，用于存储每个block的标题和内容  
        block_dict = {}  

        # 遍历所有的block  
        for block in blocks:  
            # 跳过空block  
            if block.strip() == "":  
                continue  
            
            # 处理无换行符的特殊情况（只有标题）  
            if "\n" not in block:  
                block_title = block  
                block_content = ""  
            else:  
                # 将block的标题和内容分开，并去除前后空白字符  
                block_title, block_content = block.split("\n", 1)  
            
            block_title = block_title.replace('"', '').strip()  
            
            block_dict[block_title] = block_content.strip()   

        return block_dict  

    @classmethod  
    def parse_code(cls, block: str, text: str, lang: str = "") -> str:  
        """  
        从文本中提取特定语言的代码块。  
        
        Args:  
            block (str): 可选的块标题，用于先定位内容块  
            text (str): 源文本内容  
            lang (str, optional): 编程语言标识，用于精确匹配代码块  
        
        Returns:  
            str: 提取的代码内容，如果未找到则返回原文本  
        """  
        # 如果提供了块标题，先定位内容块  
        if block:  
            text = cls.parse_block(block, text) 
        
        # 构建正则表达式匹配代码块  
        pattern = rf"```{lang}.*?\s+(.*?)```"  
        match = re.search(pattern, text, re.DOTALL)  
        
        if match:  
            code = match.group(1)  
        else:  
            logger.error(f"{pattern} not match following text:")  
            logger.error(text)  
            return text  # 如果未匹配，假定原文本就是代码  

        return code  

    @classmethod  
    def parse_str(cls, block: str, text: str, lang: str = ""):  
        """  
        提取并清理字符串值。  
        
        Args:  
            block (str): 可选的块标题  
            text (str): 源文本内容  
            lang (str, optional): 编程语言标识  
        
        Returns:  
            str: 清理后的字符串值  
        """  
        # 先提取代码块  
        code = cls.parse_code(block, text, lang)  
        
        # 提取等号右侧的值并去除引号  
        code = code.split("=")[-1]  
        code = code.strip().strip("'").strip('"')  
        return code  

    @classmethod  
    def parse_file_list(cls, block: str, text: str, lang: str = "") -> list[str]:  
        """  
        从文本中提取文件列表。  
        
        Args:  
            block (str): 可选的块标题  
            text (str): 源文本内容  
            lang (str, optional): 编程语言标识  
        
        Returns:  
            list[str]: 解析出的文件列表  
        
        Raises:  
            Exception: 当无法解析列表时  
        """  
        # 提取代码块  
        code = cls.parse_code(block, text, lang)  
        
        # 正则表达式匹配列表  
        pattern = r"\s*(.*=.*)?(\[.*\])"  

        # 使用正则提取列表字符串  
        match = re.search(pattern, code, re.DOTALL)  
        if match:  
            tasks_list_str = match.group(2)  

            # 使用ast安全地将字符串转换为列表  
            tasks = ast.literal_eval(tasks_list_str)  
        else:  
            raise Exception("无法解析文件列表")  
        
        return tasks  