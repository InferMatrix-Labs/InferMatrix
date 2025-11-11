# InferMatrix Quick Reference

## 🚀 Installation & Setup

```bash
git clone https://github.com/infermatrix/infermatrix.git
cd infermatrix
pip install -r requirements.txt
```

## 📋 Common Commands

| Command | Description |
|---------|-------------|
| `python run_tests.py --config <file>` | Run tests with configuration |
| `python run_tests.py --list` | List available tests |
| `python run_tests.py --generate-report` | Generate performance report |
| `python demo_run_server_test.py --config <file>` | Test server connectivity |

## 🎯 Configuration Templates

### Local Ollama
```json
{
  "ssh": {"local_mode": true, "hostname": "127.0.0.1"},
  "tests": [{"name": "test", "model": "llama2:7b", "backend": "ollama", "port": 11434}]
}
```

### Remote vLLM
```json
{
  "ssh": {"local_mode": false, "hostname": "192.168.1.100", "username": "user", "password": "pass"},
  "tests": [{
    "name": "test",
    "backend": "vllm",
    "port": 8000,
    "backend_config": {"model_path": "/path/to/model", "args": {"host": "0.0.0.0", "port": 8000}}
  }]
}
```

## 📊 Key Metrics

| Metric | Meaning | Good Value |
|--------|---------|------------|
| **TTFT** | Time to first token | < 1s |
| **TPOT** | Time per output token | < 50ms |
| **Throughput** | Tokens per second | > 50 tok/s |

## 🔧 Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| SSH connection failed | Check hostname, username, password |
| Model not found | Verify model path or name |
| Port in use | Change port number or kill process |
| Permission denied | Check file/directory permissions |
| GPU not detected (WSL) | Verify CUDA with `nvidia-smi` |

## 📁 File Structure

```
infermatrix/
├── run_tests.py          # Main entry
├── configs/              # Configuration examples
├── results/              # Test outputs
└── requirements.txt      # Dependencies
```

## 🎓 Best Practices

1. **Start Simple**: Begin with local testing before remote
2. **Test Connectivity**: Use `demo_run_server_test.py` first
3. **Version Control**: Keep config files in git
4. **Document Results**: Add notes to result directories
5. **Incremental Testing**: Test one backend at a time

## 📞 Getting Help

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/infermatrix/infermatrix/issues)
- 💬 [Discussions](https://github.com/infermatrix/infermatrix/discussions)
- 📧 Contact: infermatrix.dev@protonmail.com

---

**Tip**: Keep this reference handy while working with InferMatrix!
