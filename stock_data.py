"""涨停板池数据抓取与连板分类。

数据源: akshare 的 stock_zt_pool_em 接口（东方财富涨停股池）。
返回字段含「连板数」，本模块据此分组。
"""
from collections import defaultdict
from datetime import datetime, timedelta

import akshare as ak


def _market_prefix(code: str) -> str:
    """根据股票代码前缀判断交易所，用于拼东财个股 URL。"""
    code = str(code)
    if code.startswith(("60", "68", "9")):
        return "sh"
    if code.startswith(("00", "30", "20")):
        return "sz"
    if code.startswith(("4", "8")):
        return "bj"
    return "sh"


def _to_float(v, default=0.0):
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (ValueError, TypeError):
        return default


def _to_int(v, default=0):
    try:
        if v is None or v == "":
            return default
        return int(v)
    except (ValueError, TypeError):
        return default


def _fetch_zt_pool(date: str):
    """调 akshare，date 为 YYYYMMDD 字符串。失败或空返回 None。"""
    try:
        df = ak.stock_zt_pool_em(date=date)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    return df


def get_consecutive_boards(date: str, min_boards: int = 2):
    """获取指定日期的连板股，按连板数分组。

    若指定日期无数据（周末/节假日/盘前），自动向前回溯最多 7 天。
    返回 (groups_dict, used_date)。
    groups_dict 形如 {"5": [...], "4": [...], "3": [...], "2": [...]}。
    """
    df = None
    used_date = date
    try:
        cur = datetime.strptime(date, "%Y%m%d")
    except ValueError:
        cur = datetime.now()
        used_date = cur.strftime("%Y%m%d")

    for _ in range(8):
        df = _fetch_zt_pool(used_date)
        if df is not None:
            break
        cur -= timedelta(days=1)
        used_date = cur.strftime("%Y%m%d")

    if df is None:
        return {}, used_date

    if "连板数" not in df.columns:
        return {}, used_date

    df = df[df["连板数"] >= min_boards]

    groups = defaultdict(list)
    for _, row in df.iterrows():
        code = str(row["代码"]).zfill(6)
        n = _to_int(row["连板数"])
        mkt = _market_prefix(code)
        stock = {
            "code": code,
            "name": str(row["名称"]),
            "boards": n,
            "change_pct": _to_float(row.get("涨跌幅")),
            "price": _to_float(row.get("最新价")),
            "turnover": _to_float(row.get("成交额")),
            "float_cap": _to_float(row.get("流通市值")),
            "turnover_rate": _to_float(row.get("换手率")),
            "seal_amount": _to_float(row.get("封板资金")),
            "first_seal": str(row.get("首次封板时间", "") or ""),
            "last_seal": str(row.get("最后封板时间", "") or ""),
            "break_times": _to_int(row.get("炸板次数")),
            "industry": str(row.get("所属行业", "") or ""),
            "eastmoney_url": f"https://quote.eastmoney.com/{mkt}{code}.html",
            "ths_url": f"https://stockpage.10jqka.com.cn/{code}/",
            "xueqiu_url": f"https://xueqiu.com/S/{mkt.upper()}{code}",
        }
        groups[n].append(stock)

    for n in groups:
        groups[n].sort(key=lambda x: -x["turnover"])

    result = {str(n): groups[n] for n in sorted(groups.keys(), reverse=True)}
    return result, used_date
