
# Deep Learning Training Workflow

## Khi Nào Dùng

- Training hoặc fine-tuning deep learning models với PyTorch
- Thiết lập experiment tracking với MLflow
- Làm việc với HuggingFace models và datasets
- Tham gia ML competitions (Kaggle, etc.)
- Cấu hình training pipeline (data loading, augmentation, scheduling)

> **Test Coverage**: ≥ 95% cho tất cả training scripts và data pipelines.

## Common Rules

### Package Manager
- **uv pip only** (KHÔNG dùng standard pip)

### Language
- Tất cả comments/docstrings bằng **tiếng Việt**

### Code Structure
- **OOP**: Define + test classes ngay lập tức (không đợi `main`)
- **Config**: Separate `Config` class/block - KHÔNG hardcode values trong logic

### Data Handling
- **polars** strictly (KHÔNG dùng pandas, trừ legacy conflicts)

### Reproducibility
- Set explicit random seeds ở đầu

### Visualization
- `tqdm` cho loops
- `matplotlib`/`seaborn` cho results

## Deep Learning Stack

### Core Framework
- **PyTorch** + **HuggingFace**:
  - Accelerate
  - Evaluate
  - Optimum
  - PEFT
  - Safetensors

### Experiment Tracking (MLflow)
MLflow 3.x selfhost tại `mlflow.n24q02m.com`, **built-in authentication** (KHÔNG cần CF Access).

| Environment | Endpoint | Auth |
|-------------|----------|------|
| Local Dev | `https://mlflow.n24q02m.com` | Built-in auth (username/password) |
| OCI VM | `http://mlflow:5000` | Internal network |

**Setup MLflow Auth:**
```python
import os
import mlflow

# Built-in authentication
mlflow.set_tracking_uri("https://mlflow.n24q02m.com")
os.environ["MLFLOW_TRACKING_USERNAME"] = os.environ["MLFLOW_USERNAME"]
os.environ["MLFLOW_TRACKING_PASSWORD"] = os.environ["MLFLOW_PASSWORD"]
```

**Logging cơ bản:**
```python
import mlflow

mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    mlflow.log_params({
        "learning_rate": config.learning_rate,
        "batch_size": config.batch_size,
        "epochs": config.epochs,
    })
    
    for epoch in range(config.epochs):
        # Training...
        mlflow.log_metrics({
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_accuracy": val_acc,
        }, step=epoch)
    
    # Log model artifact
    mlflow.pytorch.log_model(model, "model")
```

### Optimization Techniques

| Technique | Implementation |
|-----------|----------------|
| Mixed Precision | `torch.amp` |
| Memory Optimization | Gradient Accumulation |
| Memory Optimization | Gradient Checkpointing |

### Training Configuration

| Component | Choice |
|-----------|--------|
| Optimizer | AdamW |
| Scheduler | OneCycleLR |
| Regularization | Early Stopping |

### Output Format
- Save checkpoints as **safetensors**

## Training Template

```python
# Config
class Config:
    seed: int = 42
    batch_size: int = 32
    learning_rate: float = 1e-4
    epochs: int = 10
    # ...

# Set random seeds
def set_seed(seed: int) -> None:
    """Đảm bảo reproducibility."""
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # ...

# Training loop với mixed precision
with torch.amp.autocast('cuda'):
    outputs = model(inputs)
    loss = criterion(outputs, targets)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# Save checkpoint
model.save_pretrained(path, safe_serialization=True)
```

## Checklist

- [ ] Random seeds được set?
- [ ] Config class riêng biệt?
- [ ] Comments bằng tiếng Việt?
- [ ] Dùng polars thay vì pandas?
- [ ] Mixed precision enabled?
- [ ] Gradient accumulation/checkpointing nếu cần?
- [ ] Early stopping implemented?
- [ ] Save as safetensors?
- [ ] MLflow tracking configured?
- [ ] MLflow built-in auth credentials set (nếu remote)?
