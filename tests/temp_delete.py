import os

# 删除重复的组件文件
files_to_delete = [
    "examples/multiagent_collaboration/cells/mention_processor_cell.py",
    "examples/multiagent_collaboration/cells/user_memory_cell.py",
    "examples/multiagent_team_static/cells/mention_processor_cell.py", 
    "examples/multiagent_team_static/cells/user_memory_cell.py"
]

for file_path in files_to_delete:
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"删除了重复文件: {file_path}")
    else:
        print(f"文件不存在: {file_path}")

print("清理完成！")