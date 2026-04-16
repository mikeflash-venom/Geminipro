# GraphRAG 跨段落抽取配置说明

本目录下的脚本只负责「GraphRAG 输出 → Neo4j CSV」的转换，**不包含 GraphRAG 的抽取与索引代码**。  
要让图谱里出现更多**跨段落的实体与关系**，需要在 **你自己的 GraphRAG 项目**里改配置并重新跑索引。

---

## 1. 配置文件在哪

GraphRAG 的配置在 **GraphRAG 项目根目录** 的 `settings.yml`（或 `settings.json`）里，例如：

- `E:\graphrag\graphrag-2.7.0\你的数据项目\settings.yml`
- 或你执行 `graphrag index` 时所在目录下的 `settings.yml`

本仓库里的 **`graphrag_settings_跨段落示例.yml`** 是一份**可复制粘贴的片段**，用于合并进你的 `settings.yml`，而不是替代整个文件。

---

## 2. 要改哪些配置

在 **`graphrag_settings_跨段落示例.yml`** 里，重点有两块：

| 配置块 | 作用 | 建议值 |
|--------|------|--------|
| **chunks.size** | 每个文本块的最大 token 数。调大后，一个块内包含更多段落，有利于跨段落抽取 | 600～1200（默认常为 300，可先试 800） |
| **chunks.overlap** | 相邻块之间的重叠 token 数。有重叠时，同一内容会出现在多块中，便于合并同一实体、发现跨块关系 | 50～100（默认多为 0） |
| **extract_graph.max_gleanings** | Gleaning 轮数。每多一轮会在上一轮基础上再抽一轮，能发现更多跨块关系 | 2 或 3（默认多为 1） |

其它如 `chunks.strategy`、`group_by_columns` 等可按注释和你的数据格式酌情设置。

---

## 3. 怎么合并进你的 settings.yml

1. 打开你 **GraphRAG 项目** 里的 `settings.yml`。
2. 打开本仓库里的 **`graphrag_settings_跨段落示例.yml`**。
3. 把示例里的 **`chunks`** 和 **`extract_graph`** 整段复制进你的 `settings.yml`；若已有同名字段，用示例中的键值**替换或合并**，注意 YAML 缩进（一般 2 空格）。
4. 保存后，在 GraphRAG 项目目录下重新执行索引，例如：
   ```bash
   graphrag index
   ```
5. 索引完成后，用本仓库的转换脚本把新输出转成 CSV，再导入 Neo4j：
   ```bash
   python convert_graphrag_to_neo4j.py <你的GraphRAG输出目录> [输出目录]
   python import_to_neo4j_sandbox.py ./outcsv/output/neo4j_import/nodes.csv ./outcsv/output/neo4j_import/relationships.csv
   ```

---

## 4. 预期效果与注意点

- **效果**：同一主题在不同段落/块里出现的实体会更容易被连成一条关系；整张图会更连通、「散点」会减少。
- **代价**：`chunks.size` 增大、`max_gleanings` 增加都会让索引变慢、占用更多内存/API，建议先用较小数据试一版再全量跑。
- **数据位置**：你的 GraphRAG 输出目录可能是 `E:\graphrag\graphrag-2.7.0\xxx\output` 或本仓库下的 `outcsv\output`，请以你实际跑 `graphrag index` 的输出路径为准。

如有报错或希望针对你的数据结构做更细的配置，可以把当前 `settings.yml` 里与 `chunks`、`extract_graph` 相关的部分贴出来，再一起改。
