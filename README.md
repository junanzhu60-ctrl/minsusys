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

## 免费公开部署（Render + Neon）

项目已附带 `render.yaml`，可部署到 Render 免费 Web Service，并使用 Neon 免费 PostgreSQL。

1. 在 Neon 新建 PostgreSQL 项目，复制连接字符串到 Render 的 `DATABASE_URL`。
2. 将本项目推送到 GitHub 私有仓库后，在 Render 使用 **New → Blueprint** 选择该仓库。
3. Render 首次构建会自动执行迁移和静态文件收集；部署完成后获得 `https://minsusys.onrender.com` 一类的公开网址。

免费 Render 服务在约 15 分钟无访问后会休眠，下一次访问可能需要约一分钟启动；不要在仓库提交 `.env`、数据库口令或支付信息。

线上环境使用独立的 PostgreSQL 数据库，不会自动复制本地 MySQL 数据。部署时设置以下环境变量：

- `DATABASE_URL`：Neon PostgreSQL 连接字符串，需开启 SSL。
- `SECRET_KEY`：独立的随机密钥；`DEBUG=False`。
- `CLOUD_MEDIA_STORAGE=database`：将房源图片持久化到数据库，避免免费服务器重启后图片丢失。单张不超过 5 MB，支持 JPG、PNG、WebP、GIF。
- `DJANGO_SUPERUSER_USERNAME` 和 `DJANGO_SUPERUSER_PASSWORD`：首次部署初始化管理员。账号已存在时不会覆盖密码；初始化后可移除密码环境变量。

构建过程会自动收集静态文件、执行数据库迁移并初始化管理员。上线后使用 `/admin/` 管理房源；`/health/` 用于服务健康检查。线上启用 HTTPS 跳转和安全 Cookie。

当前扫码支付通过用户点击“我已支付”登记付款，没有接入微信支付回调，仅适合课程演示；正式收款需要人工核验或接入官方支付接口。
