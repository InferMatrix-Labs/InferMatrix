# Building Performance Matrices with InferMatrix

## Overview

InferMatrix's core strength is its ability to build **comprehensive performance matrices** that allow systematic comparison across multiple dimensions. This guide shows you how to design and execute matrix-based evaluations.

## What is a Performance Matrix?

A performance matrix is a systematic comparison table where:
- **Rows** represent one variable (e.g., backends, models)
- **Columns** represent another variable (e.g., hardware configs, batch sizes)
- **Cells** contain performance metrics (e.g., throughput, latency)

### Example Matrix

| Backend | RTX 4090 | RTX 3090 | A100 |
|---------|----------|----------|------|
| Ollama  | 137 t/s  | 89 t/s   | 156 t/s |
| vLLM    | 156 t/s  | 102 t/s  | 198 t/s |
| LMStudio| 125 t/s  | 84 t/s   | 145 t/s |

## Common Matrix Types

### 1. Backend Comparison Matrix

**Use Case**: Find the best inference framework for your model

**Configuration**:
```json
{
  "prompts": ["Standard test prompt"],
  "max_tokens": 512,
  "tests": [
    {"name": "ollama-test", "backend": "ollama", "model": "llama2:7b"},
    {"name": "vllm-test", "backend": "vllm", "backend_config": {...}},
    {"name": "lmstudio-test", "backend": "lmstudio", ...}
  ]
}
```

**Result Matrix**:
```
Backend Performance Comparison - LLaMA 2 7B
┌──────────┬──────────┬────────────┬────────────┐
│ Backend  │ TTFT (s) │ TPOT (ms)  │ Throughput │
├──────────┼──────────┼────────────┼────────────┤
│ Ollama   │ 2.5      │ 45         │ 22 tok/s   │
│ vLLM     │ 0.8      │ 20         │ 50 tok/s   │
│ LMStudio │ 1.9      │ 38         │ 26 tok/s   │
└──────────┴──────────┴────────────┴────────────┘
```

### 2. Hardware Configuration Matrix

**Use Case**: Determine optimal GPU for your workload

**Approach**: Run the same model/backend on different hardware

**Step 1**: Create configs for each hardware setup
```bash
configs/
├── rtx4090_config.json
├── rtx3090_config.json
└── a100_config.json
```

**Step 2**: Run tests on each system
```bash
# On RTX 4090 machine
python run_tests.py --config configs/rtx4090_config.json

# On RTX 3090 machine
python run_tests.py --config configs/rtx3090_config.json

# On A100 machine
python run_tests.py --config configs/a100_config.json
```

**Step 3**: Aggregate results into matrix

### 3. Model Comparison Matrix

**Use Case**: Evaluate performance of different models on same hardware

**Configuration**:
```json
{
  "tests": [
    {"name": "deepseek-1.5b", "model": "deepseek-r1:1.5b"},
    {"name": "qwen-1.7b", "model": "qwen3:1.7b"},
    {"name": "llama-7b", "model": "llama2:7b"},
    {"name": "mistral-7b", "model": "mistral:7b"}
  ]
}
```

**Result Matrix**:
```
Model Performance on RTX 4090 + vLLM
┌─────────────┬──────────┬───────────┬────────────┐
│ Model       │ TTFT (s) │ TPOT (ms) │ Throughput │
├─────────────┼──────────┼───────────┼────────────┤
│ DeepSeek 1B │ 0.25     │ 8         │ 125 tok/s  │
│ Qwen 2B     │ 0.31     │ 12        │ 83 tok/s   │
│ LLaMA 7B    │ 0.89     │ 28        │ 35 tok/s   │
│ Mistral 7B  │ 0.95     │ 30        │ 33 tok/s   │
└─────────────┴──────────┴───────────┴────────────┘
```

### 4. Quantization Matrix

**Use Case**: Compare quantization methods' impact on performance

**Configuration**:
```json
{
  "tests": [
    {"name": "fp16", "model": "llama2:7b"},
    {"name": "q8", "model": "llama2:7b-q8_0"},
    {"name": "q4", "model": "llama2:7b-q4_K_M"},
    {"name": "q2", "model": "llama2:7b-q2_K"}
  ]
}
```

### 5. Prompt Length Matrix

**Use Case**: Understand how context length affects performance

**Configuration**:
```json
{
  "prompts": [
    "Short prompt (10 tokens)",
    "Medium prompt... (100 tokens)",
    "Long prompt... (1000 tokens)",
    "Very long prompt... (4000 tokens)"
  ],
  "tests": [{"name": "context-test", "model": "llama2:7b"}]
}
```

## Multi-Dimensional Matrices

### 3D Matrix: Backend × Hardware × Model

Create a comprehensive evaluation across three dimensions:

**Execution Plan**:
```bash
# Dimension 1: Backends (Ollama, vLLM, LMStudio)
# Dimension 2: Hardware (RTX 4090, RTX 3090, A100)
# Dimension 3: Models (DeepSeek, Qwen, LLaMA)

# Total tests: 3 × 3 × 3 = 27 configurations
```

**Sample Result**:
```
DeepSeek R1 1.5B Performance Matrix
                RTX 4090    RTX 3090    A100
Ollama          137 t/s     89 t/s      156 t/s
vLLM            156 t/s     102 t/s     198 t/s
LMStudio        125 t/s     84 t/s      145 t/s

Qwen 3 1.7B Performance Matrix
                RTX 4090    RTX 3090    A100
Ollama          126 t/s     82 t/s      148 t/s
vLLM            148 t/s     95 t/s      189 t/s
LMStudio        118 t/s     79 t/s      138 t/s
```

## Best Practices

### 1. Design Your Matrix

Before running tests, plan your matrix dimensions:
- What variables do you want to compare?
- What metrics matter most for your use case?
- How many data points can you reasonably collect?

### 2. Control Variables

When comparing one dimension, keep others constant:
- ✅ Same prompt when comparing backends
- ✅ Same model when comparing hardware
- ✅ Same temperature/sampling settings

### 3. Run Multiple Iterations

For statistical reliability:
```json
{
  "prompts": [
    "Test prompt 1",
    "Test prompt 2",
    "Test prompt 3"
  ]
}
```

Take averages across multiple runs.

### 4. Document Conditions

Always record:
- Date and time of tests
- Hardware specifications
- Software versions (CUDA, PyTorch, etc.)
- Environmental factors (temperature, other processes)

### 5. Visualize Results

Use InferMatrix's built-in visualization or export data:
```bash
# Generate report with charts
python run_tests.py --generate-report

# Export to CSV for custom analysis
python export_results.py --format csv
```

## Advanced Matrix Scenarios

### Scenario 1: New Model Evaluation

**Goal**: Quickly assess a new model's performance across your infrastructure

**Approach**:
1. Create configs for each hardware setup
2. Test with same prompts
3. Compare to baseline (e.g., previous model)

### Scenario 2: Infrastructure Optimization

**Goal**: Decide between purchasing RTX 4090 vs A100

**Approach**:
1. Test your target models on both GPUs
2. Calculate cost per token: (GPU price) / (tokens per second)
3. Factor in throughput and latency requirements

### Scenario 3: Production Deployment Planning

**Goal**: Choose optimal backend + hardware combination

**Approach**:
1. Build comprehensive matrix across all options
2. Weight metrics by importance (e.g., TTFT > throughput for chat)
3. Consider total cost of ownership

## Matrix Analysis Tips

### Reading the Matrix

- **Best Overall**: Highest throughput + lowest latency
- **Cost-Effective**: Good performance + lower-tier hardware
- **Latency-Sensitive**: Prioritize TTFT over throughput
- **Batch Processing**: Prioritize throughput over TTFT

### Common Patterns

```
Pattern 1: Hardware-Bound
- Small model differences
- Large hardware differences
→ Consider upgrading GPU

Pattern 2: Software-Bound
- Large backend differences
- Small hardware differences
→ Consider changing framework

Pattern 3: Model-Bound
- Large model differences
- Small backend/hardware differences
→ Model architecture is limiting factor
```

## Exporting Matrix Data

InferMatrix saves results in JSON format. Convert to matrix view:

```python
import json
import pandas as pd

# Load results
with open('results/test_results.json') as f:
    data = json.load(f)

# Create matrix
matrix = pd.DataFrame({
    'Backend': [...],
    'TTFT': [...],
    'Throughput': [...]
})

print(matrix.pivot_table(index='Backend', values='Throughput'))
```

## Conclusion

Performance matrices are powerful tools for:
- **Decision Making**: Data-driven infrastructure choices
- **Optimization**: Identify bottlenecks systematically
- **Reporting**: Clear communication of results

Start building your first matrix today with InferMatrix!

---

**Next Steps**:
1. Review [Quick Start](README.md#quick-start)
2. Check [Configuration Reference](README.md#configuration-reference)
3. Explore [Example Configs](configs/)
4. Build your first matrix!
