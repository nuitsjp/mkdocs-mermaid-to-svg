---
title: 機械学習プロジェクトガイド
created_at: 2025-06-14
updated_at: 2025-06-15
---

このドキュメントは機械学習プロジェクト用の設定とベストプラクティスを提供します。

## 機械学習特化の依存関係

### 基本パッケージ

```toml
# pyproject.toml に追加
dependencies = [
    # 機械学習コア
    "torch>=X.X.X",
    "numpy>=X.X.X",
    ...

    # 実験管理・可視化
    "wandb>=X.X.X",
    ...

    # データ処理
    "tqdm>=X.X.X",
    ...

    # 設定管理
    "hydra-core>=X.X.X",
    ...
]
```

### GPU環境用の追加設定

```bash
# CUDA環境の場合
uv add torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# MPS (Mac M1/M2) 環境の場合
uv add torch torchvision torchaudio
```

## プロジェクト構造（一例。必要に応じて省略・追加）

```
ml-project/
├── src/
│   └── project_name/
│       ├── data/           # データ処理
│       │   ├── datasets.py
│       │   └── transforms.py
│       ├── models/         # モデル定義
│       │   ├── base.py
│       │   └── networks.py
│       ├── training/       # 学習関連
│       │   ├── trainer.py
│       │   └── callbacks.py
│       ├── evaluation/     # 評価関連
│       │   └── metrics.py
│       └── utils/          # ユーティリティ
│           ├── config.py
│           └── logging.py
├── configs/                # Hydra設定ファイル
│   ├── config.yaml
│   ├── model/
│   ├── data/
│   └── experiment/
├── data/                   # データディレクトリ
│   ├── raw/
│   ├── processed/
│   └── external/
├── experiments/            # 実験結果
├── models/                 # 保存されたモデル
└── wandb/                  # W&B ローカルファイル
```

## Weights & Biases (wandb) 統合

### 初期設定

```bash
# wandb ログイン
uv run wandb login

# プロジェクト初期化
uv run wandb init
```

### 基本的な使用方法

```python
# src/project_name/training/trainer.py
import wandb
import torch
from typing import Any

class MLTrainer:
    def __init__(self, config: dict[str, Any]):
        self.config = config

        # wandb初期化
        wandb.init(
            project=config["project_name"],
            name=config["experiment_name"],
            config=config,
            tags=config.get("tags", []),
        )

        # デバイス設定
        self.device = torch.device(
            "cuda" if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available()
            else "cpu"
        )

    def train_epoch(self, model: torch.nn.Module, dataloader: torch.utils.data.DataLoader, optimizer: torch.optim.Optimizer, criterion: torch.nn.Module):
        """1エポックの学習"""
        model.train()
        total_loss = 0.0

        for batch_idx, (data, target) in enumerate(dataloader):
            data, target = data.to(self.device), target.to(self.device)

            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            # バッチごとのログ
            if batch_idx % self.config["log_interval"] == 0:
                wandb.log({
                    "batch_loss": loss.item(),
                    "batch_idx": batch_idx,
                })

        # エポック終了時のログ
        avg_loss = total_loss / len(dataloader)
        wandb.log({"epoch_loss": avg_loss})

        return avg_loss

    def validate(self, model: torch.nn.Module, dataloader: torch.utils.data.DataLoader, criterion: torch.nn.Module):
        """バリデーション"""
        model.eval()
        val_loss = 0.0
        correct = 0

        with torch.no_grad():
            for data, target in dataloader:
                data, target = data.to(self.device), target.to(self.device)
                output = model(data)
                val_loss += criterion(output, target).item()
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()

        val_loss /= len(dataloader)
        accuracy = 100.0 * correct / len(dataloader.dataset)

        # バリデーション結果をログ
        wandb.log({
            "val_loss": val_loss,
            "val_accuracy": accuracy,
        })

        return val_loss, accuracy

    def save_model(self, model: torch.nn.Module, epoch: int, metrics: dict[str, Any]):
        """モデル保存とwandbへのアーティファクト登録"""
        model_path = f"models/model_epoch_{epoch}.pt"
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'metrics': metrics,
        }, model_path)

        # wandbアーティファクトとして保存
        artifact = wandb.Artifact(
            name=f"model_epoch_{epoch}",
            type="model",
            metadata=metrics
        )
        artifact.add_file(model_path)
        wandb.log_artifact(artifact)
```

### 高度なwandb活用

```python
# src/project_name/utils/wandb_utils.py
import wandb
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any
from collections.abc import Sequence


class WandbLogger:
    @staticmethod
    def log_hyperparameters(config: dict[str, Any]):
        """ハイパーパラメータをテーブルで記録"""
        table = wandb.Table(
            columns=["Parameter", "Value"],
            data=[[k, v] for k, v in config.items()]
        )
        wandb.log({"hyperparameters": table})

    @staticmethod
    def log_confusion_matrix(y_true: Sequence, y_pred: Sequence, class_names: list[str]):
        """混同行列をログ"""
        wandb.log({
            "confusion_matrix": wandb.plot.confusion_matrix(
                y_true=y_true,
                preds=y_pred,
                class_names=class_names
            )
        })

    @staticmethod
    def log_feature_importance(feature_names: list[str], importance: list[float]):
        """特徴量重要度をログ"""
        data = [[name, imp] for name, imp in zip(feature_names, importance)]
        table = wandb.Table(data=data, columns=["Feature", "Importance"])

        wandb.log({
            "feature_importance": wandb.plot.bar(
                table, "Feature", "Importance", title="Feature Importance"
            )
        })

    @staticmethod
    def log_learning_curves(train_losses: list[float], val_losses: list[float]):
        """学習曲線をログ"""
        epochs = list(range(1, len(train_losses) + 1))

        plt.figure(figsize=(10, 6))
        plt.plot(epochs, train_losses, label='Training Loss')
        plt.plot(epochs, val_losses, label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.title('Learning Curves')

        wandb.log({"learning_curves": wandb.Image(plt)})
        plt.close()
```

## 設定管理 (Hydra)

### 基本設定ファイル

```yaml
# configs/config.yaml
defaults:
  - model: resnet
  - data: cifar10
  - experiment: baseline

# 基本設定
project_name: "ml-project"
experiment_name: "baseline_experiment"
seed: 42

# 学習設定
training:
  epochs: 100
  batch_size: 32
  learning_rate: 0.001
  log_interval: 100

# デバイス設定
device: "auto"  # auto, cpu, cuda, mps

# wandb設定
wandb:
  project: "${project_name}"
  tags: ["baseline", "experiment"]
  log_artifacts: true

# パス設定
paths:
  data_dir: "data"
  output_dir: "experiments/${now:%Y-%m-%d_%H-%M-%S}"
  model_dir: "${paths.output_dir}/models"
```

```yaml
# configs/model/resnet.yaml
_target_: torchvision.models.resnet18
pretrained: true
num_classes: 10
```

```yaml
# configs/data/cifar10.yaml
name: "cifar10"
batch_size: 32
num_workers: 4
pin_memory: true

transforms:
  train:
    - _target_: torchvision.transforms.RandomHorizontalFlip
      p: 0.5
    - _target_: torchvision.transforms.ToTensor
    - _target_: torchvision.transforms.Normalize
      mean: [0.485, 0.456, 0.406]
      std: [0.229, 0.224, 0.225]
```

### Hydraを使った学習スクリプト

```python
# scripts/train.py
import hydra
import wandb
from omegaconf import DictConfig, OmegaConf
from pathlib import Path

@hydra.main(version_base=None, config_path="../configs", config_name="config")
def train(cfg: DictConfig) -> None:
    # 設定をwandbに記録
    wandb.init(
        project=cfg.wandb.project,
        name=cfg.experiment_name,
        config=OmegaConf.to_container(cfg, resolve=True),
        tags=cfg.wandb.tags,
    )

    # 出力ディレクトリ作成
    output_dir = Path(cfg.paths.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 設定ファイルを保存
    with open(output_dir / "config.yaml", "w") as f:
        OmegaConf.save(cfg, f)

    # モデル・データローダー・トレーナーの初期化
    # ... (実装)

    print(f"Training started. Output dir: {output_dir}")

if __name__ == "__main__":
    train()
```

## よく使うコマンド

```bash
# 学習実行
uv run python scripts/train.py

# 設定を上書きして実行
uv run python scripts/train.py training.epochs=50 training.batch_size=64

# 異なる実験設定で実行
uv run python scripts/train.py experiment=advanced_experiment

# GPU使用状況確認
nvidia-smi
```

## ベストプラクティス

### 1. モデル評価とデプロイ

```python
# src/project_name/evaluation/evaluator.py
import torch
import wandb
from typing import Any
from sklearn.metrics import classification_report, confusion_matrix

class ModelEvaluator:
    def __init__(self, model: torch.nn.Module, device: torch.device):
        self.model = model
        self.device = device

    def evaluate_classification(self, dataloader: torch.utils.data.DataLoader, class_names: list[str]):
        """分類タスクの詳細評価"""
        self.model.eval()
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for data, target in dataloader:
                data = data.to(self.device)
                output = self.model(data)
                pred = output.argmax(dim=1)

                all_preds.extend(pred.cpu().numpy())
                all_targets.extend(target.cpu().numpy())

        # 詳細レポート作成
        report = classification_report(
            all_targets, all_preds,
            target_names=class_names,
            output_dict=True
        )

        # wandbにログ
        wandb.log({
            "classification_report": wandb.Table(
                data=[[k, v['precision'], v['recall'], v['f1-score']]
                      for k, v in report.items() if isinstance(v, dict)],
                columns=["Class", "Precision", "Recall", "F1-Score"]
            )
        })

        return report
```

## トラブルシューティング

### GPU関連

```bash
# CUDA利用可能か確認
uv run python -c "import torch; print(torch.cuda.is_available())"

# MPS (Mac) 利用可能か確認
uv run python -c "import torch; print(torch.backends.mps.is_available())"

# メモリ使用量確認
uv run python -c "import torch; print(torch.cuda.memory_summary())"
```

### wandb関連

```bash
# wandbキャッシュクリア
uv run wandb artifact cache cleanup

# オフラインモード
export WANDB_MODE=offline

# デバッグモード
export WANDB_DEBUG=true
```

### 依存関係の問題

```bash
# PyTorch互換性確認
uv run python -c "import torch; print(torch.__version__)"

# CUDA対応確認
uv run python -c "import torch; print(torch.version.cuda)"
```

## プロジェクト固有のカスタマイズ例

実際のプロジェクトでは、このガイドを基に以下のような追加を行ってください：

1. **ドメイン固有のデータ処理**
2. **カスタムモデルアーキテクチャ**
3. **特殊な評価指標**
4. **プロダクション環境向けの最適化**
