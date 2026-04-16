#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用Python可视化GraphRAG知识图谱
需要安装: pip install pandas pyarrow networkx matplotlib
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import sys

def visualize_graphrag(input_dir, output_file='knowledge_graph.png', max_nodes=500):
    """
    可视化GraphRAG生成的知识图谱
    
    参数:
        input_dir: GraphRAG输出目录或neo4j_import目录
        output_file: 输出图片文件名
        max_nodes: 最大节点数（如果图太大，限制节点数量）
    """
    input_path = Path(input_dir)
    
    # 尝试读取CSV文件（如果已经转换）
    nodes_csv = input_path / "nodes.csv"
    rels_csv = input_path / "relationships.csv"
    
    # 如果CSV不存在，尝试读取Parquet文件
    if not nodes_csv.exists():
        nodes_parquet = input_path / "entities.parquet"
        rels_parquet = input_path / "relationships.parquet"
        
        if nodes_parquet.exists() and rels_parquet.exists():
            print("读取Parquet文件...")
            nodes_df = pd.read_parquet(nodes_parquet)
            rels_df = pd.read_parquet(rels_parquet)
            
            # 简单转换
            if 'id' in nodes_df.columns:
                nodes_df['id'] = nodes_df['id'].astype(str)
            if 'source' in rels_df.columns and 'target' in rels_df.columns:
                rels_df['source'] = rels_df['source'].astype(str)
                rels_df['target'] = rels_df['target'].astype(str)
        else:
            print(f"错误: 找不到数据文件")
            print(f"请确保目录中包含 nodes.csv/relationships.csv 或 entities.parquet/relationships.parquet")
            return False
    else:
        print("读取CSV文件...")
        nodes_df = pd.read_csv(nodes_csv)
        rels_df = pd.read_csv(rels_csv)
    
    print(f"节点数量: {len(nodes_df)}")
    print(f"关系数量: {len(rels_df)}")
    
    # 创建图
    G = nx.DiGraph()
    
    # 添加节点
    print("添加节点...")
    id_col = None
    for col in ['id', ':ID', 'entity_id', 'node_id']:
        if col in nodes_df.columns:
            id_col = col
            break
    
    if not id_col:
        print("错误: 找不到节点ID列")
        return False
    
    # 限制节点数量（如果图太大）
    if len(nodes_df) > max_nodes:
        print(f"节点数量超过{max_nodes}，随机采样...")
        nodes_df = nodes_df.sample(n=max_nodes, random_state=42)
        # 只保留相关的边
        node_ids = set(nodes_df[id_col].astype(str))
        rels_df = rels_df[
            rels_df['source'].astype(str).isin(node_ids) & 
            rels_df['target'].astype(str).isin(node_ids)
        ]
    
    for _, row in nodes_df.iterrows():
        node_id = str(row[id_col])
        attrs = {k: v for k, v in row.items() if k != id_col and pd.notna(v)}
        G.add_node(node_id, **attrs)
    
    # 添加边
    print("添加关系...")
    source_col = None
    target_col = None
    
    for col in ['source', ':START_ID', 'from', 'from_id']:
        if col in rels_df.columns:
            source_col = col
            break
    
    for col in ['target', ':END_ID', 'to', 'to_id']:
        if col in rels_df.columns:
            target_col = col
            break
    
    if not source_col or not target_col:
        print("错误: 找不到关系起始/结束节点列")
        return False
    
    for _, row in rels_df.iterrows():
        source = str(row[source_col])
        target = str(row[target_col])
        
        # 只添加存在的节点之间的边
        if source in G and target in G:
            rel_type = row.get('type', row.get(':TYPE', 'RELATED_TO'))
            attrs = {k: v for k, v in row.items() 
                    if k not in [source_col, target_col, ':START_ID', ':END_ID'] 
                    and pd.notna(v)}
            G.add_edge(source, target, type=rel_type, **attrs)
    
    print(f"图创建完成: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")
    
    # 可视化
    print("生成可视化...")
    plt.figure(figsize=(20, 20))
    
    # 使用spring布局
    pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
    
    # 绘制节点
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=300, alpha=0.7)
    
    # 绘制边
    nx.draw_networkx_edges(G, pos, edge_color='gray', 
                          alpha=0.5, arrows=True, arrowsize=10)
    
    # 绘制标签（只显示部分节点标签，避免太拥挤）
    if G.number_of_nodes() <= 100:
        labels = {node: str(node)[:20] for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=6)
    
    plt.title(f"GraphRAG Knowledge Graph\n({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)", 
              fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    
    # 保存图片
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"可视化图片已保存: {output_file}")
    
    # 显示统计信息
    print("\n图谱统计:")
    print(f"  节点数: {G.number_of_nodes()}")
    print(f"  边数: {G.number_of_edges()}")
    print(f"  平均度: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
    
    # 计算度中心性
    degrees = dict(G.degree())
    top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\n度中心性最高的10个节点:")
    for node, degree in top_nodes:
        print(f"  {node}: {degree}")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python visualize_with_python.py <数据目录> [输出文件] [最大节点数]")
        print("\n示例:")
        print("  python visualize_with_python.py E:\\graphrag\\graphrag-2.7.0\\test_0114-2\\output")
        print("  python visualize_with_python.py E:\\graphrag\\graphrag-2.7.0\\test_0114-2\\output\\neo4j_import kg.png 1000")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'knowledge_graph.png'
    max_nodes = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    
    visualize_graphrag(input_dir, output_file, max_nodes)

if __name__ == "__main__":
    main()




