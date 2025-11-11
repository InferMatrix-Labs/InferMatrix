import paramiko
import json
import time
import sys
import requests
import threading


def load_config(config_path="config.json"):
    """加载JSON配置文件"""
    import json

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def connect_ssh(ssh_config):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if ssh_config.get("key_path"):
        client.connect(
            hostname=ssh_config["hostname"],
            username=ssh_config["username"],
            key_filename=ssh_config["key_path"],
            port=ssh_config.get("port", 22),
        )
    else:
        client.connect(
            hostname=ssh_config["hostname"],
            username=ssh_config["username"],
            password=ssh_config["password"],
            port=ssh_config.get("port", 22),
        )

    return client


def start_vllm_service(ssh_client, test_config):
    backend_config = test_config["backend_config"]
    model_path = backend_config["model_path"]
    tp_size = backend_config["tensor_parallel_size"]
    port = backend_config["port"]
    args = backend_config["args"]

    # 构建VLLM启动命令
    cmd = f"vllm serve {model_path} --tensor-parallel-size={tp_size} --port {port} "
    cmd += f"--gpu-memory-utilization {args.get('gpu-memory-utilization', 0.95)} "
    cmd += f"--max-model-len {args.get('max-model-len', 8192)} "
    cmd += f"--max-num-batched-tokens {args.get('max-num-batched-tokens', 8)} "
    cmd += f"--max-num-seqs {args.get('max-num-seqs', 8)} "
    cmd += "--disable-log-stats --enforce-eage"

    print(f"Starting VLLM service with command:\n{cmd}")

    # 使用screen在后台运行服务，但保留输出
    screen_cmd = f"screen -L -Logfile vllm_log.txt -dmS vllm_service bash -c '{cmd}'"
    stdin, stdout, stderr = ssh_client.exec_command(screen_cmd)

    # 等待screen会话启动
    time.sleep(2)

    # 创建一个标志，用于指示服务是否已准备就绪
    service_ready = False

    # 监控日志文件，直到服务准备就绪
    print("Monitoring VLLM startup logs...")

    # 最大等待时间（秒）
    max_wait_time = 300
    start_time = time.time()

    while not service_ready and (time.time() - start_time) < max_wait_time:
        # 读取日志文件
        stdin, stdout, stderr = ssh_client.exec_command("cat vllm_log.txt")
        log_content = stdout.read().decode()

        # 打印最新的日志内容
        print(log_content)

        # 检查是否包含服务启动完成的标志
        if "Application startup complete" in log_content:
            service_ready = True
            print("\n✅ VLLM service is now ready!")
            break

        # 等待一段时间再检查
        time.sleep(10)

    if not service_ready:
        print("\n❌ Timeout waiting for VLLM service to start.")
        return False

    # 验证API是否可用
    time.sleep(5)  # 给API一点时间完全启动
    api_url = f"http://{ssh_config['hostname']}:{port}/v1/models"
    print(f"Verifying API availability at: {api_url}")

    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ API verification successful!")
            print(f"API Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(
                f"❌ API verification failed with status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print(f"❌ API verification failed with error: {str(e)}")
        return False


# 主程序
try:
    config = load_config()
    ssh_config = config["ssh"]
    test_config = config["tests"][0]  # 使用第一个测试配置

    print(f"Connecting to {ssh_config['hostname']}...")
    ssh_client = connect_ssh(ssh_config)
    print("Connected successfully!")

    success = start_vllm_service(ssh_client, test_config)

    if success:
        print("\nVLLM service is fully operational and API is accessible.")
        print(
            f"API endpoint: http://{ssh_config['hostname']}:{test_config['backend_config']['port']}/v1/completions"
        )
        print("\nWhen finished, you may want to stop the service with:")
        print(
            f"  ssh {ssh_config['username']}@{ssh_config['hostname']} 'pkill -f vllm'"
        )

    # 保持SSH连接打开，直到用户手动终止
    print("\nPress Ctrl+C to close this script (VLLM service will continue running)")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting script. VLLM service remains running on the server.")

except Exception as e:
    print(f"Error: {str(e)}")

finally:
    if "ssh_client" in locals():
        ssh_client.close()
