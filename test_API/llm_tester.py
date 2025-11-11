import requests
import json
import time
import logging
import argparse
import os
from typing import Dict, Any, Optional, List, Tuple
import sys


def setup_logger(log_dir="run_test_API", framework="llm", streaming=False):
    """配置并返回日志记录器"""
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 创建日志文件名，包含框架名称和流式标志
    stream_flag = "stream" if streaming else "normal"
    log_filename = (
        f"{log_dir}/{framework}_{stream_flag}_test_{time.strftime('%Y%m%d_%H%M%S')}.log"
    )

    # 配置日志
    logger = logging.getLogger(f"LLM-Tester-{framework}")
    logger.setLevel(logging.DEBUG)

    # 防止日志记录重复
    if logger.handlers:
        logger.handlers.clear()

    # 添加文件处理器
    file_handler = logging.FileHandler(
        log_filename, encoding="utf-8"
    )  # 配置一下utf-8编码
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


class LLMTester:
    def __init__(
        self, framework: str, url: str, model: str = None, streaming: bool = False
    ):
        """
        初始化LLM测试工具

        Args:
            framework: 框架名称 (ollama, lmstudio, vllm)
            url: API端点URL
            model: 模型名称
            streaming: 是否进行流式测试
        """
        self.framework = framework.lower()
        self.url = url
        self.model = model
        self.streaming = streaming
        self.headers = {"Content-Type": "application/json"}

        # 根据框架设置API端点
        if self.framework == "ollama":
            if not self.url.endswith("/api/generate"):
                self.url = f"{self.url.rstrip('/')}/api/generate"
        elif self.framework == "vllm":
            if not self.url.endswith("/v1/completions"):
                self.url = f"{self.url.rstrip('/')}/v1/completions"
            self.headers["Authorization"] = "Bearer no-key-required"
        elif self.framework == "lmstudio":
            if not self.url.endswith("/v1/completions"):
                self.url = f"{self.url.rstrip('/')}/v1/completions"

        # 设置日志记录器
        self.logger = setup_logger(framework=framework, streaming=streaming)
        self.logger.info(
            f"初始化 {framework} 测试，URL: {url}, 模型: {model}, 流式模式: {streaming}"
        )

    def check_service(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """检查服务是否在线并获取模型信息"""
        try:
            if self.framework == "ollama":
                check_url = self.url.replace("/api/generate", "/api/tags")
                response = requests.get(check_url, timeout=5)
            elif self.framework == "vllm":
                check_url = self.url.replace("/v1/completions", "/v1/models")
                response = requests.get(check_url, timeout=5)
            elif self.framework == "lmstudio":
                check_url = self.url.replace("/v1/completions", "/v1/models")
                response = requests.get(check_url, timeout=5)
            else:
                # 使用简单请求检查服务是否可用
                response = requests.options(self.url, timeout=2)

            if response.status_code < 400:
                response_data = response.json() if response.content else None
                self.logger.info(
                    f"服务检查成功: {json.dumps(response_data, indent=2, ensure_ascii=False) if response_data else 'No content'}"
                )
                return True, response_data

            error_info = {
                "status_code": response.status_code,
                "reason": response.reason,
            }
            self.logger.error(f"服务检查失败: {error_info}")
            return False, error_info

        except requests.exceptions.RequestException as e:
            self.logger.error(f"服务连接失败: {e}")
            return False, {"error": str(e)}

    def format_request_payload(
        self,
        prompt: str,
        max_tokens: int = 50,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """根据不同框架格式化请求数据"""
        if self.framework == "ollama":
            return {
                "model": self.model,
                "prompt": prompt,
                "stream": stream,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
        elif self.framework in ["vllm", "lmstudio"]:
            return {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }
        else:
            # 通用格式
            return {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }

    def test_completion(self, prompt: str, max_tokens: int = 50) -> Dict[str, Any]:
        """测试完成接口并记录返回格式"""
        payload = self.format_request_payload(prompt, max_tokens)
        self.logger.info(
            f"测试完成接口，请求: {json.dumps(payload, ensure_ascii=False)}"
        )

        try:
            start_time = time.time()
            response = requests.post(
                self.url, headers=self.headers, json=payload, timeout=30
            )
            total_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"请求成功，耗时: {total_time:.4f}秒")
                self.logger.info(
                    f"响应格式: {json.dumps(result, indent=2, ensure_ascii=False)}"
                )
                return {
                    "success": True,
                    "time": total_time,
                    "status_code": response.status_code,
                    "response": result,
                }
            else:
                self.logger.error(
                    f"请求失败，状态码: {response.status_code}, 原因: {response.text}"
                )
                return {
                    "success": False,
                    "time": total_time,
                    "status_code": response.status_code,
                    "error": response.text,
                }
        except Exception as e:
            self.logger.error(f"请求异常: {e}")
            return {"success": False, "error": str(e)}

    def test_streaming(self, prompt: str, max_tokens: int = 50) -> Dict[str, Any]:
        """测试流式接口并记录返回格式"""
        payload = self.format_request_payload(prompt, max_tokens, stream=True)
        self.logger.info(
            f"测试流式接口，请求: {json.dumps(payload, ensure_ascii=False)}"
        )

        try:
            start_time = time.time()
            response = requests.post(
                self.url, headers=self.headers, json=payload, stream=True, timeout=30
            )

            if response.status_code == 200:
                first_chunk_time = None
                last_content_chunk_time = None  # 记录最后一个内容块的时间
                chunks = []
                content_chunks = []  # 只包含实际内容的块
                complete_text = ""
                token_count = 0

                self.logger.info("开始接收流式响应...")

                for i, chunk in enumerate(response.iter_lines()):
                    if chunk:
                        current_time = time.time()

                        # 记录首个响应的时间
                        if first_chunk_time is None:
                            first_chunk_time = current_time
                            self.logger.info(
                                f"首个响应到达 (TTFT): {first_chunk_time - start_time:.4f}秒"
                            )

                        try:
                            chunk_text = chunk.decode("utf-8")
                            chunk_content = ""
                            is_content_chunk = False  # 标记这个块是否包含内容

                            # 记录所有原始块数据
                            self.logger.debug(f"块 {i}: {chunk_text}")

                            # 处理不同框架的流式格式
                            if self.framework == "ollama":
                                # Ollama格式: JSON
                                chunk_data = json.loads(chunk_text)
                                if "response" in chunk_data:
                                    chunk_content = chunk_data["response"]
                                    complete_text += chunk_content
                                    token_count += 1  # 近似计数
                                    is_content_chunk = True
                                    last_content_chunk_time = current_time
                            elif self.framework in ["vllm", "lmstudio"]:
                                # OpenAI兼容格式: data: {...}
                                if chunk_text.startswith("data: "):
                                    chunk_text = chunk_text[6:]
                                if chunk_text.strip() and chunk_text != "[DONE]":
                                    chunk_data = json.loads(chunk_text)
                                    if (
                                        "choices" in chunk_data
                                        and len(chunk_data["choices"]) > 0
                                    ):
                                        if "text" in chunk_data["choices"][0]:
                                            chunk_content = chunk_data["choices"][0][
                                                "text"
                                            ]
                                            complete_text += chunk_content
                                            token_count += 1  # 近似计数
                                            is_content_chunk = True
                                            last_content_chunk_time = current_time
                                        elif (
                                            "delta" in chunk_data["choices"][0]
                                            and "content"
                                            in chunk_data["choices"][0]["delta"]
                                        ):
                                            chunk_content = chunk_data["choices"][0][
                                                "delta"
                                            ]["content"]
                                            complete_text += chunk_content
                                            token_count += 1  # 近似计数
                                            is_content_chunk = True
                                            last_content_chunk_time = current_time

                            chunk_info = {
                                "index": i,
                                "time": current_time - start_time,
                                "content": chunk_text,
                                "extracted_text": chunk_content,
                                "is_content": is_content_chunk,
                            }

                            chunks.append(chunk_info)
                            if is_content_chunk:
                                content_chunks.append(chunk_info)

                        except Exception as e:
                            self.logger.error(f"解析响应块错误: {e}, 块内容: {chunk}")

                total_time = time.time() - start_time
                ttft = first_chunk_time - start_time if first_chunk_time else None

                # 计算实际的TPOT，只考虑内容块
                if (
                    first_chunk_time
                    and last_content_chunk_time
                    and len(content_chunks) > 1
                ):
                    content_generation_time = last_content_chunk_time - first_chunk_time
                    tokens_per_second = (
                        token_count / content_generation_time
                        if content_generation_time > 0
                        else 0
                    )
                    tpot = (
                        1000 / tokens_per_second if tokens_per_second > 0 else 0
                    )  # 转换为每个token的生成时间（ms）
                else:
                    tpot = 0
                    tokens_per_second = 0

                # 最终结果输出
                self.logger.info(f"==============流式请求完成==============")
                self.logger.info(
                    f"流式请求完成，总耗时: {content_generation_time:.4f}秒"
                )
                self.logger.info(
                    f"结束响应到达，结尾耗时: {total_time-content_generation_time:.4f}秒"
                )
                self.logger.info(f"TTFT (首个令牌延迟): {ttft:.4f} seconds")
                self.logger.info(f"TPOT (令牌生成间隔): {tpot:.2f} millisecond")
                self.logger.info(
                    f"Throughput (令牌生成速率): {tokens_per_second:.2f} tokens/second"
                )
                self.logger.info(
                    f"Token_count (令牌生成数量): {token_count:.2f} tokens"
                )
                self.logger.info(
                    f"总共接收 {len(chunks)} 个数据块，其中内容块 {len(content_chunks)} 个"
                )
                self.logger.info(f"完整文本: {complete_text}")

                # 保存所有块的详细信息
                chunks_filename = f"run_test_API/{self.framework}_stream_chunks_{time.strftime('%Y%m%d_%H%M%S')}.json"
                with open(chunks_filename, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, indent=2, ensure_ascii=False)
                self.logger.info(f"所有流式响应块详情已保存到: {chunks_filename}")

                return {
                    "success": True,
                    "total_time": total_time,
                    "ttft": ttft,
                    "tpot": tpot,  # 每个token的生成时间（ms）
                    "throughput": tokens_per_second,  # 吞吐量（tokens/second）
                    "chunk_count": len(chunks),
                    "content_chunk_count": len(content_chunks),
                    "complete_text": complete_text,
                    "token_count": token_count,  # 实际token数量
                    "chunks_file": chunks_filename,
                }

            else:
                self.logger.error(
                    f"流式请求失败，状态码: {response.status_code}, 原因: {response.text}"
                )
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text,
                }
        except Exception as e:
            self.logger.error(f"流式请求异常: {e}")
            return {"success": False, "error": str(e)}

    def run_full_test(
        self, prompt: str = "The capital of France is", max_tokens: int = 50
    ) -> Dict[str, Any]:
        """运行完整测试，包括服务检查、普通请求和流式请求"""
        results = {
            "framework": self.framework,
            "url": self.url,
            "model": self.model,
            "streaming_mode": self.streaming,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 检查服务
        self.logger.info(f"开始检查服务 {self.url} 是否可用...")
        service_online, service_info = self.check_service()
        results["service_status"] = {"online": service_online, "info": service_info}

        if service_online:
            # 根据模式选择测试方法
            if self.streaming:
                self.logger.info("进行流式接口测试...")
                streaming_result = self.test_streaming(prompt, max_tokens)
                results["streaming_test"] = streaming_result

                if streaming_result.get("success"):
                    self.logger.info(
                        f"流式接口测试成功，TTFT: {streaming_result.get('ttft', 'N/A'):.4f}秒，"
                        f"TPOT: {streaming_result.get('tpot', 'N/A'):.2f} 毫秒，"
                        f"Throughput: {streaming_result.get('throughput', 'N/A'):.2f} 个/秒"
                    )
                else:
                    self.logger.warning("流式接口测试失败")
            else:
                self.logger.info("进行普通完成接口测试...")
                completion_result = self.test_completion(prompt, max_tokens)
                results["completion_test"] = completion_result

                if completion_result.get("success"):
                    self.logger.info(
                        f"完成接口测试成功，耗时: {completion_result.get('time', 'N/A'):.4f}秒"
                    )
                else:
                    self.logger.warning("完成接口测试失败")
        else:
            self.logger.error(f"服务 {self.url} 不可用，无法进行进一步测试")

            # 统一保存结果
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            stream_flag = "stream" if self.streaming else "normal"
            result_filename = (
                f"run_test_API/llm_test_{self.framework}_{stream_flag}_{timestamp}.json"
            )

            # 如果是流式测试，将chunks信息直接包含在results中
            if (
                self.streaming
                and "streaming_test" in results
                and results["streaming_test"].get("success")
            ):
                results["streaming_test"]["chunks"] = chunks  # 直接包含chunks数据
                del results["streaming_test"]["chunks_file"]  # 删除原来的文件引用

            os.makedirs("run_test_API", exist_ok=True)
            with open(result_filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"详细测试结果已保存到 {result_filename}")

        return results

    def run_performance_test(self, prompt: str, max_tokens: int = 50) -> Dict[str, Any]:
        """
        运行性能测试并返回关键性能指标

        Args:
            prompt: 测试提示词
            max_tokens: 最大生成token数

        Returns:
            Dict包含以下性能指标：
            - success: 测试是否成功
            - ttft: 首个token响应时间（秒）
            - tpot: 每个token生成时间（毫秒）
            - throughput: 吞吐量（tokens/second）
            - token_count: 生成的token数量
            - total_time: 总耗时（秒）
        """
        if self.streaming:
            result = self.test_streaming(prompt, max_tokens)
        else:
            result = self.test_completion(prompt, max_tokens)

        if result.get("success"):
            return {
                "success": True,
                "ttft": result.get("ttft"),
                "tpot": result.get("tpot"),
                "throughput": result.get("throughput"),
                "token_count": result.get("token_count"),
                "total_time": result.get("total_time"),
            }
        else:
            return {"success": False, "error": result.get("error")}


def main():
    parser = argparse.ArgumentParser(description="LLM服务测试工具")
    parser.add_argument(
        "--framework",
        type=str,
        default="ollama",
        choices=["ollama", "lmstudio", "vllm"],
        help="要测试的框架",
    )
    parser.add_argument("--url", type=str, help="API端点URL")
    parser.add_argument("--model", type=str, help="模型名称")
    parser.add_argument(
        "--prompt", type=str, default="The capital of France is", help="测试提示词"
    )
    parser.add_argument("--max-tokens", type=int, default=128, help="最大生成token数")
    parser.add_argument("--stream", default=True, help="使用流式API进行测试")
    parser.add_argument(
        "--both", action="store_true", default=False, help="同时测试普通API和流式API"
    )

    args = parser.parse_args()

    # 根据框架设置默认值
    if args.model is None:
        if args.framework == "ollama":
            args.model = "deepseek-r1:7b"
            if not args.url:
                args.url = "http://localhost:11434/api/generate"
                # args.url = "http://127.0.0.1:11434/api/generate"
        elif args.framework == "lmstudio":
            args.model = "deepseek-r1-distill-qwen-1.5b@q2_k"
            if not args.url:
                args.url = "http://localhost:1234/v1/completions"
        elif args.framework == "vllm":
            # args.model = "/data1/DeepSeek-R1-Distill/DeepSeek-R1-Distill-Qwen-1.5B"  # 修改为实际模型路径
            args.model = "/data1/DeepSeek-R1-Distill/DeepSeek-R1-Distill-Qwen-32B"  # 修改为实际模型路径
            if not args.url:
                args.url = "http://localhost:8000/v1/completions"

    if args.both:
        # 测试普通API
        print("\n=== 测试普通API接口 ===")
        tester = LLMTester(args.framework, args.url, args.model, streaming=False)
        tester.run_full_test(args.prompt, args.max_tokens)

        # 测试流式API
        print("\n=== 测试流式API接口 ===")
        tester = LLMTester(args.framework, args.url, args.model, streaming=True)
        tester.run_full_test(args.prompt, args.max_tokens)
    else:
        # 根据参数只测试一种API
        tester = LLMTester(args.framework, args.url, args.model, streaming=args.stream)
        tester.run_full_test(args.prompt, args.max_tokens)


if __name__ == "__main__":
    main()
