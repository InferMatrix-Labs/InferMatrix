# InferMatrix

<div align="center">

<img src="docs/assets/logo.png" width="200" alt="InferMatrix Logo">

**Systematic LLM Inference Performance Evaluation**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*Build Performance Matrices • Compare Hardware Configs • Optimize Deployments*

[Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples) • [Contributing](#-contributing)

</div>

---

## 🎯 What is InferMatrix?

**InferMatrix** is a unified framework for systematic evaluation of Large Language Model (LLM) inference performance across multiple backends and hardware configurations. It helps you build comprehensive **performance matrices** to identify optimal deployment strategies.

### Why InferMatrix?

- 🔄 **Multi-Backend Support**: Seamlessly test Ollama, vLLM, and LMStudio
- 🌐 **Flexible Deployment**: Local Windows, WSL, and remote servers via SSH
- 📊 **Matrix-Based Evaluation**: Cross-dimensional performance comparison
- ⚡ **Comprehensive Metrics**: TTFT, TPOT, Throughput, and Token Count
- 🎛️ **JSON-Driven Configuration**: Simple setup, powerful capabilities
- 📈 **Auto Visualization**: Beautiful performance reports out of the box

### Performance Matrix Example

InferMatrix generates systematic performance comparisons like this:

| Backend | RTX 4090 | RTX 3090 | A100 |
|---------|----------|----------|------|
| **Ollama** | 137 tok/s | 89 tok/s | 156 tok/s |
| **vLLM** | 156 tok/s | 102 tok/s | 198 tok/s |
| **LMStudio** | 125 tok/s | 84 tok/s | 145 tok/s |

*Evaluate new models, compare frameworks, and optimize hardware choices systematically.*

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/infermatrix/infermatrix.git
cd infermatrix

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run a test with your configuration
python run_tests.py --config configs/example.json

# List all available tests
python run_tests.py --list

# Generate performance report
python run_tests.py --generate-report
```

### Your First Test

Create a simple configuration file `my_test.json`:

```json
{
  "ssh": {
    "local_mode": true,
    "hostname": "127.0.0.1"
  },
  "prompts": ["What is the capital of France?"],
  "max_tokens": 512,
  "result_dir": "results",
  "tests": [
    {
      "name": "ollama-test",
      "model": "llama2:7b",
      "backend": "ollama",
      "port": 11434
    }
  ]
}
```

Run the test:

```bash
python run_tests.py --config my_test.json
```

View results in `results/` directory with JSON files and visualizations.

---

## 📖 Documentation

### Table of Contents

- [Testing Scenarios](#testing-scenarios)
  - [Local Windows Testing](#1-local-windows-testing)
  - [WSL Testing via SSH](#2-wsl-testing-via-ssh)
  - [Remote Server Testing](#3-remote-server-testing)
- [Configuration Reference](#configuration-reference)
- [Performance Metrics](#performance-metrics)
- [Troubleshooting](#troubleshooting)

---

## 🎬 Testing Scenarios

### 1. Local Windows Testing

Test models running directly on your Windows machine (e.g., Ollama).

#### Prerequisites

- Windows with Ollama installed and running
- Model downloaded via `ollama pull <model_name>`

#### Configuration

Use the template `configs/local_ollama_example.json`:

```json
{
  "ssh": {
    "local_mode": true,
    "hostname": "127.0.0.1"
  },
  "prompts": [
    "Explain neural networks in simple terms.",
    "Write a Python function to calculate factorial."
  ],
  "max_tokens": 512,
  "result_dir": "results",
  "tests": [
    {
      "name": "ollama-local-test",
      "model": "deepseek-r1:1.5b",
      "backend": "ollama",
      "local_mode": true,
      "port": 11434
    }
  ]
}
```

#### Run Test

```bash
python run_tests.py --config configs/local_ollama_example.json
```

---

### 2. WSL Testing via SSH

Test models deployed in Windows Subsystem for Linux (e.g., vLLM).

#### Prerequisites

- WSL (Ubuntu recommended) installed and configured
- vLLM and dependencies (CUDA) installed in WSL
- Model files accessible in WSL (e.g., `/mnt/e/models/...`)
- Network connectivity between Windows and WSL

#### Configuration

**Step 1**: Get WSL IP address

```bash
# In WSL terminal
hostname -I
# Example output: 172.28.144.1
```

**Step 2**: Create configuration `wsl_test.json`:

```json
{
  "ssh": {
    "local_mode": false,
    "hostname": "172.28.144.1",
    "username": "your_wsl_username",
    "password": "your_password",
    "port": 22
  },
  "prompts": ["What is machine learning?"],
  "max_tokens": 512,
  "result_dir": "results",
  "tests": [
    {
      "name": "wsl-vllm-test",
      "backend": "vllm",
      "port": 8000,
      "backend_config": {
        "model_path": "/mnt/e/models/deepseek-r1-distill-qwen-1.5b",
        "wsl-venv": true,
        "args": {
          "host": "0.0.0.0",
          "port": 8000,
          "tensor-parallel-size": 1,
          "gpu-memory-utilization": 0.9,
          "max-model-len": 4096
        }
      }
    }
  ]
}
```

**Note**: If `wsl-venv: true`, ensure your WSL environment activates the Python virtual environment in non-interactive SSH sessions (configure in `~/.bashrc`).

#### Run Test

```bash
python run_tests.py --config wsl_test.json
```

**How it works**: InferMatrix connects to WSL via SSH, launches vLLM service, runs performance tests, and cleanly shuts down the service.

---

### 3. Remote Server Testing

Test models on remote Linux servers (e.g., vLLM, Text Generation Inference).

#### Prerequisites

- SSH access to remote server (username/password or SSH key)
- Model service deployed on the server (vLLM, TGI, etc.)

#### Configuration

Create `remote_test.json`:

```json
{
  "ssh": {
    "local_mode": false,
    "hostname": "192.168.1.100",
    "username": "your_username",
    "password": "your_password",
    "key_path": null,
    "port": 22
  },
  "prompts": [
    "Explain the transformer architecture.",
    "What are the benefits of quantization?"
  ],
  "max_tokens": 1024,
  "result_dir": "results",
  "tests": [
    {
      "name": "remote-vllm-test",
      "backend": "vllm",
      "port": 8000,
      "backend_config": {
        "model_path": "/data/models/llama-2-7b",
        "wsl-venv": false,
        "args": {
          "host": "0.0.0.0",
          "port": 8000,
          "tensor-parallel-size": 2,
          "gpu-memory-utilization": 0.85,
          "max-model-len": 8192
        }
      }
    }
  ]
}
```

#### Test Connectivity (Recommended)

Before running full tests, verify server connectivity:

```bash
python demo_run_server_test.py --config remote_test.json
```

#### Run Performance Test

```bash
python run_tests.py --config remote_test.json
```

---

## ⚙️ Configuration Reference

### Configuration Schema

| Field | Type | Description |
|-------|------|-------------|
| **`ssh.local_mode`** | `bool` | `true`: Test local services<br>`false`: Test via SSH |
| **`ssh.hostname`** | `string` | Server IP or hostname<br>(Use `127.0.0.1` for local) |
| **`ssh.username`** | `string` | SSH username |
| **`ssh.password`** | `string` | SSH password (leave empty if using key) |
| **`ssh.key_path`** | `string` | Path to SSH private key |
| **`ssh.port`** | `int` | SSH port (default: 22) |
| **`prompts`** | `list[string]` | List of test prompts |
| **`max_tokens`** | `int` | Maximum tokens to generate |
| **`result_dir`** | `string` | Output directory for results |
| **`tests`** | `list[object]` | List of test configurations |
| **`tests[].name`** | `string` | Test identifier |
| **`tests[].model`** | `string` | Model name (Ollama only) |
| **`tests[].backend`** | `string` | Backend type: `ollama`, `vllm`, `lmstudio` |
| **`tests[].port`** | `int` | Service port |
| **`tests[].backend_config`** | `object` | Backend-specific configuration |
| **`backend_config.model_path`** | `string` | Model file path on server |
| **`backend_config.wsl-venv`** | `bool` | Activate Python venv in WSL |
| **`backend_config.args`** | `object` | Backend startup arguments |

### Example Configurations

All example configurations are available in the `configs/` directory:

- **`local_ollama_example.json`** - Local Windows Ollama testing
- **`wsl_vllm_example.json`** - WSL vLLM testing via SSH
- **`remote_server_example.json`** - Remote server testing

---

## 📊 Performance Metrics

InferMatrix measures the following key performance indicators:

| Metric | Description | Unit |
|--------|-------------|------|
| **TTFT** | Time To First Token<br>Latency from request to first token | seconds |
| **TPOT** | Time Per Output Token<br>Average time per generated token | milliseconds |
| **Throughput** | Total tokens per second<br>Overall generation speed | tokens/s |
| **Token Count** | Total tokens in response | tokens |
| **Prefill Speed** | Input processing speed | tokens/s |

### Understanding the Metrics

```
Request Timeline:
├─ TTFT ─────┤ (Prefill Phase)
             └─ TPOT ─┬─ TPOT ─┬─ TPOT ─┤ (Decode Phase)
                      Token 1  Token 2  Token N

Total Latency = TTFT + (TPOT × N tokens)
Throughput = N tokens / Total Latency
```

---

## 🎨 Examples

### Building a Performance Matrix

Compare multiple models across different backends:

```json
{
  "prompts": ["Calculate 1+1"],
  "tests": [
    {
      "name": "ollama-deepseek",
      "model": "deepseek-r1:1.5b",
      "backend": "ollama",
      "port": 11434
    },
    {
      "name": "vllm-deepseek",
      "backend": "vllm",
      "backend_config": {
        "model_path": "/models/deepseek-r1-1.5b"
      }
    },
    {
      "name": "lmstudio-deepseek",
      "backend": "lmstudio",
      "port": 8000
    }
  ]
}
```

Results automatically generate a comparison matrix:

```
Framework Comparison - DeepSeek R1 1.5B
┌─────────────┬────────────┬───────────┬──────────────┐
│ Backend     │ TTFT (s)   │ TPOT (ms) │ Throughput   │
├─────────────┼────────────┼───────────┼──────────────┤
│ Ollama      │ 4.87       │ 7.29      │ 137.09 tok/s │
│ vLLM        │ 0.25       │ 15.80     │ 63.29 tok/s  │
│ LMStudio    │ 2.33       │ 9.81      │ 101.89 tok/s │
└─────────────┴────────────┴───────────┴──────────────┘
```

### Hardware Configuration Testing

Test the same model on different GPUs:

```bash
# Test on RTX 4090
python run_tests.py --config configs/rtx4090_config.json

# Test on RTX 3090
python run_tests.py --config configs/rtx3090_config.json

# Compare results
python generate_comparison_report.py \
  --results results/rtx4090_results.json results/rtx3090_results.json
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### SSH Connection Failed

**Symptoms**: `Connection refused` or `Permission denied`

**Solutions**:
- ✅ Verify `hostname`, `username`, `password`/`key_path`, and `port`
- ✅ Ensure SSH service is running: `sudo systemctl status ssh`
- ✅ Test connectivity: `ssh username@hostname`
- ✅ For WSL: Check Windows Defender Firewall settings

#### Model Not Found

**Symptoms**: `Model <name> not found` or `404 Not Found`

**Solutions**:
- **Ollama**: Verify model name matches `ollama list` exactly
- **vLLM**: Check `model_path` points to directory with `config.json` and weight files
- **WSL**: Ensure Windows drive mount path is correct (e.g., `/mnt/e/...`)

#### Port Already in Use

**Symptoms**: `Address already in use` or `Port <N> is occupied`

**Solutions**:
- ✅ Check if port is in use: `lsof -i :8000` (Linux) or `netstat -ano | findstr :8000` (Windows)
- ✅ Kill existing process or choose a different port
- ✅ Update `port` field in configuration

#### Permission Denied

**Symptoms**: `Permission denied` when accessing files or starting services

**Solutions**:
- ✅ Ensure user has read/write permissions for config and result directories
- ✅ Verify SSH user has permissions to access model files
- ✅ Check execution permissions: `chmod +x run_tests.py`

#### vLLM Startup Failed in WSL

**Symptoms**: vLLM fails to initialize or detect GPU

**Solutions**:
- ✅ Verify CUDA installation: `nvidia-smi` in WSL
- ✅ Check vLLM can detect GPU: `python -c "import torch; print(torch.cuda.is_available())"`
- ✅ If `wsl-venv: true`, verify activation command in script (default: `source ~/venv/bin/activate`)
- ✅ Ensure GPU drivers are properly passed through to WSL

#### Timeout Errors

**Symptoms**: `Request timeout` or `Connection timeout`

**Solutions**:
- ✅ Increase timeout values in code if testing very large models
- ✅ Check network stability
- ✅ Verify server resources are sufficient (CPU, GPU, RAM)

---

## 🏗️ Architecture

InferMatrix uses a modular architecture for flexibility and extensibility:

```
infermatrix/
├── run_tests.py              # Main entry point
├── test_orchestrator.py      # Test orchestration and workflow
├── llm_tester.py             # Core testing logic
├── ssh_manager.py            # SSH connection management
├── backend_deployer.py       # Backend service deployment
├── configs/                  # Configuration examples
│   ├── local_ollama_example.json
│   ├── wsl_vllm_example.json
│   └── remote_server_example.json
├── results/                  # Test results output
│   ├── *.json               # Raw performance data
│   └── *.png                # Visualization charts
└── utils/                    # Utility functions
    ├── metrics.py           # Performance metrics calculation
    └── visualizer.py        # Chart generation
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Ways to Contribute

- 🐛 Report bugs via [GitHub Issues](https://github.com/infermatrix/infermatrix/issues)
- 💡 Suggest features or improvements
- 📝 Improve documentation
- 🔧 Submit pull requests

### Priority Areas

- Support for additional backends (TensorRT-LLM, Text-Generation-Inference)
- Enhanced visualization options
- Batch testing capabilities
- Multi-GPU performance analysis
- CI/CD pipeline

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📚 Citation

If you use InferMatrix in your research, please cite:

```bibtex
@software{infermatrix2025,
  title={InferMatrix: Systematic LLM Inference Performance Evaluation},
  author={Anonymous},
  year={2025},
  url={https://github.com/infermatrix/infermatrix}
}
```

---

## 🔗 Related Projects

- [vLLM](https://github.com/vllm-project/vllm) - High-throughput LLM serving
- [Ollama](https://github.com/ollama/ollama) - Run LLMs locally
- [LMStudio](https://lmstudio.ai/) - Desktop LLM application
- [llm-perf](https://github.com/ray-project/llm-perf) - LLM performance benchmarking

---

## 🌟 Star History

If you find InferMatrix useful, please consider giving it a star ⭐

---

<div align="center">

**Built with ❤️ for the LLM community**

[Documentation](docs/) • [Issues](https://github.com/infermatrix/infermatrix/issues) • [Discussions](https://github.com/infermatrix/infermatrix/discussions)

</div>
