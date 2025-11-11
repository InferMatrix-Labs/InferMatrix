import os
import argparse
from test_orchestrator import TestOrchestrator

# 命令行参数列表
command_args = {
    "--config": "--config config_file_path(str) 设置配置文件路径",
    "--test": "--test testname(str)           只运行指定名称的测试(可通过 --list 查看可用的测试名称)",
    "--tests": "--tests testname1 testname2...或--tests index1 index2...\t指定一个或多个测试名称或索引(可通过 --list 查看可用的测试名称和索引(名称前数字))",
    "--list": "--list                         列出所有测试配置",
    "--generate-report": "--generate-report              只生成报告，不运行测试",
    "--no-cleanup": "--no-cleanup                   测试完成后不停止服务",
    "--no-report": "--no-report                    不生成报告",
    "--deploy-only": "--deploy-only                  只部署服务不运行测试",
    "--repeat": "--repeat nums                  设置测试重复次数",
    "--maxtokens": "--maxtokens nums               覆盖最大生成token数",
    "--prompts": "--prompts prompt               覆盖测试提示词",
    "--helps": "--helps                        测试代码使用说明",
}


def main():
    parser = argparse.ArgumentParser(description="LLM性能测试框架")

    parser.add_argument(
        "--config", type=str, default="config_v00.json", help="配置文件路径"
    )
    parser.add_argument("--test", type=str, help="只运行指定名称的测试")
    parser.add_argument("--list", action="store_true", help="列出所有测试配置")
    parser.add_argument(
        "--generate-report", action="store_true", help="只生成报告，不运行测试"
    )

    # 新增的参数
    parser.add_argument("--tests", nargs="+", help="指定一个或多个测试名称或索引")
    parser.add_argument(
        "--no-cleanup", action="store_true", help="测试完成后不停止服务"
    )
    parser.add_argument("--no-report", action="store_true", help="不生成报告")
    parser.add_argument(
        "--deploy-only", action="store_true", help="只部署服务不运行测试"
    )
    # 覆盖配置文件中的参数
    parser.add_argument("--repeat", type=int, help="覆盖测试重复次数")
    parser.add_argument("--maxtokens", type=int, help="覆盖最大生成token数")
    parser.add_argument("--prompts", nargs="+", help="覆盖测试提示词")
    # 用户帮助手册
    parser.add_argument("--helps", action="store_true", help="测试代码使用说明")

    args = parser.parse_args()

    # 初始化测试编排器
    orchestrator = TestOrchestrator(args.config)

    # 用户帮助手册
    if args.helps:
        print(
            "运行测试代码：python run_tests.py [--arg1] [--arg2]([number] [number]...)\n"
        )
        print("可设置参数(arg):")
        for value in command_args.values():
            print(value)
        return

    # 列出测试
    if args.list:
        tests = orchestrator.config.get_tests()
        print(f"配置文件包含 {len(tests)} 个测试:")
        for i, test in enumerate(tests):
            print(f"{i + 1}. {test['name']} ({test['backend']})")
        return

    # 只生成报告
    if args.generate_report:
        orchestrator.generate_report()
        return

    # 初始化连接
    if not orchestrator.initialize():
        print("初始化失败，退出测试")
        return

    # 应用参数覆盖
    if args.repeat:
        orchestrator.config.config["default_repeat"] = args.repeat
    if args.maxtokens:
        orchestrator.config.config["max_tokens"] = args.maxtokens
    if args.prompts:
        orchestrator.config.config["prompts"] = args.prompts

    # 运行测试
    try:
        if args.deploy_only:
            print("只部署服务不运行测试")
            # 部署第一个测试的服务但不运行
            if orchestrator.config.get_tests():
                test_config = orchestrator.config.get_tests()[0]
                orchestrator.service_manager.deploy_service(
                    test_config["backend"], test_config["backend_config"]
                )
            return
        tests_to_run = []
        if args.test:
            # 运行单个指定测试
            tests = orchestrator.config.get_tests()
            # test_to_run = None
            for test in tests:
                if test["name"] == args.test:
                    # test_to_run = test
                    tests_to_run.append(test)
                    break
            if not tests_to_run:
                print(f"未找到名为 '{args.test}' 的测试")
            """
            if test_to_run:
                orchestrator.run_test(test_to_run)
                orchestrator.save_results()
            else:
                print(f"未找到名为 '{args.test}' 的测试")
            """
        # 运行多个指定测试
        elif args.tests:
            # selected_tests = []
            tests = orchestrator.config.get_tests()

            for identifier in args.tests:
                # 按名称查找
                test_by_name = next((t for t in tests if t["name"] == identifier), None)
                if test_by_name:
                    tests_to_run.append(test_by_name)
                # 按索引查找
                elif identifier.isdigit() and 0 < int(identifier) <= len(tests):
                    tests_to_run.append(tests[int(identifier) - 1])
                else:
                    print(f"无效的测试标识符: {identifier}")

            # for test in selected_tests:
            #    orchestrator.run_test(test)
            #    orchestrator.save_results()
        # 运行选中的测试
        if tests_to_run:
            for test in tests_to_run:
                # 应用重复次数覆盖
                if args.repeat:
                    test["repeat"] = args.repeat
                orchestrator.run_test(test)
                orchestrator.save_results()
        else:
            # 运行所有测试
            orchestrator.run_all_tests()

    finally:
        # 清理资源
        # if orchestrator.service_manager:
        #   orchestrator.service_manager.stop_service()
        if not args.no_cleanup and orchestrator.service_manager:
            orchestrator.service_manager.stop_service()

    # 生成报告
    # orchestrator.generate_report()
    if not args.no_report:
        orchestrator.generate_report()


if __name__ == "__main__":
    main()
