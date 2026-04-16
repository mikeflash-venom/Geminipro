# Neo4j Desktop 命令行启动指南

本指南帮助你在已安装Neo4j Desktop的情况下，使用命令行方式启动和管理Neo4j数据库。

## 📁 文件说明

- `find_neo4j_databases.ps1` - 查找Neo4j Desktop管理的所有数据库
- `start_neo4j.ps1` - 启动Neo4j数据库
- `stop_neo4j.ps1` - 停止Neo4j数据库

## 🚀 快速开始

### 1. 查找数据库

首先运行查找脚本，查看所有可用的数据库：

```powershell
.\find_neo4j_databases.ps1
```

这会显示：
- 所有数据库的名称和版本
- 每个数据库的安装路径
- bin目录位置
- import目录位置（用于导入CSV文件）

### 2. 启动Neo4j

```powershell
# 自动选择第一个数据库（如果有多个会提示选择）
.\start_neo4j.ps1

# 或指定数据库名称
.\start_neo4j.ps1 -DatabaseName "你的数据库名"
```

启动成功后：
- 访问 http://localhost:7474 打开Neo4j Browser
- 默认用户名：`neo4j`
- 默认密码：`neo4j`（首次登录需要修改）

### 3. 停止Neo4j

```powershell
.\stop_neo4j.ps1
```

## 📋 使用示例

### 完整工作流程

```powershell
# 1. 查找数据库
.\find_neo4j_databases.ps1

# 2. 启动Neo4j
.\start_neo4j.ps1

# 3. 在Neo4j Browser中导入数据（访问 http://localhost:7474）
# 执行 import_to_neo4j.cypher 中的语句

# 4. 停止Neo4j（完成后）
.\stop_neo4j.ps1
```

## 🔧 导入GraphRAG数据

### 步骤1: 找到import目录

运行 `find_neo4j_databases.ps1`，它会显示每个数据库的import目录路径。

### 步骤2: 复制CSV文件

将转换好的CSV文件复制到import目录：

```powershell
# 示例（根据实际路径调整）
$importPath = "C:\Users\你的用户名\AppData\Roaming\Neo4j Desktop\Application\neo4jDatabases\database-xxx\installation-xxx\import"

# 复制文件
Copy-Item "E:\graphrag\graphrag-2.7.0\test_0114-2\output\neo4j_import\nodes.csv" -Destination $importPath
Copy-Item "E:\graphrag\graphrag-2.7.0\test_0114-2\output\neo4j_import\relationships.csv" -Destination $importPath
```

### 步骤3: 启动Neo4j并导入

```powershell
# 启动Neo4j
.\start_neo4j.ps1

# 然后在Neo4j Browser (http://localhost:7474) 中执行导入语句
# 参考 import_to_neo4j.cypher 文件
```

## ⚠️ 注意事项

1. **权限问题**：如果遇到权限错误，请以管理员身份运行PowerShell

2. **端口占用**：
   - Neo4j HTTP端口：7474
   - Neo4j Bolt端口：7687
   - 确保这些端口未被占用

3. **数据库状态**：
   - 如果数据库已在Neo4j Desktop中运行，命令行启动可能会失败
   - 建议先在Neo4j Desktop中停止数据库，再使用命令行启动

4. **首次使用**：
   - 如果Neo4j Desktop中没有数据库，请先在Desktop中创建一个数据库
   - 然后才能使用这些脚本

## 🐛 故障排除

### 问题1: 找不到数据库

**错误信息**：`未找到Neo4j数据库目录`

**解决方案**：
1. 确保已安装Neo4j Desktop
2. 在Neo4j Desktop中至少创建一个数据库
3. 检查路径：`%APPDATA%\Neo4j Desktop\Application\neo4jDatabases`

### 问题2: 找不到neo4j-admin.bat

**错误信息**：`未找到neo4j-admin.bat`

**解决方案**：
1. 运行 `find_neo4j_databases.ps1` 查看实际路径
2. 确保数据库已完全安装（在Neo4j Desktop中启动一次）

### 问题3: 启动失败

**可能原因**：
- 端口被占用
- 数据库已在运行
- Java环境问题

**解决方案**：
```powershell
# 检查端口占用
netstat -ano | findstr :7474
netstat -ano | findstr :7687

# 检查Java
java -version
```

## 📚 相关文件

- `convert_graphrag_to_neo4j.py` - GraphRAG数据转换脚本
- `import_to_neo4j.cypher` - Neo4j导入Cypher语句
- `README_可视化指南.md` - 完整可视化指南

## 💡 提示

- 这些脚本会自动查找Neo4j Desktop管理的数据库
- 如果有多个数据库，脚本会提示你选择
- 所有路径都是自动检测的，无需手动配置




