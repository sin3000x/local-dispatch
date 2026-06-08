import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "local-dispatch"
SRC_DIR = PROJECT_DIR / "src"

# 让测试同时能够导入 `src.*` 和 `dto.*` 两种写法。
# 业务代码里已经固定使用 `from dto.esd_schedule_data import ...`，
# 所以这里通过测试环境补齐 Python 路径，不去改动源码本身。
TESTS_DIR = ROOT / "tests"

# 同时把 tests 目录加入路径，方便让测试里的 `aipaas` mock 包优先被解析到。
for path in (str(TESTS_DIR), str(PROJECT_DIR), str(SRC_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)


def pytest_addoption(parser):
    parser.addoption(
        "--plot",
        action="store_true",
        default=False,
        help="Show Plotly figures during tests.",
    )


@pytest.fixture
def show_plot(request):
    return request.config.getoption("--plot")
