#!/bin/bash

# 将Git子模块转换为普通文件夹的脚本
# 适用于 AI_hand 项目

echo "========================================"
echo "Git子模块转换脚本"
echo "========================================"
echo ""

# 检查当前目录
if [ ! -d ".git" ]; then
    echo "❌ 错误：请在项目根目录（AI_hand）下运行此脚本"
    echo "当前目录：$(pwd)"
    exit 1
fi

echo "✓ 检测到Git仓库"
echo "当前项目：$(basename $(pwd))"
echo ""

# 备份提示
echo "⚠️  重要提示："
echo "此操作会将子模块转换为普通文件夹"
echo "转换后将无法自动同步原始仓库的更新"
echo ""
read -p "是否继续？(输入 yes 继续): " confirm

if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "开始转换..."
echo ""

# 1. 删除 .gitmodules 文件
if [ -f ".gitmodules" ]; then
    echo "1️⃣ 删除 .gitmodules 文件..."
    rm -f .gitmodules
    echo "   ✓ 完成"
else
    echo "1️⃣ .gitmodules 文件不存在，跳过"
fi

# 2. 删除 .git/modules 目录
if [ -d ".git/modules" ]; then
    echo "2️⃣ 删除 .git/modules 目录..."
    rm -rf .git/modules
    echo "   ✓ 完成"
else
    echo "2️⃣ .git/modules 目录不存在，跳过"
fi

# 3. 删除各个子模块的 .git 文件夹
echo "3️⃣ 删除子模块的 .git 配置..."

submodules=(
    "src/drivers/astra_camera"
    "src/drivers/aubo_ros2"
    "src/drivers/jaka_mini_ros2"
    "third-party/orca_core"
)

for submodule in "${submodules[@]}"; do
    if [ -e "$submodule/.git" ]; then
        echo "   - 处理 $submodule"
        rm -rf "$submodule/.git"
        echo "     ✓ 完成"
    else
        echo "   - $submodule 不存在或已处理"
    fi
done

echo ""
echo "4️⃣ 将所有文件添加到Git..."
git add .

echo ""
echo "5️⃣ 创建提交..."
git commit -m "Convert submodules to regular folders

- Removed .gitmodules
- Converted astra_camera to regular folder
- Converted aubo_ros2 to regular folder  
- Converted jaka_mini_ros2 to regular folder
- Converted orca_core to regular folder"

echo ""
echo "========================================"
echo "✅ 转换完成！"
echo "========================================"
echo ""
echo "接下来的步骤："
echo "1. 在GitHub Desktop中应该能看到1个新的commit"
echo "2. 点击 'Push origin' 按钮上传到GitHub"
echo "3. 之后所有修改都可以正常commit和push了"
echo ""
