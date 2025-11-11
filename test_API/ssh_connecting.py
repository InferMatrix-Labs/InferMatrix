import paramiko
import time
import os
import json
from typing import Dict, Any, List, Optional, Tuple
import threading


class SSHManager:
    def __init__(self, config: Dict[str, Any]):
        self.hostname = config.get("hostname")
        self.username = config.get("username")
        self.password = config.get("password")
        self.key_path = config.get("key_path")
        self.port = config.get("port", 22)
        self.local_mode = config.get("local_mode", False)
        self.client = None
        self.connected = False

    def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.key_path:
                key = paramiko.RSAKey.from_private_key_file(self.key_path)
                self.client.connect(
                    self.hostname, port=self.port, username=self.username, pkey=key
                )
            else:
                self.client.connect(
                    self.hostname,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                )

            self.connected = True
            return True
        except Exception as e:
            print(f"SSH连接失败: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()
            self.connected = False

    def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """测试本地框架选项"""
        if self.local_mode:
            import subprocess

            try:
                # 使用subprocess执行命令
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                # 用于存储输出的变量
                stdout_lines = []
                stderr_lines = []

                # 创建线程来读取输出
                def read_stream(stream, lines):
                    for line in stream:
                        lines.append(line)

                stdout_thread = threading.Thread(
                    target=read_stream, args=(process.stdout, stdout_lines)
                )
                stderr_thread = threading.Thread(
                    target=read_stream, args=(process.stderr, stderr_lines)
                )

                stdout_thread.daemon = True
                stderr_thread.daemon = True

                stdout_thread.start()
                stderr_thread.start()

                # 处理超时
                start_time = time.time()
                while process.poll() is None:  # 进程仍在运行
                    if timeout and (time.time() - start_time) > timeout:
                        # 超时处理
                        process.terminate()
                        try:
                            process.wait(timeout=2)  # 给进程一点时间退出
                        except subprocess.TimeoutExpired:
                            process.kill()  # 强制终止
                        # 等待线程结束
                        stdout_thread.join(timeout=0.1)
                        stderr_thread.join(timeout=0.1)
                        stdout_str = "".join(stdout_lines)
                        stderr_str = "".join(stderr_lines)
                        return (
                            -1,
                            stdout_str,
                            stderr_str + f"\n命令执行超时（超过 {timeout} 秒）",
                        )
                    time.sleep(0.1)  # 避免CPU占用过高

                # 等待线程结束
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)

                # 获取输出结果
                stdout_str = "".join(stdout_lines)
                stderr_str = "".join(stderr_lines)

                return process.returncode, stdout_str, stderr_str

            except Exception as e:
                return -1, "", f"命令执行错误: {e}"

            """
            import subprocess
            # Windows特殊处理：转换管道命令
            if '|' in command and os.name == 'nt':
                parts = command.split('|')
                process1 = subprocess.Popen(parts[0].strip(), shell=True,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True)
                process2 = subprocess.Popen(parts[1].strip(), shell=True,
                                            stdin=process1.stdout,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True)
                stdout, stderr = process2.communicate(timeout=timeout)
                return process2.returncode, stdout, stderr
            else:
                result = subprocess.run(command, shell=True,
                                        capture_output=True,
                                        text=True,
                                        timeout=timeout)
                return result.returncode, result.stdout, result.stderr
            """
        else:
            """
            执行SSH命令

            Args:
                command: 要执行的命令
                timeout: 命令超时时间(秒)

            Returns:
                Tuple包含 (退出码, 标准输出, 标准错误)
            """
            if not self.connected:  # 未成功连接则重新连接
                if not self.connect():  # 重新连接未成功则返回-1表示异常退出
                    return -1, "", "SSH连接失败"

            try:
                stdin, stdout, stderr = self.client.exec_command(
                    command, timeout=timeout
                )
                exit_code = stdout.channel.recv_exit_status()
                stdout_str = stdout.read().decode("utf-8")
                stderr_str = stderr.read().decode("utf-8")

                return exit_code, stdout_str, stderr_str
            except Exception as e:
                return -1, "", f"命令执行错误: {e}"

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件到远程服务器"""
        # 只要启动相应远程服务都要先检查是否连接
        if not self.connected:
            if not self.connect():
                return False

        try:
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            return True
        except Exception as e:
            print(f"文件上传失败: {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """从远程服务器下载文件"""
        if not self.connected:
            if not self.connect():
                return False

        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            return True
        except Exception as e:
            print(f"文件下载失败: {e}")
            return False


class BackendAdapter:
    """推理后端适配器基类"""

    def __init__(self, ssh_manager: SSHManager):
        self.ssh = ssh_manager

    def start_service(self, config: Dict[str, Any]) -> bool:
        """启动服务"""
        raise NotImplementedError

    def stop_service(self) -> bool:
        """停止服务"""
        raise NotImplementedError

    def check_service(self) -> bool:
        """检查服务状态"""
        raise NotImplementedError

    def get_api_url(self, config: Dict[str, Any]) -> str:
        """获取API URL"""
        raise NotImplementedError


class OllamaAdapter(BackendAdapter):
    """Ollama后端适配器"""

    # Ollama支持的环境变量列表
    SUPPORTED_ENV_VARS = [
        "OLLAMA_DEBUG",
        "OLLAMA_HOST",
        "OLLAMA_KEEP_ALIVE",
        "OLLAMA_MAX_LOADED_MODELS",
        "OLLAMA_MAX_QUEUE",
        "OLLAMA_MODELS",
        "OLLAMA_NUM_PARALLEL",
        "OLLAMA_NOPRUNE",
        "OLLAMA_ORIGINS",
        "OLLAMA_SCHED_SPREAD",
        "OLLAMA_TMPDIR",
        "OLLAMA_FLASH_ATTENTION",
        "OLLAMA_LLM_LIBRARY",
    ]

    def start_service(self, config: Dict[str, Any]) -> bool:
        print("\n======== ollama服务启动 ========")
        """
        启动Ollama服务

        Args:
            config: 配置字典，包含:
                - model: 模型名称
                - gpu_ids: GPU ID列表，如 [0,1,2]
                - port: 服务端口
                - env_vars: 环境变量配置 (可选)
                - quantize: 量化方法 (可选)
                - other_args: 其他参数 (可选)

        Returns:
            启动成功返回True，否则返回False
        """
        # 收集所有需要配置的环境变量
        env_vars = {}

        # 处理GPU设置
        if "gpu_ids" in config and config["gpu_ids"]:
            gpu_str = ",".join(map(str, config["gpu_ids"]))
            env_vars["CUDA_VISIBLE_DEVICES"] = gpu_str

        # 处理其他Ollama环境变量
        if "env_vars" in config and isinstance(config["env_vars"], dict):
            for var_name, var_value in config["env_vars"].items():
                if var_name in self.SUPPORTED_ENV_VARS:
                    env_vars[var_name] = var_value

        # 处理NUM_PARALLEL设置 (如果在配置中有指定并且没有在env_vars中设置)
        if "num_parallel" in config and "OLLAMA_NUM_PARALLEL" not in env_vars:
            env_vars["OLLAMA_NUM_PARALLEL"] = str(config["num_parallel"])

        # 处理MAX_LOADED_MODELS设置
        if "max_loaded_models" in config and "OLLAMA_MAX_LOADED_MODELS" not in env_vars:
            env_vars["OLLAMA_MAX_LOADED_MODELS"] = str(config["max_loaded_models"])

        # 如果有任何环境变量需要设置，则需要修改服务配置
        if env_vars:
            bool1 = self._configure_service_with_env_vars(env_vars)
            if not bool1:
                return False

        # 构建启动命令
        model = config.get("model", "deepseek-r1:1.5b")
        port = config.get("port", 11434)

        # 检查模型是否已经下载 - 兼容Windows
        print(f"检查模型 {model} 是否已经下载,end='\t'")
        if self.ssh.local_mode and os.name == "nt":
            # Windows系统
            code, out, err = self.ssh.execute_command(f"ollama list {model}")
        else:
            # Linux/macOS
            code, out, err = self.ssh.execute_command(f"ollama list | grep {model}")
        if code != 0 or model not in out:
            print(f"模型 {model} 需要拉取，开始下载...")
            self.ssh.execute_command(f"ollama pull {model}")
        else:
            print(f"已下载")

        # 启动服务 - Windows兼容
        if self.ssh.local_mode and os.name == "nt":  # Windows系统
            print(
                f"windows上ollama已启动"
            )  # 上面检查模型的'ollama list {model}'指令顺带启动了ollama
        elif not env_vars:
            # Linux/macOS启动命令
            run_cmd = f"nohup ollama serve --port {port} > ollama_serve.log 2>&1 &"

            # 执行命令并检查是否成功
            print(f"执行启动命令: {run_cmd}")
            code, out, err = self.ssh.execute_command(run_cmd)
            if code != 0:
                print(f"Ollama服务启动失败: {err}")
                return False

        # 给服务启动一些时间
        time.sleep(3)

        if self.ssh.local_mode and os.name == "nt":  # Windows系统
            # 清理模型名称用于文件名（Windows文件名限制）
            safe_model = (
                model.replace(":", "_")
                .replace("\\", "_")
                .replace("/", "_")
                .replace("*", "_")
            )
            log_file = f"ollama_run_{safe_model}.log"

            # 在Windows上后台运行命令的替代方案
            # 使用start命令在独立窗口运行，并重定向输出到日志文件
            # cmd = f'start /B cmd /c "ollama run {model} --verbose > {log_file} 2>&1"'
            cmd = f'powershell -Command "ollama run {model} --verbose | Out-File -Encoding UTF8 {log_file}  2>&1"'

            # 执行命令
            exit_code, stdout, stderr = self.ssh.execute_command(cmd)

            if exit_code != 0:
                print(f"Ollama模型启动失败: {stderr}")
                return False

            print(f"Ollama模型 '{model}' 已在后台运行，日志输出到: {log_file}")
            return True
        else:
            # 运行模型 (这会在后台加载模型)
            load_cmd = f"nohup ollama run {model} --verbose > ollama_run_{model.replace(':', '_')}.log 2>&1 &"
            code, out, err = self.ssh.execute_command(load_cmd)
            if code != 0:
                print(f"Ollama模型加载失败: {err}")
                return False

        # 等待模型加载
        time.sleep(10)

        # 增加服务状态检查
        if self.ssh.local_mode and os.name == "nt":  # Windows系统
            code, out, err = self.ssh.execute_command(
                'tasklist /FI "IMAGENAME eq ollama.exe"'
            )
            print(f"Ollama进程检查: out={out}, err={err}")
            return "ollama.exe" in out
        else:
            return self.check_service()
        # return self.check_service()

    def _configure_service_with_env_vars(self, env_vars: Dict[str, str]) -> bool:
        """
        配置Ollama服务的环境变量

        Args:
            env_vars: 要设置的环境变量字典

        Returns:
            配置成功返回True，否则返回False
        """
        print(f"配置Ollama服务环境变量: {env_vars}")

        # 1. 创建用户级服务单元文件（如果不存在）
        service_content = """
    [Unit]
    Description=Ollama Service
    After=network.target

    [Service]
    ExecStart=/usr/local/bin/ollama serve
    Restart=always
    RestartSec=3
    EnvironmentFile=-/etc/ollama/ollama.env

    [Install]
    WantedBy=default.target
    """
        # 创建服务单元文件目录
        code, out, err = self.ssh.execute_command("mkdir -p ~/.config/systemd/user")
        if code != 0:
            print(f"服务目录创建失败: {err}")
            return False

        # 写入服务单元文件
        cmd = f'echo -e "{service_content}" > ~/.config/systemd/user/ollama.service'
        code, out, err = self.ssh.execute_command(cmd)
        if code != 0:
            print(f"服务单元文件创建失败: {err}")
            return False

        # 2. 创建环境变量配置目录
        code, out, err = self.ssh.execute_command(
            "mkdir -p ~/.config/systemd/user/ollama.service.d"
        )
        if code != 0:
            print(f"配置目录创建失败: {err}")
            return False

        # 3. 创建环境变量配置
        env_content = "[Service]\n"
        for var_name, var_value in env_vars.items():
            env_content += f'Environment="{var_name}={var_value}"\n'

        # 写入配置文件
        cmd = f'echo -e "{env_content}" > ~/.config/systemd/user/ollama.service.d/override.conf'
        code, out, err = self.ssh.execute_command(cmd)
        if code != 0:
            print(f"配置文件写入失败: {err}")
            return False

        # 4. 确保用户级服务已启用
        code, out, err = self.ssh.execute_command(
            "systemctl --user enable ollama.service"
        )
        if code != 0:
            print(f"启用用户服务失败: {err}")
            return False

        # 5. 重新加载用户级systemd配置
        code, out, err = self.ssh.execute_command("systemctl --user daemon-reload")
        if code != 0:
            print(f"重新加载用户级systemd配置失败: {err}")
            return False

        # 6. 重启用户级Ollama服务
        code, out, err = self.ssh.execute_command(
            "systemctl --user restart ollama.service"
        )
        if code != 0:
            print(f"重启用户级Ollama服务失败: {err}")
            return False

        # 7. 等待服务重启
        time.sleep(5)
        """
        # 添加验证步骤
        print("验证环境变量配置...")
        # 1. 检查服务配置文件内容
        code, out, err = self.ssh.execute_command("cat ~/.config/systemd/user/ollama.service.d/override.conf")
        if code == 0:
            print("服务配置文件内容:")
            print(out)
        else:
            print(f"无法读取配置文件: {err}")
        
        # 2. 检查当前服务的环境变量
        code, out, err = self.ssh.execute_command("systemctl --user show ollama.service --property=Environment")
        if code == 0:
            print("当前服务环境变量:")
            print(out)
        else:
            print(f"无法获取服务环境变量: {err}")
        """
        return True

    def stop_service(self) -> bool:
        """停止Ollama服务"""
        if self.ssh.local_mode and os.name == "nt":  # Windows系统
            code, out, err = self.ssh.execute_command('taskkill /F /IM "ollama*" /T')

            # 检查服务是否已经停止
            for _ in range(5):  # 尝试5次
                code, out, err = self.ssh.execute_command(
                    'tasklist /FI "IMAGENAME eq ollama.exe"'
                )
                if code != 0:  # 没有找到进程，说明已停止
                    return True
                time.sleep(1)
            return True

        else:  # 使用pkill终止所有Ollama进程
            code, out, err = self.ssh.execute_command("pkill -f ollama")

            # 检查服务是否已经停止
            for _ in range(5):  # 尝试5次
                code, out, err = self.ssh.execute_command("pgrep -f ollama")
                if code != 0:  # 没有找到进程，说明已停止
                    return True
                time.sleep(1)

            # 如果普通终止失败，强制终止
            self.ssh.execute_command("pkill -9 -f ollama")
            return True

    def check_service(self) -> bool:
        """检查Ollama服务状态"""
        code, out, err = self.ssh.execute_command("pgrep -f 'ollama serve'")
        return code == 0

    def get_api_url(self, config: Dict[str, Any]) -> str:
        """获取Ollama API URL"""
        port = config.get("port", 11434)
        return f"http://{self.ssh.hostname}:{port}/api/generate"


class VLLMAdapter(BackendAdapter):
    """VLLM后端适配器"""

    # VLLM 支持的命令行参数
    SUPPORTED_ARGS = [
        "tensor-parallel-size",
        "gpu-memory-utilization",
        "max-num-batched-tokens",
        "max-num-partial-prefills",
        "swap-space",
        "max-num-seqs",
        "max-num-batched-tokens",
        "max-model-len",
        "max-batch-size",
        "max-tokens",
        "quantization",
        "dtype",
        "enforce-eager",
        "worker-use-ray",
        "block-size",
        "port",
        "host",
        "disable-log-requests",
        "disable-log-stats",
    ]

    def start_service(self, config: Dict[str, Any]) -> bool:
        """
        启动VLLM服务

        Args:
            config: 配置字典，包含:
                - model_path: 模型路径
                - working_dir: VLLM工作目录 (可选)
                - tensor_parallel_size: 张量并行大小 (可选)
                - gpu_ids: GPU ID列表 (可选)
                - use_vllm_serve: 是否使用vllm serve命令 (可选，默认True)
                - args: 其他命令行参数 (可选)

        Returns:
            启动成功返回True，否则返回False
        """
        # 处理配置项
        model_path = config.get(
            "model_path", "/data1/DeepSeek-R1-Distill/DeepSeek-R1-Distill-Qwen-32B"
        )
        working_dir = config.get("working_dir", "~/vllm_test/vllm/benchmarks")
        # 解决 ~ 路径问题
        if working_dir.startswith("~"):
            code, home_dir, _ = self.ssh.execute_command("echo $HOME")
            if code == 0 and home_dir.strip():
                working_dir = working_dir.replace("~", home_dir.strip())

        tensor_parallel_size = config.get("tensor_parallel_size", 1)
        gpu_ids = config.get("gpu_ids", None)
        use_vllm_serve = config.get("use_vllm_serve", True)
        port = config.get("port", 8000)

        # 存储当前活动配置
        self.active_config = config.copy()
        self.active_config["port"] = port

        # 先停止现有服务
        self.stop_service()

        # 确保工作目录存在
        code, out, err = self.ssh.execute_command(f"mkdir -p {working_dir}")
        if code != 0:
            print(f"创建工作目录失败: {err}")
            return False

        # 处理目录切换
        cd_cmd = f"cd {working_dir}"

        # 构造环境变量部分
        env_vars = ""
        if gpu_ids:
            gpu_str = ",".join(map(str, gpu_ids))
            env_vars = f"CUDA_VISIBLE_DEVICES={gpu_str}"

        # 构建基本命令
        if use_vllm_serve:
            # 直接使用vllm serve命令
            cmd = f"vllm serve {model_path}"
        else:
            # 使用python模块方式
            cmd = f"python -m vllm.entrypoints.openai.api_server --model {model_path}"

        # if config.get("wsl") == True:
        #    cmd = f"/home/lichao1213/.venv/bin/python -m vllm.entrypoints.openai.api_server --model {model_path}"

        # 添加基本参数
        cmd += f" --tensor-parallel-size={tensor_parallel_size}"
        cmd += f" --port {port}"

        # 添加其他参数
        if "args" in config and isinstance(config["args"], dict):
            for arg_name, arg_value in config["args"].items():
                if arg_name in self.SUPPORTED_ARGS:
                    if arg_value is True:  # 处理布尔标志
                        cmd += f" --{arg_name}"
                    elif arg_value is not None:  # 跳过None值
                        cmd += f" --{arg_name}={arg_value}"

        # 使用source加载环境变量，确保PATH等环境设置正确
        source_cmd = "source ~/.bashrc && "

        if config.get("wsl-venv") == True:
            source_cmd = "source .venv/bin/activate &&"

        # 确保日志目录存在
        log_file = f"{working_dir}/vllm_server_{port}.log"

        # 组合完整命令 - 使用 && 确保命令按顺序执行
        if env_vars:
            full_cmd = f"{source_cmd} {cd_cmd} && {env_vars} {cmd}"
        else:
            full_cmd = f"{source_cmd} {cd_cmd} && {cmd}"

        # 使用nohup在后台运行，确保输出重定向到日志文件
        run_cmd = f"nohup bash -c '{full_cmd}' > {log_file} 2>&1 &"

        print(f"启动VLLM服务，执行命令: {run_cmd}")

        # 执行命令
        code, out, err = self.ssh.execute_command(run_cmd)
        print(f"命令执行结果 - 代码: {code}, 输出: '{out}', 错误: '{err}'")

        if code != 0:
            print(f"VLLM服务启动命令执行失败: {err}")
            return False
        """
        else:
            # 使用绝对路径到虚拟环境的Python解释器
            venv_python = ".venv/bin/python"

            # 构建命令
            cmd1 = f"{venv_python} -m vllm.entrypoints.openai.api_server"
            cmd1 += f" --model {model_path}"
            cmd1 += f" --tensor-parallel-size={tensor_parallel_size}"
            cmd1 += f" --port {port}"
            cmd1 += " --enforce-eager"  # 强制使用 eager 模式
            # 添加其他参数
            if "args" in config and isinstance(config["args"], dict):
                for arg_name, arg_value in config["args"].items():
                    if arg_name in self.SUPPORTED_ARGS:
                        if arg_value is True:  # 处理布尔标志
                            cmd1 += f" --{arg_name}"
                        elif arg_value is not None:  # 跳过None值
                            cmd1 += f" --{arg_name}={arg_value}"

            # 完整命令
            run_cmd1 = f"nohup {cmd1} > '{log_file}' 2>&1 &"

            print(f"执行启动命令: {run_cmd1}")
            code, out, err = self.ssh.execute_command(run_cmd1)
            print(f"命令执行结果 - 代码: {code}, 输出: '{out}', 错误: '{err}'")
            if code != 0:
                print(f"VLLM服务启动命令执行失败: {err}")
                return False
        """

        # 检查进程是否成功启动
        time.sleep(5)  # 等待进程启动，给予更多时间
        code, out, err = self.ssh.execute_command("pgrep -f 'vllm'")
        if code != 0:
            print("VLLM进程未能启动，查看日志:")
            self._print_log(log_file)
            return False
        else:
            print(f"VLLM进程已启动，进程ID: {out.strip()}")
            print("现在等待模型加载和API准备就绪...")

        # 等待服务启动 - 增加最大等待时间，因为模型加载可能很慢
        print("等待VLLM服务完全启动 (可能需要几分钟)...")
        max_wait_time = 600  # 最多等待10分钟
        check_interval = 20  # 每20秒检查一次

        for i in range(0, max_wait_time, check_interval):
            # 每次迭代都确认进程仍在运行
            code, out, err = self.ssh.execute_command("pgrep -f 'vllm'")
            if code != 0:
                print("VLLM进程已终止，启动失败。查看日志:")
                self._print_log(log_file)
                return False

            # 检查API是否响应
            if self._is_api_ready(port):
                print(f"VLLM服务已成功启动 (耗时约 {i} 秒)")
                return True

            # 查找日志中的成功启动标记
            if self._check_log_for_startup_complete(log_file):
                print(f"从日志中检测到VLLM服务已完成启动 (耗时约 {i} 秒)")
                return True

            # 打印等待消息和部分日志
            print(
                f"仍在等待VLLM服务启动... (已等待 {i} 秒，继续等待 {check_interval} 秒)"
            )

            # 只在某些时间点打印日志，减少输出量
            if i % 60 == 0:  # 每分钟打印一次详细日志
                self._print_log(log_file, lines=15)
                print(f"进程状态: {out.strip()}")

                # 检查GPU占用情况，确认模型是否正在加载
                self._check_gpu_usage()

            time.sleep(check_interval)

        print("VLLM服务启动超时，查看最后的日志:")
        self._print_log(log_file, lines=50)
        return False

    def _build_windows_command(self, config):
        # 构建适合本地系统的命令
        if os.name == "nt":  # Windows系统
            return f"start /B vllm serve {config['model_path']}"
        else:  # Linux/macOS
            return f"nohup vllm serve {config['model_path']} &"

    def _is_api_ready(self, port):
        """检查API是否准备就绪"""
        # 使用curl检查API状态
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}/v1/models"
        code, out, err = self.ssh.execute_command(cmd)

        if code == 0 and out.strip() == "200":
            print(f"API检查成功: 返回状态码 {out.strip()}")
            return True
        else:
            print(f"API尚未就绪: {err if err else '未返回成功状态码'}")
            return False

    def _check_log_for_startup_complete(self, log_file):
        """检查日志中是否包含启动完成的信息"""
        cmd = f"grep -E 'Application startup complete|GET /v1/models HTTP/1.1. 200 OK' {log_file}"
        code, out, err = self.ssh.execute_command(cmd)

        if code == 0 and out.strip():
            print(f"在日志中找到启动完成标记: {out.strip()}")
            return True
        return False

    def _check_gpu_usage(self):
        """检查GPU使用情况，帮助确认模型是否正在加载"""
        self.ssh.execute_command(
            "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv"
        )

    def _print_log(self, log_file, lines=20):
        """打印日志文件内容"""
        # 先检查文件是否存在
        code, _, _ = self.ssh.execute_command(f"test -f {log_file}")
        if code != 0:
            print(f"日志文件 {log_file} 不存在")
            return

        # 打印文件内容
        code, out, err = self.ssh.execute_command(f"tail -n {lines} {log_file}")
        if code == 0:
            print(f"日志内容 (最后 {lines} 行):")
            print("-" * 50)
            print(out)
            print("-" * 50)
        else:
            print(f"无法读取日志文件: {err}")

    def stop_service(self) -> bool:
        """停止VLLM服务"""
        print("正在停止VLLM服务...")

        # 获取并显示当前运行的VLLM进程
        code, out, err = self.ssh.execute_command("ps aux | grep vllm | grep -v grep")
        if code == 0 and out.strip():
            print(f"当前运行的VLLM进程:\n{out}")
        else:
            print("没有找到正在运行的VLLM进程")
            return True

        # 尝试终止vllm相关进程
        code, out, err = self.ssh.execute_command(
            "pkill -f 'vllm.entrypoints.openai.api_server'"
        )
        print(f"终止API服务器进程结果: 代码={code}, 输出='{out}', 错误='{err}'")

        code, out, err = self.ssh.execute_command("pkill -f 'vllm serve'")
        print(f"终止VLLM服务进程结果: 代码={code}, 输出='{out}', 错误='{err}'")

        # 检查服务是否已经停止
        for i in range(5):  # 尝试5次
            code, out, err = self.ssh.execute_command("pgrep -f 'vllm'")
            if code != 0:  # 没有找到进程，说明已停止
                print("VLLM服务已停止")
                return True

            if i > 0:  # 第一次检查失败后显示进程信息
                print(f"VLLM进程仍在运行 (尝试 {i + 1}/5): {out.strip()}")

            time.sleep(2)  # 增加等待时间

        # 如果普通终止失败，强制终止
        print("使用强制终止VLLM服务...")
        code, out, err = self.ssh.execute_command("pkill -9 -f 'vllm'")
        print(f"强制终止结果: 代码={code}, 输出='{out}', 错误='{err}'")

        time.sleep(2)  # 增加等待时间

        # 最后检查一次
        code, out, err = self.ssh.execute_command("pgrep -f 'vllm'")
        if code != 0:
            print("VLLM服务已成功停止")
            return True
        else:
            print(f"警告: 无法完全停止VLLM服务, 进程ID: {out.strip()}")
            return False

    def check_service(self, port=None) -> bool:
        """检查VLLM服务状态"""
        # 确定要检查的端口
        if port is None:
            port = 8000  # 默认端口
            if hasattr(self, "active_config") and self.active_config:
                port = self.active_config.get("port", 8000)

        # 检查进程是否在运行
        code, out, err = self.ssh.execute_command("pgrep -f 'vllm'")
        process_running = code == 0
        if not process_running:
            print("VLLM进程未运行")
            return False

        # 检查API是否响应
        return self._is_api_ready(port)

    def get_api_url(self, config: Dict[str, Any]) -> str:
        """获取VLLM API URL"""
        port = config.get("port", 8000)
        return f"http://{self.ssh.hostname}:{port}/v1/completions"


class LMStudioAdapter(BackendAdapter):
    """LMStudio后端适配器"""

    def start_service(self, config: Dict[str, Any]) -> bool:
        """
        启动LMStudio服务

        Args:
            config: 配置字典，包含:
                - model_path: 模型路径
                - port: 服务端口
                - gpu_ids: GPU ID列表 (可选)
                - other_args: 其他参数 (可选)

        Returns:
            启动成功返回True，否则返回False
        """
        # LMStudio命令行模式启动
        # 注意：这里需要根据LMStudio的实际命令行接口进行调整
        model_path = config.get("model_path", "/models/deepseek-r1-distill-qwen")
        port = config.get("port", 1234)
        gpu_ids = config.get("gpu_ids", None)

        # 构建环境变量
        env_vars = ""
        if gpu_ids:
            gpu_str = ",".join(map(str, gpu_ids))
            env_vars = f"CUDA_VISIBLE_DEVICES={gpu_str}"

        # 构建启动命令
        cmd = f"{env_vars} lmstudio-server --model {model_path} --port {port}"

        # 添加其他参数
        other_args = config.get("other_args", "")
        if other_args:
            cmd += f" {other_args}"

        # 在后台运行
        cmd = f"nohup {cmd} > lmstudio_server.log 2>&1 &"

        # 先停止现有服务
        self.stop_service()

        # 执行命令
        code, out, err = self.ssh.execute_command(cmd)
        if code != 0:
            print(f"LMStudio服务启动失败: {err}")
            return False

        # 等待服务启动
        for _ in range(30):  # 最多等待30秒
            if self.check_service():
                return True
            time.sleep(1)

        return False

    def stop_service(self) -> bool:
        """停止LMStudio服务"""
        # 使用pkill终止所有LMStudio进程
        code, out, err = self.ssh.execute_command("pkill -f lmstudio-server")

        # 检查服务是否已经停止
        for _ in range(5):  # 尝试5次
            code, out, err = self.ssh.execute_command("pgrep -f lmstudio-server")
            if code != 0:  # 没有找到进程，说明已停止
                return True
            time.sleep(1)

        # 如果普通终止失败，强制终止
        self.ssh.execute_command("pkill -9 -f lmstudio-server")
        return True

    def check_service(self) -> bool:
        """检查LMStudio服务状态"""
        code, out, err = self.ssh.execute_command("pgrep -f lmstudio-server")
        return code == 0

    def get_api_url(self, config: Dict[str, Any]) -> str:
        """获取LMStudio API URL"""
        port = config.get("port", 1234)
        return f"http://{self.ssh.hostname}:{port}/v1/completions"


class ServiceManager:
    """服务管理类，负责不同后端的生命周期管理"""

    def __init__(self, ssh_config: Dict[str, Any]):
        """
        初始化服务管理器

        Args:
            ssh_config: SSH连接配置，包含:
                - hostname: 服务器主机名
                - username: 用户名
                - password: 密码 (可选)
                - key_path: 密钥路径 (可选)
                - port: SSH端口 (可选)
        """
        """
        self.ssh_manager = SSHManager(
            hostname=ssh_config.get("hostname"),
            username=ssh_config.get("username"),
            password=ssh_config.get("password"),
            key_path=ssh_config.get("key_path"),
            port=ssh_config.get("port", 22)
        )
        """
        self.ssh_manager = SSHManager(ssh_config)  # 传递整个配置字典

        # 建立SSH连接
        if ssh_config.get("local_mode") == False:
            if not self.ssh_manager.connect():
                raise Exception("无法连接到服务器，请检查SSH配置")

        # 初始化后端适配器
        self.adapters = {
            "ollama": OllamaAdapter(self.ssh_manager),
            "vllm": VLLMAdapter(self.ssh_manager),
            "lmstudio": LMStudioAdapter(self.ssh_manager),
        }

        # 当前活动的后端
        self.active_backend = None
        self.active_config = None

    def __del__(self):
        """析构函数，确保SSH连接关闭"""
        if self.ssh_manager:
            self.ssh_manager.disconnect()

    def deploy_service(self, backend: str, config: Dict[str, Any]) -> bool:
        """
        部署指定后端服务

        Args:
            backend: 后端名称 (ollama, vllm, lmstudio)
            config: 后端配置

        Returns:
            部署成功返回True，否则返回False
        """
        if backend not in self.adapters:
            print(f"不支持的后端: {backend}")
            return False

        # 如果当前有活动的后端，先停止它
        if self.active_backend and self.active_backend != backend:
            self.stop_service()

        # 启动新后端
        adapter = self.adapters[backend]
        success = adapter.start_service(config)

        if success:
            self.active_backend = backend
            self.active_config = config
            print(f"{backend} 服务已成功启动")
        else:
            print(f"{backend} 服务启动失败")

        return success

    def stop_service(self) -> bool:
        """停止当前活动的服务"""
        if not self.active_backend:
            print("没有活动的服务需要停止")
            return True

        adapter = self.adapters[self.active_backend]
        success = adapter.stop_service()

        if success:
            print(f"{self.active_backend} 服务已停止")
            self.active_backend = None
            self.active_config = None
        else:
            print(f"{self.active_backend} 服务停止失败")

        return success

    def check_service(self) -> bool:
        """检查当前服务状态"""
        if not self.active_backend:
            print("没有活动的服务")
            return False

        adapter = self.adapters[self.active_backend]
        return adapter.check_service()

    def get_api_url(self) -> Optional[str]:
        """获取当前活动服务的API URL"""
        if not self.active_backend or not self.active_config:
            print("没有活动的服务")
            return None

        adapter = self.adapters[self.active_backend]
        return adapter.get_api_url(self.active_config)

    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """执行自定义SSH命令"""
        return self.ssh_manager.execute_command(command)

    def get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息"""
        code, out, err = self.ssh_manager.execute_command(
            "nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits"
        )

        if code != 0:
            return {"error": f"获取GPU信息失败: {err}"}

        gpu_info = []
        for line in out.strip().split("\n"):
            if line:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpu_info.append(
                        {
                            "index": int(parts[0]),
                            "name": parts[1],
                            "memory_total": float(parts[2]),
                            "memory_used": float(parts[3]),
                            "memory_free": float(parts[4]),
                            "utilization": float(parts[5]),
                        }
                    )

        return {"gpus": gpu_info}
