# 模型性能测试工具使用指南

## 目录



- [模型性能测试工具使用指南](#模型性能测试工具使用指南)
  - [目录](#目录)
  - [概述](#概述)
  - [快速开始](#快速开始)
  - [测试场景](#测试场景)
    - [1. 测试本地 Windows 上的 Ollama](#1-测试本地-windows-上的-ollama)
      - [前提条件](#前提条件)
      - [配置步骤](#配置步骤)
      - [执行命令](#执行命令)
    - [2. 通过 SSH 连接 WSL 测试 vLLM](#2-通过-ssh-连接-wsl-测试-vllm)
      - [前提条件](#前提条件-1)
      - [配置步骤](#配置步骤-1)
      - [执行命令](#执行命令-1)
    - [3. 通过 SSH 连接远程服务器测试](#3-通过-ssh-连接远程服务器测试)
      - [前提条件](#前提条件-2)
      - [配置步骤](#配置步骤-2)
      - [连通性测试](#连通性测试)
      - [执行性能测试](#执行性能测试)
  - [配置文件详解](#配置文件详解)
  - [常见问题排查](#常见问题排查)

## 概述

本工具提供了一个统一的框架，用于测试不同环境（本地 Windows、WSL、远程服务器）中部署的大语言模型（如 Ollama, vLLM）的性能。通过编写简单的 JSON 配置文件，你可以轻松发起测试并获得性能报告。

## 快速开始



1. **环境准备**:

* 确保你的本地机器安装了 Python 3.8+。

* 安装必要的依赖库：



```
pip install -r requirements.txt
```



1. **配置文件**: 根据你的测试目标，复制并修改相应的示例配置文件（`config_teach1.json`, `config_teach2.json`），保存为新文件（例如 `my_test_config.json`）。

2. **运行测试**: 在项目根目录下，打开终端，执行以下命令：



```
python run_tests.py --config my_test_config.json
```



1. **查看结果**: 测试完成后，结果（包括吞吐量、延迟等指标）将自动保存到 `results` 目录下的 JSON 文件中。



***

## 测试场景

### 1. 测试本地 Windows 上的 Ollama

此方法用于测试直接在你的 Windows 操作系统上运行的 Ollama 服务。

#### 前提条件



* Windows 已安装并运行 Ollama。

* 已通过 `ollama pull <model_name>` 命令下载好要测试的模型。

#### 配置步骤



1. 复制 `config_teach1.json` 并命名为 `your_config.json`。

2. 修改 `your_config.json` 文件：



#### 执行命令

在 `run_tests.py` 所在的目录下，打开终端并运行：



```
python run_tests.py --config your_config.json
```

***

### 2. 通过 SSH 连接 WSL 测试 vLLM

此方法用于测试部署在 Windows Subsystem for Linux (WSL) 中的 vLLM 模型服务。

#### 前提条件


* WSL (如 Ubuntu) 已安装并配置好。

* WSL 中已安装 vLLM 及其依赖（如 CUDA）。

* 已将模型文件放置在 WSL 可访问的路径下（可以是 Windows 磁盘挂载路径，如 `/mnt/e/...`）。

* 确保 Windows 主机和 WSL 之间网络通畅。

#### 配置步骤



1. 复制 `config_teach2.json` 并命名为 `wsl_test_config.json`。

2. 在 WSL 终端中，运行 `hostname -I` 获取其 IP 地址。

3. 修改 `wsl_test_config.json` 文件：


* **注意**: 如果 `wsl-venv` 设置为 `true`，请确保 WSL 中已配置好 `~/.bashrc` 或类似文件，使得非交互式 SSH 登录时也能正确加载虚拟环境。

#### 执行命令

```
python run_tests.py --config wsl_test_config.json
```

* **原理**: 脚本会通过 SSH 连接到 WSL，自动启动 vLLM 服务，执行测试，然后关闭服务。


### 3. 通过 SSH 连接远程服务器测试

此方法用于测试部署在远程 Linux 服务器上的模型服务，其配置与测试 WSL 类似。

#### 前提条件

* 拥有远程服务器的 SSH 登录权限（用户名 / 密码或 SSH 密钥）。

* 远程服务器上已部署好模型服务（如 vLLM, Text Generation Inference 等）。

#### 配置步骤

1. 复制 `config.json` 并命名为 `remote_test_config.json`。

2. 修改 `remote_test_config.json` 文件，主要配置 `ssh` 和 `tests` 部分：

#### 连通性测试

在进行完整的性能测试前，建议先测试与服务器的连通性：
```
python demo_run_server_test.py --config remote_test_config.json
```
#### 执行性能测试

```
python run_tests.py --config remote_test_config.json
```

## 配置文件详解



| 一级字段                     | 二级字段         | 类型             | 说明                                                       |
| ------------------------ | ------------ | -------------- | -------------------------------------------------------- |
| `ssh`                    | `local_mode` | `bool`         | 是否为本地模式。`true` 表示测试本机服务，`false` 表示通过 SSH 测试远程服务。         |
| `ssh`                    | `hostname`   | `string`       | 远程服务器的 IP 地址或主机名。在 `local_mode=true` 时，通常设为 `127.0.0.1`。 |
| `ssh`                    | `username`   | `string`       | SSH 登录用户名。                                               |
| `ssh`                    | `password`   | `string`       | SSH 登录密码。如果使用密钥认证，请留空或设为 `null`。                         |
| `ssh`                    | `key_path`   | `string`       | SSH 私钥文件路径。                                              |
| `ssh`                    | `port`       | `int`          | SSH 服务端口，默认为 `22`。                                       |
| `prompts`                | -            | `list[string]` | 用于测试的提示词列表。                                              |
| `max_tokens`             | -            | `int`          | 模型生成文本的最大 Token 数。                                       |
| `result_dir`             | -            | `string`       | 测试结果文件的输出目录。                                             |
| `tests`                  | -            | `list[object]` | 测试用例列表。每个对象代表一个模型 / 后端的测试任务。                             |
| `tests[].name`           | -            | `string`       | 测试用例的名称，用于标识结果。                                          |
| `tests[].model`          | -            | `string`       | **(Ollama 专用)** 要测试的 Ollama 模型名称。                        |
| `tests[].backend`        | -            | `string`       | **(远程 / 非 Ollama 专用)** 模型服务后端，如 `vllm`。                  |
| `tests[].local_mode`     | -            | `bool`         | **(Ollama 专用)** 通常与顶层 `ssh.local_mode` 保持一致。             |
| `tests[].port`           | -            | `int`          | 模型服务监听的端口号。                                              |
| `tests[].backend_config` | -            | `object`       | **(远程 / 非 Ollama 专用)** 后端服务的详细配置。                        |
| `...`                    | `model_path` | `string`       | 模型文件在远程服务器上的绝对路径。                                        |
| `...`                    | `wsl-venv`   | `bool`         | **(WSL 专用)** 是否需要激活 WSL 中的 Python 虚拟环境。                  |
| `...`                    | `args`       | `object`       | 启动后端服务时的命令行参数。                                           |

## 常见问题排查



1. **SSH 连接失败**:

* 检查 `hostname`, `username`, `password`/`key_path` 和 `port` 是否正确。

* 确保远程服务器的 SSH 服务正在运行，并且网络可达（可尝试用 `ping` 或 `ssh username@hostname` 命令测试）。

* 如果是 WSL，确保 Windows Defender 防火墙允许相关连接。

1. **模型未找到**:

* 对于 Ollama，确保 `model` 字段与 `ollama list` 中显示的名称完全一致。

* 对于 vLLM，确保 `model_path` 指向的是包含模型权重文件（如 `config.json`, `model.safetensors`）的正确目录。在 WSL 中，检查 Windows 磁盘挂载路径是否正确（如 `/mnt/e/...`）。

1. **端口冲突**:

* 确保配置文件中 `port` 字段指定的端口在本地或远程服务器上没有被其他程序占用。可以更换一个未使用的端口号。

1. **权限问题**:

* 确保执行脚本的用户有足够的权限读取配置文件和写入结果目录。

* 在远程服务器上，确保 SSH 用户有足够的权限在指定目录启动服务和访问模型文件。

1. **vLLM 启动失败 (WSL)**:

* 检查 WSL 中的 CUDA 和 GPU 驱动是否正确安装并能被 vLLM 识别。

* 如果 `wsl-venv` 设置为 `true`，确认虚拟环境的激活命令是否正确。脚本默认使用 `source ~/venv/bin/activate`。如果你的环境不同，请修改 `run_tests.py` 中相应的激活命令。
