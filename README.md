# pytorch-trainer

## Requirements

* `Python 3.7`

```bash
pip install -r requirements/runtime.txt
# For development
pip install -r requirements/dev.txt
```

* Pycocotool

```bash
pip install "git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI"
```

## Pre-commit Hook

> for DEV

```bash
pip install pre-commit
pre-commit install
```

## Config

> Fix the version `fvcore` to `0.1.2.post20210128`

* Support multiple inheritance of config

## Demo

epoch base trainer

```bash
python examples/train_cifar10.py -cfg configs/pytorch_trainer/epoch_trainer.yaml
```

iteration base trainer

```bash
python examples/train_cifar10.py -cfg configs/pytorch_trainer/iter_trainer.yaml
```
