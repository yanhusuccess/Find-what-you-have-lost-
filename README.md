# 失物招领系统

一个功能完整、界面美观的失物招领Web应用系统，基于Flask框架开发。

## ✨ 主要功能

### 用户功能
- **用户认证**
  - 用户注册、登录、登出
  - 个人信息展示
  - 个人中心

- **失物管理**
  - 发布失物信息（支持图片上传）
  - 浏览所有失物启事
  - 搜索和筛选（按类别、关键词）
  - 查看失物详情
  - 更新失物状态（寻找中/已找到/已关闭）
  - 浏览计数

- **拾物管理**
  - 发布拾物信息（支持图片上传）
  - 浏览所有拾物信息
  - 搜索和筛选功能
  - 查看拾物详情
  - 更新拾物状态（待认领/已认领/已归还）

- **互动功能**
  - 评论系统（支持对失物和拾物发表评论）
  - 站内消息系统（用户间私信）
  - 未读消息提醒
  - 联系发布者

- **数据统计**
  - 总体数据统计
  - 类别分布图表（饼图）
  - 状态统计图表（柱状图）
  - 失物与拾物对比分析
  - 成功率统计

### 管理员功能
- **后台管理**
  - 用户管理
  - 失物信息管理
  - 拾物信息管理
  - 评论管理
  - 消息管理

## 🚀 技术栈

- **后端框架**: Flask 3.0.0
- **数据库**: SQLite (使用SQLAlchemy ORM)
- **用户认证**: Flask-Login
- **表单验证**: Flask-WTF + WTForms
- **管理后台**: Flask-Admin
- **前端框架**: Bootstrap 5
- **图标库**: Bootstrap Icons
- **图表库**: Chart.js
- **图片处理**: Pillow

## 📦 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd project_lost
```

### 2. 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 运行应用
```bash
python app.py
```

### 5. 访问应用
打开浏览器访问: http://localhost:5000

## 👤 默认管理员账号

- **用户名**: admin
- **密码**: admin123
- **管理后台**: http://localhost:5000/admin

## 📁 项目结构

```
project_lost/
├── app.py                  # 主应用文件
├── requirements.txt        # 项目依赖
├── README.md              # 项目说明
├── lostfound.db           # SQLite数据库（运行后自动生成）
├── templates/             # HTML模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── register.html     # 注册页面
│   ├── login.html        # 登录页面
│   ├── lost_list.html    # 失物列表
│   ├── found_list.html   # 拾物列表
│   ├── lost_detail.html  # 失物详情
│   ├── found_detail.html # 拾物详情
│   ├── new_lost.html     # 发布失物
│   ├── new_found.html    # 发布拾物
│   ├── profile.html      # 个人中心
│   ├── messages.html     # 消息列表
│   ├── send_message.html # 发送消息
│   ├── read_message.html # 读取消息
│   ├── statistics.html   # 数据统计
│   ├── 404.html          # 404错误页
│   └── 500.html          # 500错误页
├── static/                # 静态文件
│   ├── css/
│   │   └── style.css     # 自定义样式
│   ├── js/
│   │   └── main.js       # JavaScript脚本
│   └── uploads/          # 上传的图片
```

## 🎨 主要特性

### 1. 美观的用户界面
- 现代化设计风格
- 响应式布局，支持移动端
- 渐变色彩方案
- 流畅的动画效果
- 卡片式布局

### 2. 完善的搜索功能
- 按关键词搜索
- 按类别筛选
- 分页显示
- 实时搜索提示

### 3. 图片上传
- 支持JPG、PNG格式
- 最大16MB文件大小
- 图片预览功能
- 安全的文件名处理

### 4. 数据统计与可视化
- 饼图：类别分布
- 柱状图：状态统计
- 对比图：失物与拾物对比
- 实时数据更新

### 5. 消息系统
- 站内私信
- 未读消息提醒
- 消息分类（收件箱/发件箱）
- 消息已读/未读状态

### 6. 安全特性
- 密码加密存储
- CSRF保护
- 文件上传安全验证
- SQL注入防护（SQLAlchemy ORM）

## 🔧 配置说明

### 数据库配置
在 `app.py` 中修改数据库配置：
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lostfound.db'
```

### 上传文件夹配置
```python
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

### 密钥配置（生产环境请修改）
```python
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
```

## 📊 数据库模型

### User（用户）
- id, username, email, password_hash
- phone, is_admin, created_at
- 关系: lost_items, found_items, comments, messages

### LostItem（失物）
- id, title, description, category
- location, lost_date, image, status
- contact_info, reward, views
- 关系: author, comments

### FoundItem（拾物）
- id, title, description, category
- location, found_date, image, status
- contact_info, views
- 关系: author, comments

### Comment（评论）
- id, content, user_id
- lost_item_id, found_item_id, created_at

### Message（消息）
- id, subject, content
- sender_id, receiver_id, is_read, created_at

## 🌟 使用说明

### 发布失物信息
1. 登录账号
2. 点击"发布失物"
3. 填写物品详细信息
4. 上传物品图片（可选）
5. 提交发布

### 发布拾物信息
1. 登录账号
2. 点击"发布拾物"
3. 填写拾到物品的详细信息
4. 上传物品图片
5. 提交发布

### 搜索物品
1. 进入失物或拾物列表
2. 使用搜索框输入关键词
3. 选择物品类别筛选
4. 点击搜索查看结果

### 联系发布者
1. 查看物品详情
2. 点击"联系发布者"
3. 填写消息主题和内容
4. 发送消息

## 🔐 安全建议

1. **生产环境部署前**：
   - 修改 SECRET_KEY
   - 使用更安全的数据库（如PostgreSQL、MySQL）
   - 配置HTTPS
   - 设置合适的文件上传限制
   - 启用日志记录

2. **定期备份数据库**

3. **更新依赖包**：
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## 📝 许可证

MIT License

## 👨‍💻 开发者

如有问题或建议，请联系：
- Email: support@lostfound.com
- Phone: 400-123-4567

## 🙏 致谢

感谢所有开源项目的贡献者！

