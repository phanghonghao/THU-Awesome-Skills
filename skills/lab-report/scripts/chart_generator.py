#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验报告图表生成器
从 Excel/CSV 数据生成 matplotlib 图表，支持曲线拟合
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    import matplotlib
    matplotlib.use('Agg')  # 无 GUI 后端
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from scipy import optimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# 设置中文字体
if HAS_MATPLOTLIB:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False


def read_excel_columns(excel_path: str, sheet_name: str = None) -> Dict[str, list]:
    """读取 Excel 文件的所有列

    Returns:
        {列名: [值列表]}
    """
    if not HAS_OPENPYXL:
        print("错误: 需要安装 openpyxl: pip install openpyxl")
        return {}

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {}

    # 第一行作为表头
    headers = [str(h) if h else f"col_{i}" for i, h in enumerate(rows[0])]
    columns = {h: [] for h in headers}

    for row in rows[1:]:
        for i, val in enumerate(row):
            if i < len(headers):
                columns[headers[i]].append(val)

    wb.close()
    return columns


def read_csv_columns(csv_path: str, encoding: str = 'utf-8') -> Dict[str, list]:
    """读取 CSV 文件的所有列"""
    import csv
    columns = {}
    with open(csv_path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key, val in row.items():
                if key not in columns:
                    columns[key] = []
                columns[key].append(val)
    return columns


def generate_chart(
    x_data: list,
    y_data: list,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    output_path: str = "chart.png",
    chart_type: str = 'line',
    fit: str = None,
    fit_degree: int = 1,
    show_grid: bool = True,
    dpi: int = 150,
) -> str:
    """
    生成图表

    Args:
        x_data: X 轴数据
        y_data: Y 轴数据
        title: 图表标题
        x_label: X 轴标签
        y_label: Y 轴标签
        output_path: 输出路径
        chart_type: 图表类型 (line, scatter, bar)
        fit: 拟合类型 (None, 'linear', 'poly', 'exp')
        fit_degree: 多项式拟合阶数
        show_grid: 显示网格
        dpi: 图片分辨率

    Returns:
        生成的图片路径
    """
    if not HAS_MATPLOTLIB:
        print("错误: 需要安装 matplotlib: pip install matplotlib")
        return ""

    # 转换为数值
    x = _to_numeric(x_data)
    y = _to_numeric(y_data)

    fig, ax = plt.subplots(figsize=(8, 5))

    # 绘制数据
    if chart_type == 'scatter':
        ax.scatter(x, y, c='blue', s=30, zorder=3, label='实验数据')
    elif chart_type == 'bar':
        ax.bar(x, y, color='steelblue', label='数据')
    else:  # line
        ax.plot(x, y, 'b-o', markersize=4, label='实验数据')

    # 曲线拟合
    if fit and HAS_NUMPY and len(x) > 1:
        _add_fit_curve(ax, x, y, fit, fit_degree)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    if show_grid:
        ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    plt.tight_layout()

    # 确保输出目录存在
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out), dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    print(f"已生成图表: {out}")
    return str(out)


def generate_chart_from_excel(
    excel_path: str,
    x_col: str,
    y_col: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    output_path: str = "chart.png",
    chart_type: str = 'line',
    fit: str = None,
) -> str:
    """从 Excel 指定列生成图表"""
    columns = read_excel_columns(excel_path)

    if x_col not in columns:
        print(f"错误: 未找到列 '{x_col}'，可用列: {list(columns.keys())}")
        return ""
    if y_col not in columns:
        print(f"错误: 未找到列 '{y_col}'，可用列: {list(columns.keys())}")
        return ""

    return generate_chart(
        x_data=columns[x_col],
        y_data=columns[y_col],
        title=title or f"{y_col} vs {x_col}",
        x_label=x_label or x_col,
        y_label=y_label or y_col,
        output_path=output_path,
        chart_type=chart_type,
        fit=fit,
    )


def detect_chart_templates(md_content: str) -> List[Dict]:
    """
    扫描 MD 中的 <!-- [待生成: xxx] --> 标记

    Returns:
        [{"description": "xxx", "line": 行号}, ...]
    """
    templates = []
    for i, line in enumerate(md_content.split('\n'), 1):
        m = re.match(r'<!--\s*\[待生成:\s*(.+?)\]\s*-->', line.strip())
        if m:
            templates.append({
                "description": m.group(1).strip(),
                "line": i,
            })
    return templates


# ── 内部辅助函数 ──

def _to_numeric(data: list) -> list:
    """将数据转换为数值列表"""
    result = []
    for v in data:
        if v is None:
            continue
        try:
            result.append(float(v))
        except (ValueError, TypeError):
            continue
    return result


def _add_fit_curve(ax, x, y, fit_type: str, degree: int = 1):
    """添加拟合曲线"""
    try:
        if fit_type == 'linear':
            coeffs = np.polyfit(x, y, 1)
            fit_func = np.poly1d(coeffs)
            x_fit = np.linspace(min(x), max(x), 100)
            ax.plot(x_fit, fit_func(x_fit), 'r--', label=f'线性拟合 (R²={_r_squared(y, fit_func(x)):.4f})')

        elif fit_type == 'poly':
            coeffs = np.polyfit(x, y, degree)
            fit_func = np.poly1d(coeffs)
            x_fit = np.linspace(min(x), max(x), 100)
            ax.plot(x_fit, fit_func(x_fit), 'r--', label=f'{degree}次多项式拟合')

        elif fit_type == 'exp':
            # y = a * exp(b * x)
            def exp_func(x, a, b):
                return a * np.exp(b * x)
            popt, _ = optimize.curve_fit(exp_func, x, y, p0=[1, 0.1])
            x_fit = np.linspace(min(x), max(x), 100)
            ax.plot(x_fit, exp_func(x_fit, *popt), 'r--', label='指数拟合')

    except Exception as e:
        print(f"拟合失败: {e}")


def _r_squared(y_actual, y_predicted) -> float:
    """计算 R²"""
    ss_res = np.sum((np.array(y_actual) - np.array(y_predicted)) ** 2)
    ss_tot = np.sum((np.array(y_actual) - np.mean(y_actual)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='实验报告图表生成器')
    parser.add_argument('excel', help='Excel/CSV 文件路径')
    parser.add_argument('--x-col', required=True, help='X 轴列名')
    parser.add_argument('--y-col', required=True, help='Y 轴列名')
    parser.add_argument('--title', default='', help='图表标题')
    parser.add_argument('--x-label', default='', help='X 轴标签')
    parser.add_argument('--y-label', default='', help='Y 轴标签')
    parser.add_argument('-o', '--output', default='chart.png', help='输出路径')
    parser.add_argument('--type', default='line', choices=['line', 'scatter', 'bar'], help='图表类型')
    parser.add_argument('--fit', default=None, choices=['linear', 'poly', 'exp'], help='拟合类型')
    parser.add_argument('--degree', type=int, default=2, help='多项式拟合阶数')

    args = parser.parse_args()
    generate_chart_from_excel(
        excel_path=args.excel,
        x_col=args.x_col,
        y_col=args.y_col,
        title=args.title,
        x_label=args.x_label,
        y_label=args.y_label,
        output_path=args.output,
        chart_type=args.type,
        fit=args.fit,
    )


if __name__ == '__main__':
    main()
