# 简单测试脚本，用于检查app.py的语法和导入问题
import sys

print("开始测试app.py...")

try:
    # 尝试导入app模块
    import app
    print("app.py导入成功！")
except Exception as e:
    print(f"导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("测试完成")