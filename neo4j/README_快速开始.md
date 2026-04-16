# GraphRAG数据导入Neo4j - 快速开始指南

本指南帮助你快速将GraphRAG生成的知识图谱数据导入到Neo4j中。

## 📋 前提条件

1. ✅ 已安装Neo4j Desktop
2. ✅ 已在Neo4j Desktop中创建数据库（名称：graphrag2.7.0）
3. ✅ 已运行 `convert_graphrag_to_neo4j.py` 生成CSV文件

## 🚀 快速导入（一键完成）

### 步骤1: 自动复制CSV文件到Neo4j

```powershell
.\import_to_neo4j_auto.ps1
```

这个脚本会：
- 自动找到你的数据库（graphrag2.7.0）
- 找到import目录
- 复制CSV文件到正确位置

### 步骤2: 启动Neo4j

**方法A: 使用Neo4j Desktop（推荐）**
1. 在Neo4j Desktop中启动数据库
2. 点击 "Open" 打开Browser

**方法B: 使用命令行**
```powershell
.\start_neo4j.ps1
```

### 步骤3: 在Browser中执行导入

1. 访问 http://localhost:7474（如果使用命令行启动）
2. 登录（默认：neo4j/neo4j）
3. 复制并执行 `import_to_neo4j.cypher` 文件中的语句

## 📝 详细步骤

### 1. 数据转换

如果还没有CSV文件，先运行转换脚本：

```powershell
python convert_graphrag_to_neo4j.py E:\graphrag\graphrag-2.7.0\test_0114-2\output
```

这会生成：
- `nodes.csv` - 节点文件
- `relationships.csv` - 关系文件

### 2. 自动导入脚本

运行自动导入脚本：

```powershell
.\import_to_neo4j_auto.ps1
```

**自定义参数：**
```powershell
# 指定不同的数据库名称
.\import_to_neo4j_auto.ps1 -DatabaseName "my-database"

# 指定不同的源目录
.\import_to_neo4j_auto.ps1 -SourceDir "E:\other\path\neo4j_import"
```

### 3. 启动Neo4j

```powershell
# 使用默认数据库（graphrag2.7.0）
.\start_neo4j.ps1

# 或指定数据库名称
.\start_neo4j.ps1 -DatabaseName "graphrag2.7.0"
```

### 4. 执行导入语句

在Neo4j Browser中执行以下语句（来自 `import_to_neo4j.cypher`）：

```cypher
// 导入节点
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CREATE (n:Entity {id: row.`:ID`})
SET n += row
REMOVE n.`:ID`, n.`:LABEL`
RETURN count(n) AS nodesCreated;

// 创建索引
CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id);

// 导入关系
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (source:Entity {id: row.`:START_ID`})
MATCH (target:Entity {id: row.`:END_ID`})
CREATE (source)-[r:RELATED_TO]->(target)
SET r += row
REMOVE r.`:START_ID`, r.`:END_ID`, r.`:TYPE`
RETURN count(r) AS relationshipsCreated;
```

### 5. 查看结果

```cypher
// 查看统计
MATCH (n)
RETURN labels(n) AS Label, count(n) AS Count
ORDER BY Count DESC;

// 查看图谱
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100;
```

## 🛠️ 可用脚本

| 脚本 | 功能 | 用法 |
|------|------|------|
| `find_neo4j_databases.ps1` | 查找所有数据库 | `.\find_neo4j_databases.ps1` |
| `import_to_neo4j_auto.ps1` | 自动复制CSV文件 | `.\import_to_neo4j_auto.ps1` |
| `start_neo4j.ps1` | 启动Neo4j | `.\start_neo4j.ps1` |
| `stop_neo4j.ps1` | 停止Neo4j | `.\stop_neo4j.ps1` |
| `convert_graphrag_to_neo4j.py` | 转换Parquet为CSV | `python convert_graphrag_to_neo4j.py <输入目录>` |

## ⚠️ 常见问题

### Q1: 找不到数据库

**错误**: `未找到数据库目录`

**解决**:
1. 确保在Neo4j Desktop中已创建数据库
2. 检查数据库名称是否正确
3. 运行 `.\find_neo4j_databases.ps1` 查看所有数据库

### Q2: CSV文件不存在

**错误**: `未找到 nodes.csv`

**解决**:
1. 先运行 `convert_graphrag_to_neo4j.py` 生成CSV文件
2. 检查源目录路径是否正确

### Q3: 导入失败

**可能原因**:
- CSV文件格式不正确
- 文件编码不是UTF-8
- import目录路径配置错误

**解决**:
1. 检查CSV文件是否在import目录中
2. 确保文件编码为UTF-8
3. 查看Neo4j日志获取详细错误信息

### Q4: 端口被占用

**错误**: 启动失败，端口被占用

**解决**:
```powershell
# 检查端口占用
netstat -ano | findstr :7474
netstat -ano | findstr :7687

# 停止Neo4j
.\stop_neo4j.ps1
```

## 📊 数据统计

导入完成后，你可以查看：

- **节点数量**: 4875个实体
- **关系数量**: 4325个关系
- **文件大小**: 
  - nodes.csv: ~2MB
  - relationships.csv: ~1.3MB

## 🔗 相关文件

- `import_to_neo4j.cypher` - 导入Cypher语句
- `README_可视化指南.md` - 详细可视化指南
- `README_Neo4j启动指南.md` - Neo4j启动详细说明

## 💡 提示

- 首次导入可能需要几分钟时间
- 建议在导入前创建索引以提高速度
- 如果数据量大，可以分批导入
- 导入完成后建议运行统计查询验证数据

---

**快速命令总结**:
```powershell
# 1. 转换数据（如果还没做）
python convert_graphrag_to_neo4j.py E:\graphrag\graphrag-2.7.0\test_0114-2\output

# 2. 自动导入
.\import_to_neo4j_auto.ps1

# 3. 启动Neo4j
.\start_neo4j.ps1

# 4. 在Browser中执行导入语句（import_to_neo4j.cypher）

# 5. 完成后停止
.\stop_neo4j.ps1
```




