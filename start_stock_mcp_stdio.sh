#!/usr/bin/env zsh
# ------------------------------------------------------------
#  MCP stdio 启动脚本 – 适配 VS Code/LocalProcess
# ------------------------------------------------------------

# 切换到脚本所在目录（项目根目录）
cd "$(dirname "$0")"

# 加载 conda（非交互式）
export CONDA_BASE=$(conda info --base)
source "${CONDA_BASE}/etc/profile.d/conda.sh"

# 激活项目的 conda 环境
conda activate stock-mcp

# 确保 src 包在 PYTHONPATH
export PYTHONPATH=$(pwd)

# 启动 FastMCP（阻塞），使用 stdio 传输
python -c "import src.server.mcp.server as m; m.create_mcp_server().run(transport='stdio')"

