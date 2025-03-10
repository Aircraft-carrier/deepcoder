# 定义颜色常量  
class Colors:  
    RED = '\033[31m'  
    GREEN = '\033[32m'  
    YELLOW = '\033[33m'  
    BLUE = '\033[34m'  
    MAGENTA = '\033[35m'  
    CYAN = '\033[36m'  
    WHITE = '\033[37m'  
    RESET = '\033[0m'  # 重置颜色  

colors = Colors()

# 使用示例  
# print(f"{Colors.RED}这是红色的文本{Colors.RESET}")  
# print(f"{Colors.GREEN}这是绿色的文本{Colors.RESET}")  
# print(f"{Colors.YELLOW}这是黄色的文本{Colors.RESET}")  