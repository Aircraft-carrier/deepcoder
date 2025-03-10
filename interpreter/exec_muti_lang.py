import os
import shutil
import tempfile
import subprocess
import random
from typing import Tuple
class TimeoutException(Exception):
    pass

def execute(code: str, language_type: str, timeout: int = 10) -> Tuple[str,bool]:
    """执行代码并返回结果
    
    Args:
        code (str): 要执行的代码
        language_type (str): 编程语言类型 (python/go/js/java/cpp/...)
        timeout (int): 执行超时时间（秒）
    
    Returns:
        str: 执行结果 ("passed"/"failed: {error}"/"timed out")
    """
    result = []
    tmp_dir = tempfile.mkdtemp()
    random_id = random.randint(1, 100000)
    lang = language_type.lower()

    try:
        if "python" in lang:
            _handle_python(code, tmp_dir, timeout, result)
        elif "go" in lang:
            _handle_go(code, tmp_dir, timeout, result, random_id)
        elif "js" in lang or "javascript" in lang:
            _handle_js(code, tmp_dir, timeout, result, random_id)
        elif "java" in lang:
            _handle_java(code, tmp_dir, timeout, result, random_id)
        elif "cpp" in lang or "c++" in lang:
            _handle_cpp(code, tmp_dir, timeout, result, random_id)
        elif "php" in lang:
            _handle_php(code, tmp_dir, timeout, result, random_id)
        elif "sh" in lang or "shell" in lang:
            _handle_shell(code, tmp_dir, timeout, result, random_id)
        else:
            result.append(f"Unsupported language: {language_type}")
    except Exception as e:
        result.append(f"Execution error: {str(e)}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    
    return result[0] if result else "No execution result",result[0]=="passed"

def _handle_python(code, tmp_dir, timeout, result):
    """处理Python代码执行"""
    origin_dir = os.getcwd()
    try:
        os.chdir(tmp_dir)
        with open("script.py", "w") as f:
            f.write(code)
        
        # 在子进程中执行以支持超时
        process = subprocess.run(
            ["python", "script.py"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Unknown error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    finally:
        os.chdir(origin_dir)

def _handle_go(code, tmp_dir, timeout, result, random_id):
    """处理Go代码执行"""
    origin_dir = os.getcwd()
    work_dir = os.path.join(tmp_dir, f"go_{random_id}")
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        os.chdir(work_dir)
        with open("main_test.go", "w") as f:
            f.write(code)
        
        process = subprocess.run(
            ["go", "test", f"-timeout={timeout}s", "main_test.go"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Unknown error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    except Exception as e:
        result.append(f"failed: {str(e)}")
    finally:
        os.chdir(origin_dir)

def _handle_js(code, tmp_dir, timeout, result, random_id):
    """处理JavaScript代码执行"""
    origin_dir = os.getcwd()
    work_dir = os.path.join(tmp_dir, f"js_{random_id}")
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        os.chdir(work_dir)
        with open("test.js", "w") as f:
            f.write(code)
        
        process = subprocess.run(
            ["node", "test.js"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Unknown error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    finally:
        os.chdir(origin_dir)

def _handle_java(code, tmp_dir, timeout, result, random_id):
    """处理Java代码执行"""
    origin_dir = os.getcwd()
    work_dir = os.path.join(tmp_dir, f"java_{random_id}")
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        os.chdir(work_dir)
        with open("Main.java", "w") as f:
            f.write(code)
        
        # 编译Java代码
        compile_process = subprocess.run(
            ["javac", "Main.java"],
            capture_output=True,
            text=True
        )
        
        if compile_process.returncode != 0:
            err = compile_process.stderr or "Compilation error"
            result.append(f"failed: {err.strip()}")
            return
        
        # 执行Java程序
        process = subprocess.run(
            ["java", "Main"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Runtime error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    finally:
        os.chdir(origin_dir)

def _handle_cpp(code, tmp_dir, timeout, result, random_id):
    """处理C++代码执行"""
    origin_dir = os.getcwd()
    work_dir = os.path.join(tmp_dir, f"cpp_{random_id}")
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        os.chdir(work_dir)
        with open("test.cpp", "w") as f:
            f.write(code)
        
        # 编译C++代码
        compile_process = subprocess.run(
            ["g++", "-std=c++17", "test.cpp", "-o", "test"],
            capture_output=True,
            text=True
        )
        
        if compile_process.returncode != 0:
            err = compile_process.stderr or "Compilation error"
            result.append(f"failed: {err.strip()}")
            return
        
        # 执行程序
        process = subprocess.run(
            ["./test"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Runtime error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    finally:
        os.chdir(origin_dir)

def _handle_php(code, tmp_dir, timeout, result, random_id):
    """处理PHP代码执行"""
    origin_dir = os.getcwd()
    work_dir = os.path.join(tmp_dir, f"php_{random_id}")
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        os.chdir(work_dir)
        with open("test.php", "w") as f:
            f.write(code)
        
        process = subprocess.run(
            ["php", "test.php"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Unknown error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    finally:
        os.chdir(origin_dir)

def _handle_shell(code, tmp_dir, timeout, result, random_id):
    """处理Shell脚本执行"""
    origin_dir = os.getcwd()
    work_dir = os.path.join(tmp_dir, f"sh_{random_id}")
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        os.chdir(work_dir)
        script_path = os.path.join(work_dir, "test.sh")
        with open(script_path, "w") as f:
            f.write(code)
        os.chmod(script_path, 0o755)  # 添加执行权限
        
        process = subprocess.run(
            ["/bin/bash", script_path],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Unknown error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    finally:
        os.chdir(origin_dir)

def _handle_rust(code, tmp_dir, timeout, result, random_id):
    """处理Rust代码执行"""
    origin_dir = os.getcwd()
    work_dir = os.path.join(tmp_dir, f"rust_{random_id}")
    
    try:
        # 创建Cargo项目结构
        os.makedirs(work_dir, exist_ok=True)
        os.chdir(work_dir)
        
        # 生成Cargo.toml
        cargo_toml = """
[package]
name = "rust_temp"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
        with open("Cargo.toml", "w") as f:
            f.write(cargo_toml.strip())
        
        # 创建源代码文件
        src_dir = os.path.join(work_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(src_dir, "main.rs"), "w") as f:
            f.write(code)
        
        # 编译项目
        compile_process = subprocess.run(
            ["cargo", "build", "--release"],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if compile_process.returncode != 0:
            err = compile_process.stderr or "Compilation error"
            result.append(f"failed: {err.strip()}")
            return
        
        # 执行程序
        exec_path = os.path.join(work_dir, "target/release/rust_temp")
        process = subprocess.run(
            [exec_path],
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            result.append("passed")
        else:
            err = process.stderr or process.stdout or "Runtime error"
            result.append(f"failed: {err.strip()}")
            
    except subprocess.TimeoutExpired:
        result.append("timed out")
    except Exception as e:
        result.append(f"failed: {str(e)}")
    finally:
        os.chdir(origin_dir)
        shutil.rmtree(work_dir, ignore_errors=True)

if __name__ == "__main__":
    # 测试用例
    tests = [
        ("print('Hello World!')", "python", "passed"),
        ("package main\nimport \"testing\"\nfunc TestExample(t *testing.T) {}", "go", "passed"),
        ("console.log('Hello World!');", "javascript", "passed"),
        ("public class Main { public static void main(String[] args) {} }", "java", "passed"),
        ("#include <iostream>\nint main() { return 0; }", "cpp", "passed"),
    ]
    
    for code, lang, expected in tests:
        print(f"Testing {lang}...")
        result = execute(code, lang, 5)
        assert result == expected, f"Test failed: {result}"
        print("Passed!")