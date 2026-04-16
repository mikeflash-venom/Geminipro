#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GraphRAG知识图谱可视化工具 - 无需Neo4j
直接读取Parquet或CSV文件并生成可视化图片
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import json

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def load_data(input_dir):
    """加载GraphRAG数据（支持Parquet和CSV）"""
    input_path = Path(input_dir)

    # 优先读取CSV文件
    nodes_csv = input_path / "nodes.csv"
    rels_csv = input_path / "relationships.csv"

    if nodes_csv.exists() and rels_csv.exists():
        print("读取CSV文件...")
        nodes_df = pd.read_csv(nodes_csv)
        rels_df = pd.read_csv(rels_csv)
        return nodes_df, rels_df, 'csv'

    # 读取Parquet文件
    nodes_parquet = input_path / "entities.parquet"
    rels_parquet = input_path / "relationships.parquet"

    if nodes_parquet.exists() and rels_parquet.exists():
        print("读取Parquet文件...")
        engines = ['auto', 'pyarrow', 'fastparquet']
        nodes_df = None
        rels_df = None

        for engine in engines:
            try:
                nodes_df = pd.read_parquet(nodes_parquet, engine=engine)
                rels_df = pd.read_parquet(rels_parquet, engine=engine)
                print(f"成功使用 {engine} 引擎读取")
                break
            except:
                continue

        if nodes_df is None:
            raise Exception("无法读取Parquet文件")

        return nodes_df, rels_df, 'parquet'

    raise FileNotFoundError("找不到数据文件")


def create_id_mapping(nodes_df):
    """创建节点ID映射（从title到ID）"""
    id_map = {}

    # 查找ID列
    id_col = None
    for col in ['id', ':ID', 'entity_id']:
        if col in nodes_df.columns:
            id_col = col
            break

    # 查找title列
    title_col = None
    for col in ['title', 'name', 'human_readable_id']:
        if col in nodes_df.columns:
            title_col = col
            break

    if id_col and title_col:
        for _, row in nodes_df.iterrows():
            title = str(row[title_col])
            node_id = str(row[id_col])
            id_map[title] = node_id

    return id_map, id_col, title_col


def build_graph(nodes_df, rels_df, id_map=None):
    """构建NetworkX图"""
    G = nx.DiGraph()

    # 获取节点ID列
    id_col = None
    for col in ['id', ':ID', 'entity_id']:
        if col in nodes_df.columns:
            id_col = col
            break

    if not id_col:
        raise ValueError("找不到节点ID列")

    # 添加节点
    print("添加节点...")
    for _, row in nodes_df.iterrows():
        node_id = str(row[id_col])

        # 获取节点属性
        attrs = {}
        for col in nodes_df.columns:
            if col != id_col:
                val = row[col]
                if pd.notna(val):
                    # 处理复杂类型
                    if isinstance(val, (list, dict)):
                        attrs[col] = json.dumps(val, ensure_ascii=False)
                    else:
                        attrs[col] = str(val)

        G.add_node(node_id, **attrs)

    print(f"已添加 {G.number_of_nodes()} 个节点")

    # 添加边
    print("添加关系...")
    source_col = None
    target_col = None

    for col in ['source', ':START_ID', 'from']:
        if col in rels_df.columns:
            source_col = col
            break

    for col in ['target', ':END_ID', 'to']:
        if col in rels_df.columns:
            target_col = col
            break

    if not source_col or not target_col:
        raise ValueError("找不到关系起始/结束节点列")

    # 检查source/target是ID还是title
    sample_start = str(rels_df[source_col].iloc[0]) if len(rels_df) > 0 else ""
    is_uuid = len(sample_start) == 36 and '-' in sample_start and sample_start.count('-') == 4

    added_edges = 0
    missing_nodes = set()

    for _, row in rels_df.iterrows():
        source = str(row[source_col])
        target = str(row[target_col])

        # 如果不是UUID格式，尝试通过title映射到ID
        if not is_uuid and id_map:
            source = id_map.get(source, source)
            target = id_map.get(target, target)

        # 只添加存在的节点之间的边
        if source in G and target in G:
            rel_type = row.get('type', row.get(':TYPE', 'RELATED_TO'))
            attrs = {'type': str(rel_type)}

            # 添加其他属性
            for col in rels_df.columns:
                if col not in [source_col, target_col, ':START_ID', ':END_ID', 'type', ':TYPE']:
                    val = row[col]
                    if pd.notna(val):
                        if isinstance(val, (list, dict)):
                            attrs[col] = json.dumps(val, ensure_ascii=False)
                        else:
                            attrs[col] = str(val)

            G.add_edge(source, target, **attrs)
            added_edges += 1
        else:
            if source not in G:
                missing_nodes.add(source)
            if target not in G:
                missing_nodes.add(target)

    if missing_nodes:
        print(f"警告: {len(missing_nodes)} 个节点在关系中存在但不在节点列表中")

    print(f"已添加 {added_edges} 条关系")
    return G


def visualize_graph(G, output_file='knowledge_graph.png', layout='spring', show_labels=True, max_nodes_for_labels=100):
    """可视化图谱"""
    print(f"\n生成可视化 (布局: {layout})...")

    # 如果节点太多，使用子图
    if G.number_of_nodes() > 1000:
        print("节点数量较多，使用度中心性最高的节点...")
        degrees = dict(G.degree())
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:1000]
        top_node_ids = [n[0] for n in top_nodes]
        # 使用ID子图，而不是(top_node, degree)元组
        G = G.subgraph(top_node_ids).copy()

    # 选择布局
    if layout == 'spring':
        pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)

    # 创建图形
    fig, ax = plt.subplots(figsize=(24, 24))

    # 根据节点度设置节点大小
    degrees = dict(G.degree())
    node_sizes = [300 + degrees.get(node, 0) * 50 for node in G.nodes()]

    # 根据标签设置节点颜色
    node_colors = []
    for node in G.nodes():
        labels = G.nodes[node].get(':LABEL', G.nodes[node].get('type', 'Entity'))
        if isinstance(labels, str):
            labels = labels.split(';')
        if 'ATTRIBUTE' in labels:
            node_colors.append('#FF6B6B')  # 红色
        elif 'OBJECT' in labels:
            node_colors.append('#4ECDC4')  # 青色
        else:
            node_colors.append('#95E1D3')  # 浅绿色

    # 绘制节点
    nx.draw_networkx_nodes(G, pos,
                           node_color=node_colors if node_colors else 'lightblue',
                           node_size=node_sizes,
                           alpha=0.8,
                           ax=ax)

    # 绘制边
    nx.draw_networkx_edges(G, pos,
                           edge_color='gray',
                           alpha=0.4,
                           arrows=True,
                           arrowsize=15,
                           arrowstyle='->',
                           width=1.5,
                           ax=ax)

    # 绘制标签
    if show_labels and G.number_of_nodes() <= max_nodes_for_labels:
        # 获取节点标题
        labels = {}
        for node in G.nodes():
            node_data = G.nodes[node]
            # 尝试获取title或name
            title = node_data.get('title', node_data.get('name', str(node)[:15]))
            labels[node] = str(title)[:20]  # 限制长度

        nx.draw_networkx_labels(G, pos, labels,
                                font_size=7,
                                font_family='sans-serif',
                                ax=ax)

    # 设置标题
    ax.set_title(f'GraphRAG Knowledge Graph\n{G.number_of_nodes()} nodes, {G.number_of_edges()} edges',
                 fontsize=20, pad=20)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✓ 可视化图片已保存: {output_file}")

    # 显示统计
    print("\n" + "=" * 50)
    print("图谱统计信息:")
    print("=" * 50)
    print(f"节点数: {G.number_of_nodes()}")
    print(f"边数: {G.number_of_edges()}")
    if G.number_of_nodes() > 0:
        print(f"平均度: {sum(degrees.values()) / G.number_of_nodes():.2f}")
    else:
        print("平均度: NA (图为空)")

    # 度中心性最高的节点
    if G.number_of_nodes() > 0:
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        print("\n度中心性最高的10个节点:")
        for i, (node, degree) in enumerate(top_nodes, 1):
            node_data = G.nodes[node]
            title = node_data.get('title', node_data.get('name', node))
            print(f"  {i}. {str(title)[:50]} (度: {degree})")

    plt.close()


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("GraphRAG知识图谱可视化工具")
        print("=" * 60)
        print("\n用法:")
        print("  python visualize_graphrag.py <数据目录> [输出文件] [布局]")
        print("\n参数:")
        print("  数据目录: GraphRAG输出目录或neo4j_import目录")
        print("  输出文件: 图片文件名（默认: knowledge_graph.png）")
        print("  布局: spring/circular/kamada_kawai（默认: spring）")
        print("\n示例:")
        print("  python visualize_graphrag.py E:\\graphrag\\graphrag-2.7.0\\test_0114-2\\output")
        print(
            "  python visualize_graphrag.py E:\\graphrag\\graphrag-2.7.0\\test_0114-2\\output\\neo4j_import kg.png spring")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'knowledge_graph.png'
    layout = sys.argv[3] if len(sys.argv) > 3 else 'spring'

    try:
        # 加载数据
        nodes_df, rels_df, data_type = load_data(input_dir)
        print(f"\n数据加载完成:")
        print(f"  节点数: {len(nodes_df)}")
        print(f"  关系数: {len(rels_df)}")
        print(f"  数据类型: {data_type}")

        # 创建ID映射（如果需要）
        id_map, id_col, title_col = create_id_mapping(nodes_df)
        if id_map:
            print(f"  已创建 {len(id_map)} 个节点的ID映射")

        # 构建图
        G = build_graph(nodes_df, rels_df, id_map)

        # 可视化
        visualize_graph(G, output_file, layout)

        print("\n" + "=" * 50)
        print("✓ 完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()