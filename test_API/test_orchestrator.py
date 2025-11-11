import os
import json
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

# 导入之前实现的模块
from ssh_connecting import ServiceManager
from llm_tester import LLMTester  # 您现有的测试类


class TestConfig:
    """测试配置类"""

    def __init__(self, config_path: str = None):
        """
        初始化测试配置

        Args:
            config_path: 配置文件路径 (可选)
        """
        self.config = {
            "ssh": {
                "local_mode": False,
                "hostname": "localhost",
                "username": "user",
                "password": None,
                "key_path": "~/.ssh/id_rsa",
                "port": 22,
            },
            "tests": [],
            "prompts": [
                "The capital of France is",
                "Write a short story about a robot learning to feel emotions",
            ],
            "max_tokens": 128,
            "result_dir": "results",
            "default_repeat": 1,
            "test_param": ""
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)

    def save(self, path: str):
        """保存配置到文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def add_test(self, test_config: Dict[str, Any]):
        """添加测试配置"""
        self.config["tests"].append(test_config)

    def get_ssh_config(self) -> Dict[str, Any]:
        """获取SSH配置"""
        return self.config["ssh"]

    def get_tests(self) -> List[Dict[str, Any]]:
        """获取所有测试配置"""
        return self.config["tests"]

    def get_prompts(self) -> List[str]:
        """获取测试提示"""
        return self.config["prompts"]

    def get_max_tokens(self) -> int:
        """获取最大token数"""
        return self.config.get("max_tokens", 128)

    def get_result_dir(self) -> str:
        """获取结果目录"""
        return self.config.get("result_dir", "results")

    def get_localmode(self) -> bool:
        """获取本地模式是否开启"""
        return self.config["ssh"]["local_mode"]
    
    def get_test_param(self) -> str:
        """获取被测试的参数名"""
        return self.config["test_param"]


class TestOrchestrator:
    """测试编排器，管理整个测试流程"""

    def __init__(self, config_path: str = None):
        """
        初始化测试编排器

        Args:
            config_path: 配置文件路径 (可选)
        """
        self.config = TestConfig(config_path)
        self.service_manager = None
        self.results = []
        self.run_timestamp = time.strftime("%Y%m%d_%H%M%S")  # 记录运行时间戳
        self.run_dir = None  # 测试运行目录

    def initialize(self):
        """初始化服务管理器"""
        ssh_config = self.config.get_ssh_config()
        try:
            self.service_manager = ServiceManager(ssh_config)
            if ssh_config["local_mode"] == False:
                print(f"成功连接到服务器 {ssh_config['hostname']}")
            else:
                print("测试本地框架")
            return True
        except Exception as e:
            print(f"初始化服务管理器失败: {e}")
            return False

    def run_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个测试

        Args:
            test_config: 测试配置，包含:
                - name: 测试名称
                - backend: 后端名称 (ollama, vllm, lmstudio)
                - backend_config: 后端配置
                - streaming: 是否使用流式API
                - repeat: 重复次数

        Returns:
            测试结果
        """
        name = test_config.get("name", "unnamed_test")
        backend = test_config.get("backend")
        backend_config = test_config.get("backend_config", {})
        streaming = test_config.get("streaming", True)
        repeat = test_config.get("repeat", 1)

        print(f"\n开始测试: {name}")
        print(f"后端: {backend}")
        print(f"配置: {json.dumps(backend_config, indent=2, ensure_ascii=False)}")

        # 部署服务
        if not self.service_manager.deploy_service(backend, backend_config):
            return {"name": name, "success": False, "error": "服务部署失败"}

        # 获取API URL
        api_url = self.service_manager.get_api_url()
        if not api_url:
            return {"name": name, "success": False, "error": "无法获取API URL"}

        # 准备测试参数
        model = backend_config.get("model", backend_config.get("model_path", "unknown"))
        prompts = self.config.get_prompts()
        max_tokens = self.config.get_max_tokens()

        # 创建测试器
        tester = LLMTester(backend, api_url, model, streaming=streaming)

        # 运行测试
        test_results = []
        for i in range(repeat):
            print(f"第 {i + 1}/{repeat} 轮测试...")

            for j, prompt in enumerate(prompts):
                print(f"提示 {j + 1}/{len(prompts)}: {prompt[:30]}...")

                # 运行性能测试
                result = tester.run_performance_test(prompt, max_tokens)

                if result.get("success"):
                    result.update(
                        {
                            "prompt_id": j,
                            "prompt": prompt,
                            "round": i,
                            "timestamp": time.time(),
                        }
                    )
                    test_results.append(result)
                    print(
                        f"TTFT: {result.get('ttft', 'N/A'):.4f}秒, TPOT: {result.get('tpot', 'N/A'):.2f}毫秒"
                    )
                else:
                    print(f"测试失败: {result.get('error')}")

        test_param=self.config.get_test_param()

        # 计算汇总统计
        summary_stats = {}
        if test_param:
            param=backend_config.get(test_param,"no")
            if param=="no":
                args=backend_config.get("args",{})
                param=args.get(test_param,'no')
            if not param=="no":
                summary_stats[test_param]=param
        if test_results:
            ttfts = [r.get("ttft") for r in test_results if r.get("ttft") is not None]
            tpots = [r.get("tpot") for r in test_results if r.get("tpot") is not None]
            throughputs = [
                r.get("throughput")
                for r in test_results
                if r.get("throughput") is not None
            ]

            if ttfts:
                summary_stats["ttft_avg"] = sum(ttfts) / len(ttfts)
                summary_stats["ttft_min"] = min(ttfts)
                summary_stats["ttft_max"] = max(ttfts)

            if tpots:
                summary_stats["tpot_avg"] = sum(tpots) / len(tpots)
                summary_stats["tpot_min"] = min(tpots)
                summary_stats["tpot_max"] = max(tpots)

            if throughputs:
                summary_stats["throughput_avg"] = sum(throughputs) / len(throughputs)
                summary_stats["throughput_min"] = min(throughputs)
                summary_stats["throughput_max"] = max(throughputs)

        # 打印汇总结果
        if summary_stats:
            print("\n测试结果汇总:")
            if "ttft_avg" in summary_stats:
                print(
                    f"TTFT 平均: {summary_stats['ttft_avg']:.4f}秒, 最小: {summary_stats['ttft_min']:.4f}秒, 最大: {summary_stats['ttft_max']:.4f}秒"
                )
            if "tpot_avg" in summary_stats:
                print(
                    f"TPOT 平均: {summary_stats['tpot_avg']:.2f}毫秒, 最小: {summary_stats['tpot_min']:.2f}毫秒, 最大: {summary_stats['tpot_max']:.2f}毫秒"
                )
            if "throughput_avg" in summary_stats:
                print(
                    f"吞吐量 平均: {summary_stats['throughput_avg']:.2f}个/秒, 最小: {summary_stats['throughput_min']:.2f}个/秒, 最大: {summary_stats['throughput_max']:.2f}个/秒"
                )

        # 返回完整结果
        return {
            "name": name,
            "success": True,
            "backend": backend,
            "config": backend_config,
            "streaming": streaming,
            "test_results": test_results,
            "summary": summary_stats,
        }

    def run_all_tests(self):
        """运行所有配置的测试"""
        # 创建运行目录
        result_dir = self.config.get_result_dir()
        self.run_dir = os.path.join(result_dir, f"run_{self.run_timestamp}")
        os.makedirs(self.run_dir, exist_ok=True)

        tests = self.config.get_tests()
        print(f"开始运行 {len(tests)} 个测试...")
        print(f"测试结果将保存到: {self.run_dir}")

        for i, test_config in enumerate(tests):
            print(f"\n[{i + 1}/{len(tests)}] 运行测试: {test_config['name']}")
            result = self.run_test(test_config)
            self.results.append(result)

            # 保存中间结果
            self.save_results()

        print("\n所有测试完成!")

    def save_results(self):
        """保存测试结果"""
        if not self.run_dir:
            result_dir = self.config.get_result_dir()
            self.run_dir = os.path.join(result_dir, f"run_{self.run_timestamp}")
            os.makedirs(self.run_dir, exist_ok=True)

        # 保存原始结果
        result_file = os.path.join(self.run_dir, f"test_results.json")

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"测试结果已保存到: {result_file}")

    def generate_report_unused(self):
        """生成测试报告"""
        if not self.results:
            # 尝试从文件加载结果
            result_dir = self.config.get_result_dir()
            result_files = [f for f in os.listdir(result_dir) if
                            f.startswith("test_results_") and f.endswith(".json")]

            if not result_files:
                print("没有测试结果可供分析")
                return

            # 使用最新的结果文件
            latest_file = sorted(result_files)[-1]
            result_path = os.path.join(result_dir, latest_file)

            with open(result_path, 'r', encoding='utf-8') as f:
                self.results = json.load(f)

        # 准备数据框
        rows = []
        for result in self.results:
            if not result.get("success", False):
                continue

            name = result.get("name", "未命名")
            backend = result.get("backend", "未知")

            for test_result in result.get("test_results", []):
                if test_result.get("success", False):
                    rows.append({
                        "Test": name,
                        "Backend": backend,
                        "Round": test_result.get("round", 0),
                        "Prompt": test_result.get("prompt_id", 0),
                        "TTFT (s)": test_result.get("ttft"),
                        "TPOT (ms)": test_result.get("tpot"),
                        "Throughput (t/s)": test_result.get("throughput"),
                        "Tokens": test_result.get("token_count"),
                        "Total Time (s)": test_result.get("total_time")
                    })

        if not rows:
            print("没有成功的测试结果可供分析")
            return

        # 创建数据框
        df = pd.DataFrame(rows)

        # 生成汇总统计
        summary = df.groupby(["Test", "Backend"]).agg({
            "TTFT (s)": ["mean", "min", "max", "std"],
            "TPOT (ms)": ["mean", "min", "max", "std"],
            "Throughput (t/s)": ["mean", "min", "max", "std"],
            "Tokens": ["mean", "sum"],
            "Total Time (s)": ["mean", "sum"]
        })

        # 保存报告
        result_dir = self.config.get_result_dir()
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # 保存CSV
        csv_path = os.path.join(result_dir, f"report_{timestamp}.csv")
        summary.to_csv(csv_path)

        # 保存详细数据
        detailed_csv = os.path.join(result_dir, f"detailed_{timestamp}.csv")
        df.to_csv(detailed_csv)

        # 生成图表
        self._generate_charts(df, result_dir, timestamp)

        print(f"测试报告已生成:")
        print(f"- 汇总报告: {csv_path}")
        print(f"- 详细数据: {detailed_csv}")
        print(f"- 图表已保存到: {result_dir}")

    def _generate_charts(self, df, run_dir):
        """生成测试图表"""
        # 创建图表目录
        charts_dir = os.path.join(run_dir, "charts")
        os.makedirs(charts_dir, exist_ok=True)

        # 1. TTFT比较图
        plt.figure(figsize=(12, 8))
        ttft_data = df.groupby("Test")["TTFT (s)"].mean().sort_values()
        ttft_data.plot(kind="bar")
        plt.title("Average Time to First Token (TTFT)")
        plt.ylabel("Seconds")
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "ttft_comparison.png"))
        plt.close()  # 关闭图形以释放内存

        # 2. TPOT比较图
        plt.figure(figsize=(12, 8))
        tpot_data = df.groupby("Test")["TPOT (ms)"].mean().sort_values()
        tpot_data.plot(kind="bar")
        plt.title("Average Time Per Output Token (TPOT)")
        plt.ylabel("Milliseconds")
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "tpot_comparison.png"))
        plt.close()

        # 3. 吞吐量比较图
        plt.figure(figsize=(12, 8))
        throughput_data = (
            df.groupby("Test")["Throughput (t/s)"].mean().sort_values(ascending=False)
        )
        throughput_data.plot(kind="bar")
        plt.title("Average Throughput")
        plt.ylabel("Tokens per Second")
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "throughput_comparison.png"))
        plt.close()

        # 4. 箱线图 - TTFT
        plt.figure(figsize=(14, 8))
        sns.boxplot(x="Test", y="TTFT (s)", data=df)
        plt.title("TTFT Distribution by Test")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "ttft_boxplot.png"))
        plt.close()

        # 5. 箱线图 - TPOT
        plt.figure(figsize=(14, 8))
        sns.boxplot(x="Test", y="TPOT (ms)", data=df)
        plt.title("TPOT Distribution by Test")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "tpot_boxplot.png"))
        plt.close()

    def generate_report(self):
        """生成测试报告，将四幅图合并到一张大图中"""
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        from collections import defaultdict

        # 设置中文字体，解决字符显示为方框的问题
        plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial Unicode MS"]
        plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

        # 加载结果数据
        if not self.results and self.run_dir and os.path.exists(self.run_dir):
            result_path = os.path.join(self.run_dir, "test_results.json")
            if os.path.exists(result_path):
                with open(result_path, "r", encoding="utf-8") as f:
                    self.results = json.load(f)
            else:
                print("没有找到测试结果数据，无法生成报告")
                return

        if not self.results:
            print("没有测试结果数据，无法生成报告")
            return

        # 创建报告目录
        report_dir = os.path.join(self.run_dir, "report")
        os.makedirs(report_dir, exist_ok=True)

        # 从配置文件获取用户指定的横坐标参数（test_param）
        test_param = self.config.config.get("test_param", "model")
        print(f"使用测试参数 '{test_param}' 作为横坐标")

        # 按后端分组
        backend_groups = defaultdict(list)
        for result in self.results:
            backend_groups[result["backend"]].append(result)

        # 为每个后端生成单独图表（保留原有功能）
        for backend, results in backend_groups.items():
            # 定义需要绘制的指标
            metrics = {
                "TTFT": ("ttft_avg", "s"),
                "TPOT": ("tpot_avg", "ms"),
                "Throughput": ("throughput_avg", "token/s"),
                "Total Time": ("total_time", "s")
            }

            # 为每个指标绘制单独图表（原有功能）
            for metric_name, (metric_key, y_unit) in metrics.items():
                plt.figure(figsize=(10, 6))
                sns.set_style("whitegrid")

                # 收集每个模型的数据
                model_data = defaultdict(dict)
                for result in results:
                    model_name = result["name"]

                    # 获取横坐标参数值
                    backend_config = result["config"]
                    x_value = backend_config.get(test_param)
                    if x_value is None:
                        x_value = backend_config.get("args", {}).get(test_param)
                    if x_value is None:
                        x_value = f"unknown_{test_param}"
                    original_x_value = str(x_value)
                    sort_x_value = x_value

                    # 处理不同指标的数据来源
                    if metric_name == "Total Time":
                        total_times = [t["total_time"] for t in result["test_results"]]
                        value = sum(total_times) / len(total_times) if total_times else 0
                    else:
                        value = result["summary"].get(metric_key, 0)

                    model_data[model_name][(original_x_value, sort_x_value)] = value

                # 绘制折线
                for model, data in model_data.items():
                    def sort_key(item):
                        key = item[0][1]
                        try:
                            return float(key)
                        except (ValueError, TypeError):
                            return str(key)

                    sorted_items = sorted(data.items(), key=sort_key, reverse=False)
                    x = [item[0][0] for item in sorted_items]
                    y = [item[1] for item in sorted_items]
                    plt.plot(x, y, marker='o', label=model, linewidth=2, markersize=6)

                # 图表设置
                plt.xlabel(test_param, fontsize=12)
                plt.ylabel(f"{metric_name} ({y_unit})", fontsize=12)
                plt.title(f"{backend} - {metric_name} vs {test_param}", fontsize=14)
                plt.legend(title="Models", fontsize=10)
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()

                # 保存单独图表
                plot_path = os.path.join(report_dir, f"{backend}_{metric_name.lower()}_vs_{test_param}.png")
                plt.savefig(plot_path, dpi=300)
                plt.close()
                print(f"已生成单独图表: {plot_path}")

            # 新功能：生成合并大图
            self._generate_combined_chart(backend, results, test_param, report_dir)

        print(f"所有报告图表已保存到: {report_dir}")

    def _generate_combined_chart(self, backend, results, test_param, report_dir):
        """生成合并四幅图的大图"""
        from collections import defaultdict

        # 设置中文字体，确保中文显示正常
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 创建大图
        fig = plt.figure(figsize=(20, 30))
        sns.set_style("whitegrid")
        
        # 定义子图布局
        # 顶部预留空间用于配置信息，下面放2x2的四幅图
        fig.suptitle(f'{backend} - 性能测试报告', fontsize=30, fontweight='bold', y=0.95,fontproperties=self._get_chinese_font())
        
        # 创建网格布局：5行1列，第一行用于配置信息，下面四行用于图表
        grid_spec = plt.GridSpec(5, 1, height_ratios=[0.8, 1, 1, 1, 1], hspace=0.4)
        
        # 第一行：配置信息区域
        config_ax = fig.add_subplot(grid_spec[0])
        config_ax.axis('off')  # 隐藏坐标轴
        
        # 准备配置信息文本
        config_text = self._prepare_config_info(results, test_param)
        config_ax.text(0.02, 0.5, config_text, fontsize=11, va='center', ha='left', 
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.7),
                     fontproperties=self._get_chinese_font())
        
        # 定义指标和对应的子图位置
        metrics = {
            "TTFT": ("ttft_avg", "s", grid_spec[1]),
            "TPOT": ("tpot_avg", "ms", grid_spec[2]),
            "Throughput": ("throughput_avg", "token/s", grid_spec[3]),
            "Total Time": ("total_time", "s", grid_spec[4])
        }
        
        # 为每个指标创建子图
        for i, (metric_name, (metric_key, y_unit, subplot_spec)) in enumerate(metrics.items()):
            ax = fig.add_subplot(subplot_spec)
            
            # 收集每个模型的数据
            model_data = defaultdict(dict)
            for result in results:
                model_name = result["name"]

                # 获取横坐标参数值
                backend_config = result["config"]
                x_value = backend_config.get(test_param)
                if x_value is None:
                    x_value = backend_config.get("args", {}).get(test_param)
                if x_value is None:
                    x_value = f"unknown_{test_param}"
                original_x_value = str(x_value)
                sort_x_value = x_value

                # 处理不同指标的数据来源
                if metric_name == "Total Time":
                    total_times = [t["total_time"] for t in result["test_results"]]
                    value = sum(total_times) / len(total_times) if total_times else 0
                else:
                    value = result["summary"].get(metric_key, 0)

                model_data[model_name][(original_x_value, sort_x_value)] = value

            # 绘制折线
            colors = plt.cm.Set3(np.linspace(0, 1, len(model_data)))
            for (model, data), color in zip(model_data.items(), colors):
                def sort_key(item):
                    key = item[0][1]
                    try:
                        return float(key)
                    except (ValueError, TypeError):
                        return str(key)

                sorted_items = sorted(data.items(), key=sort_key, reverse=True)
                x = [item[0][0] for item in sorted_items]
                y = [item[1] for item in sorted_items]
                ax.plot(x, y, marker='o', label=model, linewidth=2, markersize=6, color=color)
                
                # 在数据点上添加数值标签
                for j, (x_val, y_val) in enumerate(zip(x, y)):
                    ax.annotate(f'{y_val:.2f}', (x_val, y_val), 
                            textcoords="offset points", xytext=(0,8), 
                            ha='center', fontsize=8)

            # 子图设置
            ax.set_xlabel(test_param, fontsize=11)
            ax.set_ylabel(f"{metric_name} ({y_unit})", fontsize=11)
            ax.set_title(f"{metric_name} vs {test_param}", fontsize=13, fontweight='bold')
            ax.legend(title="Models", fontsize=9)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存合并大图
        combined_plot_path = os.path.join(report_dir, f"{backend}_combined_report.png")
        plt.savefig(combined_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"已生成合并大图: {combined_plot_path}")

    def _get_chinese_font(self):
        """获取中文字体属性，确保中文显示正常"""
        from matplotlib.font_manager import FontProperties
        # 尝试使用系统中可能的中文字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 
                        'Heiti TC', 'Arial Unicode MS', 'DejaVu Sans']
        
        # 返回第一个可用的字体
        return FontProperties(family=chinese_fonts)

    def _prepare_config_info(self, results, test_param):
        """准备配置信息文本"""
        config_info = []
        
        # 基本信息
        config_info.append("测试配置信息")
        config_info.append("=" * 30)
        
        # 测试参数信息
        config_info.append(f"横坐标参数: {test_param}")
        config_info.append(f"测试数量: {len(results)}")
        config_info.append(f"后端类型: {results[0]['backend'] if results else 'N/A'}")
        
        # 添加每个测试的基本信息
        config_info.append("\n测试详情:")
        for i, result in enumerate(results):
            backend_config = result["config"]
            value=backend_config.get(test_param)
            config_info.append(f"  {i+1}. {result['name']} {test_param}={value}")
            #config_info.append(f"     模型: {result['config'].get('model', 'N/A')}")
            config_info.append(f"     流式: {result.get('streaming', 'N/A')}")
            # if test_param in result['config']:
            #     config_info.append(f"     {test_param}: {result['config'][test_param]}")
            # elif 'args' in result['config'] and test_param in result['config']['args']:
            #     config_info.append(f"     {test_param}: {result['config']['args'][test_param]}")
        
        # 添加提示词信息
        prompts = self.config.get_prompts()
        config_info.append(f"\n提示词数量: {len(prompts)}")
        config_info.append(f"最大Token数: {self.config.get_max_tokens()}")
        
        return "\n".join(config_info)
    