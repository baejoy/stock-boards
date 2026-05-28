# 连板股池 看盘 · 公网部署版

一个**完全免费**的 A 股连板股看盘网站。GitHub Actions 每 5 分钟自动抓取涨停板池数据，前端是纯静态网页托管在 GitHub Pages，任何设备打开网址就能看。点股票卡片可跳转东方财富/同花顺/雪球的真实看盘页。

## 你将得到

- 一个永久网址，类似 `https://你的用户名.github.io/仓库名/`
- 任何设备访问（手机、平板、电脑都行）
- 5 分钟级更新（交易时段自动跑）
- 完全免费，电脑无需开机

## 项目结构

```
.
├── .github/workflows/
│   └── update-data.yml      # GitHub Actions 定时任务
├── scripts/
│   └── fetch_data.py        # 抓数据脚本（Actions 调用）
├── docs/                     # GitHub Pages 站点根目录
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── data/
│       └── boards.json      # 自动生成的数据
├── stock_data.py            # akshare 封装（核心逻辑）
├── app.py                   # 本地 Flask 调试用（可选）
├── requirements.txt
└── README.md
```

## 部署步骤（一次性，跟着做即可）

### 1. 装 Git（如果没装）

下载安装 https://git-scm.com/download/win，一路下一步即可。

### 2. 注册 GitHub 账号

https://github.com/signup ，免费的。

### 3. 在 GitHub 上建一个空仓库

- 打开 https://github.com/new
- 仓库名建议 `stock-boards`（自己起也行）
- **Public**（公共）— 这样 Actions 不限分钟数
- 不要勾 "Add README" / "Add .gitignore"（我们已经有了）
- 点 Create repository

### 4. 把代码推上去

在 PowerShell 里进入项目目录后执行（把 `你的用户名` 和 `仓库名` 换成你的）：

```powershell
cd "F:\Claude code babe"
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

第一次 push 会让你登录 GitHub，跟着提示走。

### 5. 开启 GitHub Pages

- 打开你 GitHub 仓库主页 → 顶部 `Settings` → 左侧 `Pages`
- Source 选 `Deploy from a branch`
- Branch 选 `main`，文件夹选 `/docs`
- 点 Save
- 等 1-2 分钟，页面会显示你的网址：`https://你的用户名.github.io/仓库名/`

### 6. 手动触发一次数据抓取（可选）

第一次部署时 `docs/data/boards.json` 是占位，需要 Actions 跑一次才有数据：

- 仓库主页 → 顶部 `Actions` 标签
- 左侧选 `Update stock data`
- 右上角 `Run workflow` → 绿色按钮
- 等 1-2 分钟完成
- 再过 1-2 分钟（Pages 部署延迟），打开你的网址就能看到数据了

之后每 5 分钟（交易时段）会自动跑，你无需任何操作。

## 本地预览（可选）

不部署也想在本地看看，需要 Python 3.9+：

```powershell
pip install -r requirements.txt
python app.py
```

打开 http://127.0.0.1:5000

## 重要说明

### 关于"实时"

- GitHub Actions 的 cron 在繁忙时段可能延迟几分钟，实际更新频率约 5-10 分钟
- akshare 拉的是东方财富盘中接口，盘中数据是当时快照
- 涨停板数据本身变化不剧烈（封板的票基本一整天保持），5 分钟级足够

### 交易时间

Actions 只在 A 股交易时段跑：
- 周一到周五
- 北京时间 9:00-15:55，每 5 分钟一次
- 收盘后 16:10 再补一次（最终数据）

非交易时段不跑，节省资源。

### Actions 跑失败了怎么办

去仓库 `Actions` 标签看具体哪个步骤错了。常见情况：
- akshare 在 GitHub 海外服务器上访问东财偶尔会超时 → 重跑一次就好
- 数据接口字段变了 → 改 `stock_data.py` 适配

### 改"最低连板"等设置

前端 `docs/app.js` 里改即可，提交 push 后 Pages 自动更新。

## 自定义扩展（再开 issue 找我加）

- 概念板块聚合（每个连板股属于哪些热门概念）
- 跌停股池、首板池
- 连板天梯图（多日连板的可视化）
- 自选股、收藏标签
- 移动端 PWA（添加到主屏幕）

## 免责声明

数据仅供学习研究，不构成任何投资建议。
