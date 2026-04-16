#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接将CSV文件导入到Neo4j Sandbox（线上版本）
适用于Google账号登录的Neo4j Sandbox
"""

import pandas as pd
import sys
from pathlib import Path

# 尝试导入neo4j驱动
try:
    from neo4j import GraphDatabase
except ImportError:
    print("[ERROR] 请先安装neo4j驱动: pip install neo4j")
    sys.exit(1)


def print_info(message):
    """打印信息"""
    print(f"[INFO] {message}")


def print_error(message):
    """打印错误"""
    print(f"[ERROR] {message}", file=sys.stderr)


def import_nodes(driver, nodes_df, batch_size=500, database="neo4j", dataset_name=None):
    """
    导入节点到Neo4j
    
    参数:
        driver: Neo4j驱动
        nodes_df: 节点DataFrame
        batch_size: 每批导入的数量
        database: 数据库名称
        dataset_name: 可选，数据集名称，写入节点属性 dataset，便于按批可视化
    """
    print_info(f"开始导入 {len(nodes_df)} 个节点...")
    if dataset_name:
        print_info(f"数据集名称: {dataset_name}（将写入节点属性 dataset）")
    
    # 创建索引（先创建可以提高导入速度）
    with driver.session(database=database) as session:
        session.run("CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id)")
        if dataset_name:
            session.run("CREATE INDEX entity_dataset_index IF NOT EXISTS FOR (n:Entity) ON (n.dataset)")
        print_info("节点索引已创建")
    
    total_nodes = 0
    
    with driver.session(database=database) as session:
        for i in range(0, len(nodes_df), batch_size):
            batch = nodes_df.iloc[i:i + batch_size]

            # 准备批量数据
            batch_data = []
            for _, row in batch.iterrows():
                node_props = {}
                node_id = None
                node_labels = ['Entity']

                # 处理每一列
                for col in row.index:
                    value = row[col]

                    # 跳过空值
                    if pd.isna(value):
                        continue

                    # 处理特殊列（兼容 :LABEL 与 :LAB）
                    if col == ':ID':
                        node_id = str(value)
                    elif col in (':LABEL', ':LAB'):
                        # 处理标签（可能用分号分隔）
                        labels_str = str(value)
                        if ';' in labels_str:
                            node_labels.extend([l.strip() for l in labels_str.split(';') if l.strip()])
                        elif labels_str.strip():
                            node_labels.append(labels_str.strip())
                    else:
                        # 普通属性
                        node_props[col] = value

                if node_id:
                    node_props['id'] = node_id
                    if dataset_name:
                        node_props['dataset'] = dataset_name
                    batch_data.append({
                        'props': node_props,
                        'labels': node_labels
                    })

            if not batch_data:
                continue

            # 批量创建节点
            # 注意：Neo4j不支持在Cypher中动态设置标签名，所以我们需要先设置Entity标签
            # 然后在循环中逐个处理其他标签，或者使用APOC插件
            # 这里采用简化方式：使用第一个标签作为主标签，其他标签作为属性
            query = """
            UNWIND $batch AS item
            CREATE (n)
            SET n:Entity
            SET n += item.props
            """

            try:
                result = session.run(query, batch=batch_data)
                # 执行查询（为了确保创建完成）
                result.consume()
                total_nodes += len(batch_data)
                print_info(f"已导入 {total_nodes}/{len(nodes_df)} 个节点")
            except Exception as e:
                print_error(f"导入节点时出错: {e}")
                # 尝试单条导入
                print_info("尝试单条导入...")
                for item in batch_data:
                    try:
                        session.run(query, batch=[item]).consume()
                        total_nodes += 1
                    except Exception as err:
                        print_error(f"跳过节点 {item.get('props', {}).get('id', 'unknown')}: {err}")

    print_info(f"节点导入完成！总共导入 {total_nodes} 个节点")
    return total_nodes


def import_relationships(driver, rels_df, batch_size=500, database="neo4j", dataset_name=None):
    """
    导入关系到Neo4j
    
    参数:
        driver: Neo4j驱动
        rels_df: 关系DataFrame
        batch_size: 每批导入的数量
        database: 数据库名称
        dataset_name: 可选，数据集名称，写入关系属性 dataset
    """
    print_info(f"开始导入 {len(rels_df)} 个关系...")
    
    total_rels = 0
    
    with driver.session(database=database) as session:
        for i in range(0, len(rels_df), batch_size):
            batch = rels_df.iloc[i:i + batch_size]

            # 准备批量数据
            batch_data = []
            for _, row in batch.iterrows():
                rel_props = {}
                start_id = None
                end_id = None
                rel_type = 'RELATED_TO'

                # 处理每一列
                for col in row.index:
                    value = row[col]

                    # 跳过空值
                    if pd.isna(value):
                        continue

                    # 处理特殊列
                    if col == ':START_ID':
                        start_id = str(value)
                    elif col == ':END_ID':
                        end_id = str(value)
                    elif col == ':TYPE':
                        rel_type = str(value).strip() or 'RELATED_TO'
                    else:
                        # 普通属性
                        rel_props[col] = value

                if start_id and end_id:
                    if dataset_name:
                        rel_props['dataset'] = dataset_name
                    batch_data.append({
                        'start_id': start_id,
                        'end_id': end_id,
                        'rel_type': rel_type,
                        'props': rel_props
                    })

            if not batch_data:
                continue

            # 批量创建关系
            # 注意：关系类型需要使用参数化方式，所以需要为每种类型分别处理
            # 这里使用简单方法：统一使用RELATED_TO类型，或者动态创建

            # 按关系类型分组
            type_groups = {}
            for item in batch_data:
                rel_type = item['rel_type']
                if rel_type not in type_groups:
                    type_groups[rel_type] = []
                type_groups[rel_type].append(item)

            # 为每种关系类型分别导入
            for rel_type, items in type_groups.items():
                query = f"""
                UNWIND $batch AS item
                MATCH (source:Entity {{id: item.start_id}})
                MATCH (target:Entity {{id: item.end_id}})
                CREATE (source)-[r:{rel_type}]->(target)
                SET r += item.props
                """

                try:
                    result = session.run(query, batch=items)
                    result.consume()
                    total_rels += len(items)
                    if len(type_groups) > 1:
                        print_info(f"已导入 {total_rels}/{len(rels_df)} 个关系 (类型: {rel_type})")
                    else:
                        print_info(f"已导入 {total_rels}/{len(rels_df)} 个关系")
                except Exception as e:
                    print_error(f"导入关系类型 {rel_type} 时出错: {e}")
                    # 尝试单条导入
                    for item in items:
                        try:
                            session.run(query, batch=[item]).consume()
                            total_rels += 1
                        except Exception as err:
                            print_error(f"跳过关系 {item['start_id']} -> {item['end_id']}: {err}")

    print_info(f"关系导入完成！总共导入 {total_rels} 个关系")
    return total_rels


def import_csv_to_sandbox(nodes_file, relationships_file, uri, username, password, database="neo4j", dataset_name=None):
    """
    将CSV文件导入到Neo4j Sandbox
    
    参数:
        nodes_file: 节点CSV文件路径
        relationships_file: 关系CSV文件路径
        uri: Neo4j连接URI
        username: 用户名
        password: 密码
        database: 数据库名称（默认: neo4j）
        dataset_name: 可选，数据集名称；传入后节点和关系会带 dataset 属性，便于在 Neo4j 中按批可视化
    """
    # 检查文件是否存在
    nodes_path = Path(nodes_file)
    rels_path = Path(relationships_file)

    if not nodes_path.exists():
        print_error(f"节点文件不存在: {nodes_file}")
        return False

    if not rels_path.exists():
        print_error(f"关系文件不存在: {relationships_file}")
        return False

    # 读取CSV文件
    print_info(f"正在读取节点文件: {nodes_file}")
    try:
        nodes_df = pd.read_csv(nodes_file)
        print_info(f"成功读取 {len(nodes_df)} 个节点")
        print_info(f"节点列: {list(nodes_df.columns)}")
    except Exception as e:
        print_error(f"读取节点文件失败: {e}")
        return False

    print_info(f"正在读取关系文件: {relationships_file}")
    try:
        rels_df = pd.read_csv(relationships_file)
        print_info(f"成功读取 {len(rels_df)} 个关系")
        print_info(f"关系列: {list(rels_df.columns)}")
    except Exception as e:
        print_error(f"读取关系文件失败: {e}")
        return False

    # 连接Neo4j
    print_info(f"正在连接到Neo4j: {uri}")
    print_info(f"数据库: {database}")
    try:
        # 使用官方推荐的方式连接
        driver = GraphDatabase.driver(
            uri, 
            auth=(username, password),
            connection_timeout=30
        )
        # 测试连接
        with driver.session(database=database) as session:
            result = session.run("RETURN 1 as test")
            result.single()
        print_info("连接成功！")
    except Exception as e:
        print_error(f"连接Neo4j失败: {e}")
        print_error("\n可能的解决方案:")
        print_error("  1. 确保URI使用正确的协议和端口:")
        print_error("     - 推荐: neo4j://3.83.79.57:7687")
        print_error("     - 或: neo4j+s://xxx.neo4jsandbox.com:7687")
        print_error("  2. 检查防火墙或代理设置")
        print_error("  3. 确认Sandbox实例仍在运行")
        print_error("  4. 尝试使用另一个URI（在脚本配置中修改）")
        
        return False

    try:
        # 导入节点
        print_info("\n" + "=" * 60)
        print_info("开始导入节点...")
        print_info("=" * 60)
        nodes_count = import_nodes(driver, nodes_df, database=database, dataset_name=dataset_name)
        
        # 导入关系
        print_info("\n" + "=" * 60)
        print_info("开始导入关系...")
        print_info("=" * 60)
        rels_count = import_relationships(driver, rels_df, database=database, dataset_name=dataset_name)

        # 完成
        print_info("\n" + "=" * 60)
        print_info("导入完成！")
        print_info("=" * 60)
        print_info(f"✓ 成功导入 {nodes_count} 个节点")
        print_info(f"✓ 成功导入 {rels_count} 个关系")
        if dataset_name:
            print_info(f"\n只画这批数据时，在 Neo4j Browser 中执行：")
            print_info(f"  MATCH (n:Entity)-[r]-(m:Entity)")
            print_info(f"  WHERE n.dataset = '{dataset_name}' AND m.dataset = '{dataset_name}'")
            print_info(f"  RETURN n, r, m LIMIT 200;")
        print_info("\n现在可以在Neo4j Browser中查看你的数据了！")
        return True

    except Exception as e:
        print_error(f"导入过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.close()
        print_info("已关闭数据库连接")


def main():
    """主函数"""
    print("=" * 60)
    print("Neo4j Sandbox CSV导入工具")
    print("=" * 60)
    print()

    # ========== 配置区域：在这里填入你的连接信息 ==========
    # 如果这些值不为空，将直接使用，不再提示输入
    # 注意：Sandbox 单实例用 neo4j:// 或 bolt:// 直连
    # 使用 Sandbox 页面的 "Bolt URL" 或 "neo4j://IP:7687"
    CONFIG_URI = "neo4j://3.92.50.201:7687"
    # 若直连失败，可改用 Websocket Bolt URL（Sandbox 页面的 "Websocket Bolt URL"）:
    # CONFIG_URI = "bolt+s://7f77e62c1281c2e0864c0114f00af7e9.neo4jsandbox.com:7687"
    CONFIG_USERNAME = "neo4j"
    CONFIG_PASSWORD = "books-minority-trouble"
    CONFIG_DATABASE = "neo4j"  # Neo4j Sandbox默认数据库名
    # ======================================================

    # 获取CSV文件路径和可选的数据集名称（第三个参数）
    if len(sys.argv) >= 3:
        nodes_file = sys.argv[1]
        relationships_file = sys.argv[2]
        dataset_name = sys.argv[3].strip() if len(sys.argv) >= 4 and sys.argv[3].strip() else None
    else:
        dataset_name = None
        # 默认使用neo4j_import目录
        default_nodes = "neo4j_import/nodes.csv"
        default_rels = "neo4j_import/relationships.csv"

        nodes_file = input(f"节点CSV文件路径 (默认: {default_nodes}): ").strip() or default_nodes
        relationships_file = input(f"关系CSV文件路径 (默认: {default_rels}): ").strip() or default_rels
        dataset_name = input("数据集名称（可选，用于按批可视化，直接回车跳过）: ").strip() or None

    # 获取Neo4j连接信息
    if CONFIG_URI and CONFIG_USERNAME and CONFIG_PASSWORD:
        # 使用配置中的连接信息
        uri = CONFIG_URI
        username = CONFIG_USERNAME
        password = CONFIG_PASSWORD
        database = CONFIG_DATABASE
        print("\n使用配置文件中的连接信息:")
        print(f"  URI: {uri}")
        print(f"  用户名: {username}")
        print(f"  密码: {'*' * len(password)}")
        print(f"  数据库: {database}")
    else:
        # 提示用户输入
        print("\n请输入Neo4j Sandbox连接信息:")
        print("（可以在Sandbox项目页面找到这些信息）")
        print()
        
        uri = input("Connection URI (例如: bolt+s://xxx.neo4jsandbox.com:7687): ").strip()
        # 清除可能的意外输入（去除命令行内容）
        if uri.startswith("python ") or "import_to_neo4j_sandbox.py" in uri:
            print_error("检测到错误的URI输入，请重新输入正确的URI")
            uri = input("Connection URI: ").strip()
        
        if not uri:
            print_error("URI不能为空")
            sys.exit(1)
        
        # 验证URI格式
        valid_schemes = ['bolt', 'bolt+ssc', 'bolt+s', 'neo4j', 'neo4j+ssc', 'neo4j+s']
        if not any(uri.startswith(f"{scheme}://") for scheme in valid_schemes):
            print_error(f"URI格式错误，必须以以下之一开头: {', '.join([f'{s}://' for s in valid_schemes])}")
            print_error(f"你输入的URI: {uri}")
            sys.exit(1)

        username = input("用户名 (默认: neo4j): ").strip() or "neo4j"
        password = input("密码 (在Sandbox页面显示，不是Google账号密码): ").strip()
        if not password:
            print_error("密码不能为空")
            sys.exit(1)
        database = input("数据库名称 (默认: neo4j): ").strip() or "neo4j"

    print()
    print("=" * 60)

    # 执行导入
    success = import_csv_to_sandbox(nodes_file, relationships_file, uri, username, password, database, dataset_name=dataset_name)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()