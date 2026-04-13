#!/usr/bin/env python3
import subprocess
import json
import sys
import os

# 你提供的Wiki节点链接，将以此节点为根递归获取子目录树
WIKI_URL = "https://waytoagi.feishu.cn/wiki/QPe5w5g7UisbEkkow8XcDmOpn8e"

# lark-cli 的完整路径（Windows 系统）
LARK_CLI = r"C:\Users\jsy96\AppData\Roaming\npm\lark-cli.cmd"

def get_node_info(node_token):
    """
    获取指定节点的详细信息，用于提取space_id
    """
    cmd = [
        LARK_CLI, "wiki", "spaces", "get_node",
        "--params", json.dumps({"token": node_token})
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
        response = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"错误: 获取节点信息失败: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"错误: 无法解析节点信息响应: {result.stdout}", file=sys.stderr)
        sys.exit(1)

    if response.get("code", 0) != 0:
        print(f"错误: 节点信息接口调用失败: {response.get('msg', '未知错误')}", file=sys.stderr)
        sys.exit(1)

    # 返回节点信息（注意：API 返回的是 data.node，不是 data）
    return response.get("data", {}).get("node", {})

def get_nodes(space_id, parent_node_token=None):
    """
    获取指定父节点下的所有子节点（自动处理分页）
    如果parent_node_token为None，则获取知识空间的顶级节点
    """
    nodes = []
    params = {
        "space_id": space_id,
        "page_size": 50
    }

    # 如果指定了父节点，添加到参数中
    if parent_node_token:
        params["parent_node_token"] = parent_node_token
    
    while True:
        # 构造lark-cli命令
        cmd = [
            LARK_CLI, "wiki", "nodes", "list",
            "--params", json.dumps(params)
        ]
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                errors='replace'
            )
            # 解析响应
            response = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"错误: 执行lark-cli命令失败: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"错误: 无法解析lark-cli的响应: {result.stdout}", file=sys.stderr)
            sys.exit(1)
        
        # 检查接口返回是否成功
        if response.get("code", 0) != 0:
            print(f"错误: 接口调用失败: {response.get('msg', '未知错误')}", file=sys.stderr)
            sys.exit(1)
        
        data = response.get("data", {})
        items = data.get("items", [])
        nodes.extend(items)
        
        # 检查是否有下一页数据
        has_more = data.get("has_more", False)
        if not has_more:
            break
        
        # 更新分页参数，获取下一页
        params["page_token"] = data.get("page_token")
    
    return nodes

def traverse_tree(space_id, parent_node_token, depth=0):
    """
    递归遍历节点树，按层级打印
    """
    nodes = get_nodes(space_id, parent_node_token)

    # 根据层级生成缩进
    indent = "    " * depth

    # 如果没有子节点，直接返回
    if not nodes:
        return

    for node in nodes:
        node_title = node.get("title", "未命名节点")
        node_token = node.get("node_token", "")
        obj_type = node.get("obj_type", "")
        has_child = node.get("has_child", False)

        # 打印当前节点及其信息
        print(f"{indent}├── {node_title} [{obj_type}]")

        # 如果当前节点有子节点，递归遍历子节点
        if has_child:
            traverse_tree(space_id, node_token, depth + 1)

if __name__ == "__main__":
    # 设置控制台输出编码为UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    print("正在解析Wiki链接，获取知识空间信息...\n")
    try:
        # 从链接中提取node_token
        root_node_token = WIKI_URL.split("/")[-1]
        # 获取根节点的信息，拿到space_id
        root_node_info = get_node_info(root_node_token)

        if not root_node_info:
            print("错误: 无法获取根节点信息", file=sys.stderr)
            sys.exit(1)

        space_id = root_node_info.get("space_id")
        if not space_id:
            print("错误: 节点信息中没有space_id", file=sys.stderr)
            sys.exit(1)

        space_name = root_node_info.get("title", "未命名空间")

        print(f"已找到知识空间: {space_name}")
        print(f"Space ID: {space_id}")
        print("正在获取所有顶级节点及其子树，请稍候...\n")
        print("=" * 80)
        print(f"知识空间: {space_name}")
        print("=" * 80)

        # 获取所有顶级节点（不指定parent_node_token表示获取根级节点）
        traverse_tree(space_id, parent_node_token=None, depth=0)

        print("\n" + "=" * 80)
        print("✅ 目录树获取完成！")
        print("=" * 80)
    except KeyboardInterrupt:
        print("\n⚠️  操作已取消。", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"错误: 无法获取必要的节点信息: {e}", file=sys.stderr)
        sys.exit(1)
