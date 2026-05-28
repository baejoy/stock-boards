"""读取 docs/data/boards.json，按连板数倒序组织成 HTML 邮件，通过 163 SMTP 发送。

用法 (本地手工 / GitHub Actions 通用)：
    设置环境变量：
      MAIL_USER  发件 163 邮箱，例如 baejoy@163.com
      MAIL_PASS  163 SMTP 授权码（不是登录密码，需在 163 邮箱设置里开启 SMTP 服务并生成）
      MAIL_TO    收件邮箱，逗号分隔可多个，例如 baejoy@163.com
      MIN_BOARDS 最低连板数过滤，默认 2

    python scripts/send_email.py

退出码：0 成功，1 配置/数据错误，2 发送失败。
"""
import json
import os
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BJ_TZ = timezone(timedelta(hours=8))
SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465


def _fmt_time(s: str) -> str:
    """'095140' -> '09:51:40'；非法值原样返回。"""
    if not s or not isinstance(s, str) or len(s) != 6 or not s.isdigit():
        return s or "--"
    return f"{s[0:2]}:{s[2:4]}:{s[4:6]}"


def _fmt_yi(v) -> str:
    """元 -> 亿，保留 2 位。"""
    try:
        return f"{float(v) / 1e8:.2f}"
    except (TypeError, ValueError):
        return "--"


def _fmt_pct(v) -> str:
    try:
        return f"{float(v):.2f}%"
    except (TypeError, ValueError):
        return "--"


def _row(stock: dict) -> str:
    last_seal = _fmt_time(stock.get("last_seal", ""))
    first_seal = _fmt_time(stock.get("first_seal", ""))
    seal_time = last_seal if stock.get("break_times", 0) else first_seal
    return f"""
      <tr>
        <td>{stock.get('boards', '')}</td>
        <td><a href="{stock.get('eastmoney_url', '#')}">{stock.get('code', '')}</a></td>
        <td>{stock.get('name', '')}</td>
        <td>{stock.get('industry', '')}</td>
        <td style="text-align:right;">{_fmt_pct(stock.get('change_pct'))}</td>
        <td style="text-align:right;">{stock.get('price', '')}</td>
        <td style="text-align:right;">{_fmt_yi(stock.get('seal_amount'))}</td>
        <td style="text-align:right;">{_fmt_yi(stock.get('turnover'))}</td>
        <td style="text-align:right;">{_fmt_pct(stock.get('turnover_rate'))}</td>
        <td style="text-align:right;">{_fmt_yi(stock.get('float_cap'))}</td>
        <td style="text-align:center;">{seal_time}</td>
        <td style="text-align:center;">{stock.get('break_times', 0)}</td>
      </tr>"""


def build_html(payload: dict, min_boards: int) -> tuple[str, str, int]:
    """返回 (subject, html_body, kept_count)。"""
    groups = payload.get("groups", {})
    data_date = payload.get("data_date", "")
    updated_at = payload.get("updated_at", "")

    # 按连板数倒序
    kept = sorted(
        ((int(k), v) for k, v in groups.items() if int(k) >= min_boards),
        key=lambda x: -x[0],
    )
    total = sum(len(v) for _, v in kept)

    rows = []
    for boards, stocks in kept:
        # 同一连板数内按封单金额倒序
        stocks_sorted = sorted(stocks, key=lambda s: -(s.get("seal_amount") or 0))
        for s in stocks_sorted:
            rows.append(_row(s))

    nice_date = f"{data_date[:4]}-{data_date[4:6]}-{data_date[6:]}" if len(data_date) == 8 else data_date
    subject = f"[连板池] {nice_date} {min_boards}板+ 共 {total} 只"

    if total == 0:
        body_inner = f'<p style="color:#888;">数据日 {nice_date} 没有 {min_boards} 板及以上的票。</p>'
    else:
        summary = " ".join(f"{b}板 {len(v)}只" for b, v in kept)
        body_inner = f"""
        <p>数据日：<b>{nice_date}</b>　共 <b>{total}</b> 只　（{summary}）</p>
        <table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;font-size:13px;font-family:'Microsoft YaHei',Arial,sans-serif;">
          <thead style="background:#f4f4f4;">
            <tr>
              <th>连板</th><th>代码</th><th>名称</th><th>行业</th>
              <th>涨幅</th><th>现价</th>
              <th>封单(亿)</th><th>成交(亿)</th><th>换手</th><th>流通市值(亿)</th>
              <th>封板时间</th><th>炸板</th>
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        <p style="color:#888;font-size:12px;margin-top:12px;">
          说明：封板时间在「炸板≥1」时显示最后封板，否则显示首次封板。数据源：东方财富涨停股池。更新时间 {updated_at}。
        </p>"""

    html = f"""<!doctype html><html><body style="font-family:'Microsoft YaHei',Arial,sans-serif;">
      <h2 style="margin:0 0 12px;">连板股池 — {nice_date}</h2>
      {body_inner}
    </body></html>"""
    return subject, html, total


def send(subject: str, html: str, user: str, password: str, to_addrs: list[str]) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("连板股池", user))
    msg["To"] = ", ".join(to_addrs)
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.sendmail(user, to_addrs, msg.as_string())


def main() -> int:
    user = os.environ.get("MAIL_USER", "").strip()
    password = os.environ.get("MAIL_PASS", "").strip()
    to_raw = os.environ.get("MAIL_TO", "").strip()
    min_boards = int(os.environ.get("MIN_BOARDS", "2"))

    if not user or not password or not to_raw:
        print("[error] MAIL_USER / MAIL_PASS / MAIL_TO 必须设置", file=sys.stderr)
        return 1
    to_addrs = [a.strip() for a in to_raw.split(",") if a.strip()]

    data_file = ROOT / "docs" / "data" / "boards.json"
    if not data_file.exists():
        print(f"[error] {data_file} 不存在", file=sys.stderr)
        return 1
    payload = json.loads(data_file.read_text(encoding="utf-8"))

    subject, html, total = build_html(payload, min_boards)
    print(f"[build] subject={subject!r} rows={total}")

    try:
        send(subject, html, user, password, to_addrs)
    except Exception as e:
        print(f"[error] send failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    now_bj = datetime.now(BJ_TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[ok] sent to {to_addrs} at {now_bj} BJT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
