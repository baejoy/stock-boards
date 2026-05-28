"""GitHub Actions 调用：拉今日涨停板池，写入 docs/data/boards.json。

设计：
- 用北京时间判断「今天」是哪一天
- 失败时不覆盖现有数据（保留上一次成功的快照）
- 输出包含 updated_at（UTC），前端展示
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 让脚本能 import 项目根目录下的 stock_data
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stock_data import get_consecutive_boards  # noqa: E402


BJ_TZ = timezone(timedelta(hours=8))


def main():
    now_bj = datetime.now(BJ_TZ)
    date = now_bj.strftime("%Y%m%d")
    print(f"[fetch] bj_now={now_bj.isoformat()} target_date={date}")

    try:
        groups, used_date = get_consecutive_boards(date, min_boards=2)
    except Exception as e:
        print(f"[error] fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    total = sum(len(v) for v in groups.values())
    payload = {
        "ok": True,
        "requested_date": date,
        "data_date": used_date,
        "total": total,
        "groups": groups,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    out = ROOT / "docs" / "data" / "boards.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] total={total} data_date={used_date} -> {out}")


if __name__ == "__main__":
    main()
