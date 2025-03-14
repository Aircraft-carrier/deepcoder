# deepcoder/logger.py  
import sys  
from datetime import datetime  
from pathlib import Path  

from loguru import logger as _logger  

# 定义日志根目录  
DEEPCODER_ROOT = Path(__file__).parent

_print_level = "INFO"  
_llm_stream_log = print  # 默认使用 print 作为流日志记录函数  

def define_log_level(  
    print_level: str = "INFO",   
    logfile_level: str = "DEBUG",   
    name: str = None  
) -> _logger:  
    """  
    配置日志级别和日志文件  

    Args:  
        print_level (str): 控制台输出日志级别，默认为 "INFO"  
        logfile_level (str): 日志文件记录级别，默认为 "DEBUG"  
        name (str, optional): 日志文件名前缀  

    Returns:  
        logger: 配置后的日志对象  
    """  
    global _print_level  
    _print_level = print_level  

    # 创建日志目录  
    log_dir = DEEPCODER_ROOT / "logs"  
    log_dir.mkdir(exist_ok=True)  

    # 生成日志文件名  
    current_date = datetime.now()  
    formatted_date = current_date.strftime("%Y%m%d")  
    log_name = f"{name}_{formatted_date}" if name else formatted_date  

    # 移除现有日志处理器  
    _logger.remove()  

    # 添加控制台日志处理器  
    _logger.add(  
        sys.stderr,   
        level=print_level,   
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "  
               "<level>{level: <8}</level> | "  
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"  
    )  

    # 添加文件日志处理器  
    _logger.add(  
        log_dir / f"{log_name}.log",   
        level=logfile_level,  
        rotation="10 MB",  # 日志文件大小超过10MB时轮转  
        retention="10 days"  # 保留最近10天的日志  
    )  

    return _logger  

# 创建默认 logger  
logger = define_log_level()  

def log_llm_stream(msg):  
    """记录 LLM 流式输出的消息"""  
    _llm_stream_log(msg)  

def set_llm_stream_logfunc(func):  
    """  
    设置 LLM 流式日志记录函数  
    
    Args:  
        func (callable): 自定义的日志记录函数  
    """  
    global _llm_stream_log  
    _llm_stream_log = func  

# 示例用法  
def demo_logger_usage():  
    logger.debug("这是一个调试信息")  
    logger.info("这是一个信息")  
    logger.warning("这是一个警告")  
    logger.error("这是一个错误")  
    
    # 自定义流式日志记录函数示例  
    def custom_stream_log(msg):  
        print(f"Custom Stream Log: {msg}", end="")  
    
    set_llm_stream_logfunc(custom_stream_log)  
    log_llm_stream("LLM 输出流")  

if __name__ == "__main__":  
    demo_logger_usage()  