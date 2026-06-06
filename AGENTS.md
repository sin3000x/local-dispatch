# AGENTS.md

## 项目概览

这是一个用于 ESD 发货排程的 Python 项目，核心目标是：在给定发货产能的前提下，为多个分组（车辆）安排合适的发货时间。

## 文件结构

### 根目录
- `pyproject.toml`：项目配置、依赖和 Python 版本要求。
- `uv.lock`：`uv` 的锁定文件，用于固定依赖版本。
- `.python-version`：本地 Python 版本提示。
- `.gitignore`：Git 忽略规则。
- `notes.md`：业务背景说明。
- `AGENTS.md`：给 AI/协作者看的项目说明。

### 代码目录
- `local-dispatch/src/`：已被添加到 `PYTHONPATH`，因此这里面的模块可以直接按包名导入，不需要额外处理路径。
- `local-dispatch/src/algo/`
  - `esd_schedule.py`：ESD 排程核心算法 `ESDScheduler`。
- `local-dispatch/src/dto/`
  - `esd_schedule_data.py`：调度输入/输出数据结构，以及 `Group`、`DeliveryCapacity` 等 DTO。
- `local-dispatch/src/aipaas/`
  - `logger_factory.py`：日志相关封装。

### 测试目录
- `tests/`
  - `test_esd_scheduler.py`：排程算法测试。
  - `test_esd_schedule_data.py`：数据结构测试。
  - `conftest.py`：pytest 通用测试配置。
- `tests/helpers/`
  - `esd_schedule_fixtures.py`：测试数据/夹具。
  - `esd_schedule_viz.py`：测试可视化辅助工具。

## 工作约定

- 使用 `uv` 管理 Python 环境并执行命令：如用 `uv run pytest` 来执行测试。
- 代码变更后优先补充或更新对应测试。
- 调整算法时，重点关注 `local-dispatch/src/algo/esd_schedule.py` 与 `tests/test_esd_scheduler.py` 的一致性。
