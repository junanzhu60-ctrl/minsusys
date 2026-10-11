# 民宿管理系统

一个使用 Django 构建的民宿预订与管理系统基础版，默认连接 MySQL 数据库 `minsudb`，适合本地开发和课程项目演示。

## 已有功能

- 房源展示、详情、设施与图片链接
- 住客提交预订申请，自动核算住宿晚数与总价
- 防止同一房源的已确认订单日期重叠
- Django 管理后台：管理房源、订单、住客和房态
- 简洁的中文响应式页面

## 启动

请先在电脑上安装 Python 3.11 或更高版本、MySQL，并在项目目录执行：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，填写 MySQL 的账号和密码
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

打开 <http://127.0.0.1:8000/> 查看预订页面；打开 <http://127.0.0.1:8000/admin/> 进入后台。

## 后续建议

## 免费公开部署（Render + Neon）

项目已附带 `render.yaml`，可部署到 Render 免费 Web Service，并使用 Neon 免费 PostgreSQL。

1. 在 Neon 新建 PostgreSQL 项目，复制连接字符串到 Render 的 `DATABASE_URL`。
2. 将本项目推送到 GitHub 私有仓库后，在 Render 使用 **New → Blueprint** 选择该仓库。
3. Render 首次构建会自动执行迁移和静态文件收集；部署完成后获得 `https://minsusys.onrender.com` 一类的公开网址。

免费 Render 服务在约 15 分钟无访问后会休眠，下一次访问可能需要约一分钟启动；不要在仓库提交 `.env`、数据库口令或支付信息。
