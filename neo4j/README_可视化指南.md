# GraphRAG知识图谱可视化指南

本指南将帮助你将GraphRAG生成的知识图谱数据导入Neo4j并进行可视化。

## 📋 目录

1. [准备工作](#准备工作)
2. [数据转换](#数据转换)
3. [导入Neo4j](#导入neo4j)
4. [可视化查看](#可视化查看)
5. [常见问题](#常见问题)

## 🔧 准备工作

### 1. 安装Python依赖

```bash
pip install pandas pyarrow
```

### 2. 准备Neo4j数据库

- 下载并安装Neo4j Community Edition: https://neo4j.com/download/
- 启动Neo4j服务
- 访问Neo4j Browser: http://localhost:7474

## 📊 数据转换

### 方法1: 使用Python脚本（推荐）

```bash
# 基本用法
python convert_graphrag_to_neo4j.py <GraphRAG输出目录>

# 指定输出目录
python convert_graphrag_to_neo4j.py E:\graphrag\graphrag-2.7.0\test_0114-2\output E:\neo4j_import
```

**示例：**
```bash
python convert_graphrag_to_neo4j.py E:\graphrag\graphrag-2.7.0\test_0114-2\output
```

脚本会自动：
- 读取 `entities.parquet` 和 `relationships.parquet`
- 检测字段结构
- 转换为Neo4j标准CSV格式
- 输出到 `neo4j_import` 目录

### 方法2: 手动转换（了解数据结构后）

如果你熟悉数据结构，也可以手动编写转换脚本。

## 📥 导入Neo4j

### 步骤1: 复制CSV文件到Neo4j import目录

将生成的CSV文件复制到Neo4j的import目录：
- Windows: `neo4j安装目录\import\`
- Linux/Mac: `neo4j安装目录/import/`

例如：
```bash
copy nodes.csv "C:\Program Files\Neo4j\neo4j-community-5.x.x\import\"
copy relationships.csv "C:\Program Files\Neo4j\neo4j-community-5.x.x\import\"
```

### 步骤2: 在Neo4j Browser中执行导入

打开Neo4j Browser (http://localhost:7474)，执行以下Cypher语句：

#### 2.1 导入节点

```cypher
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CREATE (n:Entity {id: row.`:ID`})
SET n += row
REMOVE n.`:ID`, n.`:LABEL`
RETURN count(n) AS nodesCreated;
```

#### 2.2 创建索引（提高查询速度）

```cypher
CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id);
```

#### 2.3 导入关系

```cypher
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (source:Entity {id: row.`:START_ID`})
MATCH (target:Entity {id: row.`:END_ID`})
CREATE (source)-[r:RELATED_TO]->(target)
SET r += row
REMOVE r.`:START_ID`, r.`:END_ID`, r.`:TYPE`
RETURN count(r) AS relationshipsCreated;
```

**注意：** 如果关系有多种类型，需要使用APOC插件或分别处理每种类型。

### 步骤3: 验证导入结果

```cypher
// 查看节点统计
MATCH (n)
RETURN labels(n) AS Label, count(n) AS Count
ORDER BY Count DESC;

// 查看关系统计
MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC;
```

## 🎨 可视化查看

### 1. 使用Neo4j Browser可视化

在Neo4j Browser中执行查询，结果会自动以图形方式显示：

```cypher
// 查看图谱概览（限制100个节点）
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100;
```

```cypher
// 查看特定节点及其邻居
MATCH (n {id: '某个实体ID'})-[r]-(m)
RETURN n, r, m;
```

```cypher
// 查看度中心性最高的节点
MATCH (n)
RETURN n.id AS NodeID, 
       size((n)--()) AS Degree
ORDER BY Degree DESC
LIMIT 20;
```

### 2. 使用Neo4j Bloom（商业版）

Neo4j Bloom提供了更强大的可视化功能，支持：
- 交互式图谱探索
- 样式自定义
- 搜索和过滤
- 路径分析

### 3. 使用Python可视化（NetworkX + Matplotlib）

如果需要自定义可视化，可以使用Python：

```python
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# 读取数据
nodes_df = pd.read_csv('nodes.csv')
rels_df = pd.read_csv('relationships.csv')

# 创建图
G = nx.DiGraph()

# 添加节点
for _, row in nodes_df.iterrows():
    G.add_node(row[':ID'], **row.to_dict())

# 添加边
for _, row in rels_df.iterrows():
    G.add_edge(row[':START_ID'], row[':END_ID'], 
               type=row.get(':TYPE', 'RELATED_TO'))

# 可视化
plt.figure(figsize=(20, 20))
pos = nx.spring_layout(G, k=0.5, iterations=50)
nx.draw(G, pos, with_labels=True, node_size=500, 
        font_size=8, arrows=True, alpha=0.6)
plt.title("GraphRAG Knowledge Graph")
plt.savefig('knowledge_graph.png', dpi=300, bbox_inches='tight')
plt.show()
```

## ❓ 常见问题

### Q1: 导入时提示文件找不到

**A:** 确保CSV文件在Neo4j的import目录中，并且使用 `file:///` 前缀（注意三个斜杠）。

### Q2: 导入速度很慢

**A:** 
- 使用 `neo4j-admin import` 命令进行批量导入（需要数据库为空）
- 创建索引提高匹配速度
- 分批导入数据

### Q3: 关系类型显示不正确

**A:** 检查relationships.csv中的`:TYPE`列是否正确。如果关系类型多样，可能需要分别处理每种类型。

### Q4: 节点标签显示不正确

**A:** 检查nodes.csv中的`:LABEL`列。多个标签用分号分隔。

### Q5: 如何导出可视化图片

**A:** 
- Neo4j Browser: 点击右上角的导出按钮
- Python: 使用matplotlib保存图片
- Neo4j Bloom: 支持导出高质量图片

## 📚 更多资源

- [Neo4j Cypher手册](https://neo4j.com/docs/cypher-manual/)
- [Neo4j Browser使用指南](https://neo4j.com/docs/browser-manual/)
- [GraphRAG文档](https://github.com/microsoft/graphrag)

## 🔄 完整导入流程示例

```bash
# 1. 转换数据
python convert_graphrag_to_neo4j.py E:\graphrag\graphrag-2.7.0\test_0114-2\output

# 2. 复制到Neo4j import目录
copy E:\graphrag\graphrag-2.7.0\test_0114-2\output\neo4j_import\*.csv "C:\Program Files\Neo4j\neo4j-community-5.x.x\import\"

# 3. 在Neo4j Browser中执行import_to_neo4j.cypher中的语句

# 4. 查看可视化结果
```

---

**提示：** 如果遇到问题，请检查：
1. CSV文件编码是否为UTF-8
2. Neo4j服务是否正常运行
3. import目录权限是否正确
4. 数据量是否过大（可能需要分批导入）




