#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GraphRAG数据转Neo4j导入脚本
将GraphRAG生成的Parquet文件转换为Neo4j可导入的CSV格式
"""

import json
from pathlib import Path
import sys
import os
import warnings

# 尝试导入pandas，如果失败则提示
try:
    import pandas as pd
except ImportError:
    print("[ERROR] 请安装pandas: pip install pandas")
    sys.exit(1)

# 抑制NumPy兼容性警告（如果pyarrow有问题，我们会使用替代方案）
warnings.filterwarnings('ignore', category=UserWarning, message='.*NumPy.*')

def print_info(message):
    """打印信息"""
    print(f"[INFO] {message}")

def print_error(message):
    """打印错误"""
    print(f"[ERROR] {message}", file=sys.stderr)

def convert_entities_to_nodes(entities_df, output_file):
    """
    将实体DataFrame转换为Neo4j节点CSV格式
    
    Neo4j节点CSV格式要求：
    - 必须包含 :ID 列（节点唯一标识）
    - 可选包含 :LABEL 列（节点标签，多个标签用分号分隔）
    - 其他列作为节点属性
    """
    print_info("正在处理实体数据...")
    print_info(f"实体数量: {len(entities_df)}")
    print_info(f"实体列: {entities_df.columns.tolist()}")
    
    # 创建副本避免修改原数据
    nodes_df = entities_df.copy()
    
    # 查找ID列（可能的列名）
    id_candidates = ['id', 'entity_id', 'node_id', 'entityId', 'nodeId', 'ID']
    id_col = None
    for col in id_candidates:
        if col in nodes_df.columns:
            id_col = col
            break
    
    # 如果没找到ID列，使用第一列或创建索引
    if id_col is None:
        if len(nodes_df) > 0:
            # 使用第一列作为ID，或创建基于索引的ID
            first_col = nodes_df.columns[0]
            print_info(f"未找到标准ID列，使用 '{first_col}' 作为ID")
            nodes_df.insert(0, ':ID', nodes_df[first_col].astype(str))
        else:
            print_error("数据为空，无法处理")
            return False
    else:
        print_info(f"使用 '{id_col}' 作为节点ID")
        # 将ID列移到最前面并重命名为:ID
        nodes_df.insert(0, ':ID', nodes_df[id_col].astype(str))
    
    # 查找标签列（可能的列名）
    label_candidates = ['type', 'category', 'label', 'labels', 'entity_type', 'node_type']
    label_col = None
    for col in label_candidates:
        if col in nodes_df.columns:
            label_col = col
            break
    
    # 处理标签
    if label_col:
        print_info(f"使用 '{label_col}' 作为节点标签")
        # 如果标签是列表，转换为分号分隔的字符串
        if nodes_df[label_col].dtype == 'object':
            # 检查是否是列表类型
            sample = nodes_df[label_col].iloc[0] if len(nodes_df) > 0 else None
            if isinstance(sample, (list, tuple)):
                nodes_df[':LABEL'] = nodes_df[label_col].apply(
                    lambda x: ';'.join(str(v) for v in x) if isinstance(x, (list, tuple)) else str(x)
                )
            else:
                nodes_df[':LABEL'] = nodes_df[label_col].astype(str)
        else:
            nodes_df[':LABEL'] = nodes_df[label_col].astype(str)
    else:
        print_info("未找到标签列，使用默认标签 'Entity'")
        nodes_df[':LABEL'] = 'Entity'
    
    # 移除原始的ID和标签列（如果它们不是:ID和:LABEL）
    columns_to_remove = []
    if id_col and id_col != ':ID':
        columns_to_remove.append(id_col)
    if label_col and label_col != ':LABEL':
        columns_to_remove.append(label_col)
    
    for col in columns_to_remove:
        if col in nodes_df.columns:
            nodes_df = nodes_df.drop(columns=[col])
    
    # 处理其他列：确保所有值都是可序列化的
    for col in nodes_df.columns:
        if col not in [':ID', ':LABEL']:
            # 如果是复杂类型（列表、字典），转换为JSON字符串
            if nodes_df[col].dtype == 'object':
                sample = nodes_df[col].iloc[0] if len(nodes_df) > 0 else None
                if isinstance(sample, (list, dict)):
                    nodes_df[col] = nodes_df[col].apply(
                        lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x
                    )
    
    # 保存为CSV
    try:
        nodes_df.to_csv(output_file, index=False, encoding='utf-8')
        print_info(f"节点CSV已保存: {output_file}")
        print_info(f"节点CSV大小: {os.path.getsize(output_file) / 1024:.2f} KB")
        return True
    except Exception as e:
        print_error(f"保存节点CSV失败: {e}")
        return False

def convert_relationships_to_rels(relationships_df, output_file, nodes_id_map=None):
    """
    将关系DataFrame转换为Neo4j关系CSV格式
    
    Neo4j关系CSV格式要求：
    - 必须包含 :START_ID 列（起始节点ID）
    - 必须包含 :END_ID 列（结束节点ID）
    - 必须包含 :TYPE 列（关系类型）
    - 其他列作为关系属性
    
    参数:
        relationships_df: 关系DataFrame
        output_file: 输出文件路径
        nodes_id_map: 节点映射字典，用于将title等属性映射到节点ID
    """
    print_info("正在处理关系数据...")
    print_info(f"关系数量: {len(relationships_df)}")
    print_info(f"关系列: {relationships_df.columns.tolist()}")
    
    if len(relationships_df) == 0:
        print_error("关系数据为空")
        return False
    
    # 创建副本
    rels_df = relationships_df.copy()
    
    # 查找起始节点ID列
    start_id_candidates = ['source', 'source_id', 'from', 'from_id', 'start', 'start_id', 
                          'sourceId', 'fromId', 'startId', 'SOURCE', 'FROM']
    start_id_col = None
    for col in start_id_candidates:
        if col in rels_df.columns:
            start_id_col = col
            break
    
    # 查找结束节点ID列
    end_id_candidates = ['target', 'target_id', 'to', 'to_id', 'end', 'end_id',
                        'targetId', 'toId', 'endId', 'TARGET', 'TO']
    end_id_col = None
    for col in end_id_candidates:
        if col in rels_df.columns:
            end_id_col = col
            break
    
    # 检查是否找到必需的列
    if not start_id_col:
        print_error("未找到起始节点ID列（可能的列名: source, source_id, from, from_id等）")
        print_info(f"可用列: {rels_df.columns.tolist()}")
        return False
    
    if not end_id_col:
        print_error("未找到结束节点ID列（可能的列名: target, target_id, to, to_id等）")
        print_info(f"可用列: {rels_df.columns.tolist()}")
        return False
    
    print_info(f"使用 '{start_id_col}' 作为起始节点标识")
    print_info(f"使用 '{end_id_col}' 作为结束节点标识")
    
    # 检查source/target的值是否是UUID格式（节点ID）还是文本（title）
    sample_start = str(rels_df[start_id_col].iloc[0]) if len(rels_df) > 0 else ""
    sample_end = str(rels_df[end_id_col].iloc[0]) if len(rels_df) > 0 else ""
    
    # UUID格式检查（通常包含连字符，长度36）
    is_uuid_format = len(sample_start) == 36 and '-' in sample_start
    
    if is_uuid_format:
        print_info("检测到source/target是UUID格式（节点ID），直接使用")
        rels_df[':START_ID'] = rels_df[start_id_col].astype(str)
        rels_df[':END_ID'] = rels_df[end_id_col].astype(str)
    else:
        print_info("检测到source/target是文本格式（可能是title），需要映射到节点ID")
        if nodes_id_map is None:
            print_error("需要节点ID映射，但未提供nodes_id_map参数")
            print_error("请确保在调用此函数时传入节点ID映射")
            return False
        
        # 使用映射将title转换为ID
        def map_to_id(value, mapping):
            value_str = str(value)
            if value_str in mapping:
                return mapping[value_str]
            else:
                print_error(f"警告: 未找到节点ID映射: {value_str}")
                return None
        
        rels_df[':START_ID'] = rels_df[start_id_col].apply(lambda x: map_to_id(x, nodes_id_map))
        rels_df[':END_ID'] = rels_df[end_id_col].apply(lambda x: map_to_id(x, nodes_id_map))
        
        # 检查是否有无法映射的值
        missing_start = rels_df[':START_ID'].isna().sum()
        missing_end = rels_df[':END_ID'].isna().sum()
        if missing_start > 0 or missing_end > 0:
            print_error(f"警告: {missing_start} 个起始节点和 {missing_end} 个结束节点无法映射到ID")
            # 移除无法映射的行
            rels_df = rels_df.dropna(subset=[':START_ID', ':END_ID'])
            print_info(f"已移除无法映射的关系，剩余 {len(rels_df)} 个关系")
    
    # 查找关系类型列
    type_candidates = ['type', 'relationship_type', 'rel_type', 'edge_type', 
                      'relationshipType', 'relType', 'edgeType', 'TYPE']
    type_col = None
    for col in type_candidates:
        if col in rels_df.columns:
            type_col = col
            break
    
    if type_col:
        print_info(f"使用 '{type_col}' 作为关系类型")
        rels_df[':TYPE'] = rels_df[type_col].astype(str)
    else:
        print_info("未找到关系类型列，使用默认类型 'RELATED_TO'")
        rels_df[':TYPE'] = 'RELATED_TO'
    
    # 移除原始的ID和类型列
    columns_to_remove = []
    if start_id_col and start_id_col != ':START_ID':
        columns_to_remove.append(start_id_col)
    if end_id_col and end_id_col != ':END_ID':
        columns_to_remove.append(end_id_col)
    if type_col and type_col != ':TYPE':
        columns_to_remove.append(type_col)
    
    for col in columns_to_remove:
        if col in rels_df.columns:
            rels_df = rels_df.drop(columns=[col])
    
    # 处理其他列：确保所有值都是可序列化的
    for col in rels_df.columns:
        if col not in [':START_ID', ':END_ID', ':TYPE']:
            if rels_df[col].dtype == 'object':
                sample = rels_df[col].iloc[0] if len(rels_df) > 0 else None
                if isinstance(sample, (list, dict)):
                    rels_df[col] = rels_df[col].apply(
                        lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x
                    )
    
    # 保存为CSV
    try:
        rels_df.to_csv(output_file, index=False, encoding='utf-8')
        print_info(f"关系CSV已保存: {output_file}")
        print_info(f"关系CSV大小: {os.path.getsize(output_file) / 1024:.2f} KB")
        return True
    except Exception as e:
        print_error(f"保存关系CSV失败: {e}")
        return False

def convert_graphrag_to_neo4j(input_dir, output_dir=None):
    """
    将GraphRAG输出转换为Neo4j可导入的CSV格式
    
    参数:
        input_dir: GraphRAG输出目录路径（包含entities.parquet和relationships.parquet）
        output_dir: 输出目录路径（如果不指定，则在input_dir下创建neo4j_import目录）
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print_error(f"输入目录不存在: {input_dir}")
        return False
    
    # 确定输出目录
    if output_dir is None:
        output_path = input_path / "neo4j_import"
    else:
        output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    print_info(f"输出目录: {output_path}")
    
    # 检查输入文件
    entities_file = input_path / "entities.parquet"
    relationships_file = input_path / "relationships.parquet"
    
    if not entities_file.exists():
        print_error(f"实体文件不存在: {entities_file}")
        return False
    
    if not relationships_file.exists():
        print_error(f"关系文件不存在: {relationships_file}")
        return False
    
    success = True
    entities_df = None  # 在外部定义，以便在转换关系时使用
    
    # 读取并转换实体
    try:
        print_info(f"读取实体文件: {entities_file}")
        # 尝试使用不同的引擎读取Parquet文件
        engines = ['auto', 'pyarrow', 'fastparquet']
        
        for engine in engines:
            try:
                print_info(f"尝试使用 {engine} 引擎读取...")
                entities_df = pd.read_parquet(entities_file, engine=engine)
                print_info(f"成功使用 {engine} 引擎读取实体文件")
                break
            except Exception as e:
                if engine == engines[-1]:  # 最后一个引擎也失败了
                    raise e
                print_info(f"{engine} 引擎失败，尝试下一个...")
                continue
        
        nodes_output = output_path / "nodes.csv"
        if not convert_entities_to_nodes(entities_df, nodes_output):
            success = False
    except Exception as e:
        print_error(f"读取实体文件失败: {e}")
        print_error("提示: 如果遇到NumPy版本兼容性问题，请尝试:")
        print_error("  1. 降级NumPy: pip install 'numpy<2'")
        print_error("  2. 或升级pyarrow: pip install --upgrade pyarrow")
        print_error("  3. 或安装fastparquet: pip install fastparquet")
        success = False
        entities_df = None  # 确保即使失败也设置为None
    
    # 读取并转换关系
    try:
        print_info(f"读取关系文件: {relationships_file}")
        # 尝试使用不同的引擎读取Parquet文件
        relationships_df = None
        engines = ['auto', 'pyarrow', 'fastparquet']
        
        for engine in engines:
            try:
                print_info(f"尝试使用 {engine} 引擎读取...")
                relationships_df = pd.read_parquet(relationships_file, engine=engine)
                print_info(f"成功使用 {engine} 引擎读取关系文件")
                break
            except Exception as e:
                if engine == engines[-1]:  # 最后一个引擎也失败了
                    raise e
                print_info(f"{engine} 引擎失败，尝试下一个...")
                continue
        
        # 创建节点ID映射（从title到ID）
        nodes_id_map = None
        if entities_df is not None:
            print_info("创建节点ID映射...")
            nodes_id_map = {}
            if 'title' in entities_df.columns and 'id' in entities_df.columns:
                for _, row in entities_df.iterrows():
                    title = str(row['title'])
                    node_id = str(row['id'])
                    nodes_id_map[title] = node_id
                print_info(f"已创建 {len(nodes_id_map)} 个节点的ID映射")
            else:
                print_info("无法创建节点ID映射（缺少title或id列）")
        else:
            print_info("警告: 实体数据未加载，无法创建节点ID映射")
        
        rels_output = output_path / "relationships.csv"
        if not convert_relationships_to_rels(relationships_df, rels_output, nodes_id_map):
            success = False
    except Exception as e:
        print_error(f"读取关系文件失败: {e}")
        print_error("提示: 如果遇到NumPy版本兼容性问题，请尝试:")
        print_error("  1. 降级NumPy: pip install 'numpy<2'")
        print_error("  2. 或升级pyarrow: pip install --upgrade pyarrow")
        print_error("  3. 或安装fastparquet: pip install fastparquet")
        success = False
    
    if success:
        print_info("\n" + "="*50)
        print_info("转换完成！")
        print_info("="*50)
        print_info(f"\n生成的CSV文件位置:")
        print_info(f"  节点文件: {output_path / 'nodes.csv'}")
        print_info(f"  关系文件: {output_path / 'relationships.csv'}")
        print_info(f"\n下一步操作:")
        print_info("1. 将CSV文件复制到Neo4j的import目录")
        print_info("2. 使用Neo4j Browser或Cypher命令导入数据")
        print_info("3. 查看README.md了解详细的导入步骤")
    else:
        print_error("\n转换过程中出现错误，请检查上述错误信息")
    
    return success

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python convert_graphrag_to_neo4j.py <输入目录> [输出目录]")
        print("\n示例:")
        print("  python convert_graphrag_to_neo4j.py E:\\graphrag\\graphrag-2.7.0\\test_0114-2\\output")
        print("  python convert_graphrag_to_neo4j.py E:\\graphrag\\graphrag-2.7.0\\test_0114-2\\output E:\\neo4j_import")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_graphrag_to_neo4j(input_dir, output_dir)

if __name__ == "__main__":
    main()

