// Neo4j导入脚本 - 使用LOAD CSV导入GraphRAG数据
// 使用方法：在Neo4j Browser中执行这些Cypher语句

// ============================================
// 步骤1: 导入节点（实体）
// ============================================
// 注意：确保nodes.csv文件已放在Neo4j的import目录中
// 默认路径：neo4j安装目录/import/nodes.csv

// 方法1: 简单导入（使用默认标签Entity）
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CREATE (n:Entity {id: row.`:ID`})
SET n += row
REMOVE n.`:ID`, n.`:LABEL`
RETURN count(n) AS nodesCreated;

// 方法2: 处理多个标签（如果:LABEL列包含分号分隔的多个标签）
// 注意：这个方法会为每个标签创建单独的节点，如果需要合并，请使用APOC插件
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row, split(row.`:LABEL`, ';') AS labels
UNWIND labels AS label
CREATE (n)
SET n:`Entity`
SET n.id = row.`:ID`
SET n += row
REMOVE n.`:ID`, n.`:LABEL`
WITH n, label
WHERE label <> 'Entity' AND label <> ''
SET n:`Entity`:`${label}`
RETURN count(n) AS nodesCreated;

// ============================================
// 步骤2: 创建节点索引（提高导入速度）
// ============================================
CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id);

// ============================================
// 步骤3: 导入关系
// ============================================
// 注意：确保relationships.csv文件已放在Neo4j的import目录中

// 方法1: 使用固定关系类型RELATED_TO（推荐，简单快速）
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
MATCH (source:Entity {id: row.`:START_ID`})
MATCH (target:Entity {id: row.`:END_ID`})
CREATE (source)-[r:RELATED_TO]->(target)
SET r += row
REMOVE r.`:START_ID`, r.`:END_ID`, r.`:TYPE`
RETURN count(r) AS relationshipsCreated;

// 方法2: 根据:TYPE列动态创建关系（需要先查看有哪些关系类型）
// 首先查看所有关系类型：
// LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
// RETURN DISTINCT row.`:TYPE` AS RelationshipType;

// 然后为每种关系类型分别导入（示例）：
// LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
// WHERE row.`:TYPE` = '某种关系类型'
// MATCH (source:Entity {id: row.`:START_ID`})
// MATCH (target:Entity {id: row.`:END_ID`})
// CREATE (source)-[r:某种关系类型]->(target)
// SET r += row
// REMOVE r.`:START_ID`, r.`:END_ID`, r.`:TYPE`
// RETURN count(r) AS relationshipsCreated;

// 方法3: 使用APOC插件动态创建关系类型（需要安装APOC插件）
// LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
// MATCH (source:Entity {id: row.`:START_ID`})
// MATCH (target:Entity {id: row.`:END_ID`})
// CALL apoc.create.relationship(source, row.`:TYPE`, {}, target) YIELD rel
// SET rel += row
// REMOVE rel.`:START_ID`, rel.`:END_ID`, rel.`:TYPE`
// RETURN count(rel) AS relationshipsCreated;

// ============================================
// 步骤4: 查看导入结果统计
// ============================================

// 查看节点数量
MATCH (n)
RETURN labels(n) AS Label, count(n) AS Count
ORDER BY Count DESC;

// 查看关系类型统计
MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC;

// 查看图谱概览（限制数量）
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50;

// ============================================
// 步骤5: 查看特定节点及其关系
// ============================================

// 查看某个节点的所有关系
MATCH (n {id: '某个实体ID'})-[r]-(m)
RETURN n, r, m;

// 查看节点的度（连接数）
MATCH (n)
RETURN n.id AS NodeID, 
       size((n)--()) AS Degree
ORDER BY Degree DESC
LIMIT 20;

