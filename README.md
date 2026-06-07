# AI 小说转剧本工具

一个帮助小说作者将作品快速改编成结构化剧本的 AI 辅助工具。

## 🎬 Demo 视频

[AI小说转剧本 - B站视频](https://www.bilibili.com/video/BV1dmE864EgS/?vd_source=85e6fc2208d8304404e8f392cc43e66c)

## 技术栈

- **后端**: Python + Flask
- **AI**: DeepSeek-Chat API
- **前端**: 原生 HTML/CSS/JS
- **数据库**: SQLite + SQLAlchemy
- **格式**: YAML

## 核心功能

1. ✅ 支持粘贴或上传小说文本
2. ✅ 自动识别角色、拆分场景
3. ✅ 输出结构化 YAML 剧本（含角色、场景、对白、动作、情绪标注）
4. ✅ 支持复制、下载 YAML 文件
5. ✅ 提供剧本预览模式
6. ✅ 用户注册与登录
7. ✅ 转换历史记录

## 创新点

- **全局角色ID关联**：方便后续统计和替换
- **情绪标注可选**：尊重编剧创作空间
- **保留 notes 字段**：给人工打磨留有余地
- **动作与对白分离**：方便导演分别调度

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 并填入你的 DeepSeek API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
```

### 3. 启动服务

```bash
python app.py
```

访问 http://127.0.0.1:5000

## 项目结构

```
novel-to-script/
├── app.py                 # Flask 主应用
├── auth.py                # 用户认证模块
├── models.py              # 数据库模型
├── requirements.txt       # 依赖配置
├── .env.example           # API 密钥配置模板
├── .env                   # API 密钥配置（需创建）
├── schema_doc.md          # Schema 设计文档
├── start_server.py        # 服务器启动脚本
├── instance/
│   └── conversions.db     # SQLite 数据库文件
└── templates/
    ├── base.html          # 基础模板
    ├── index.html         # 主转换页面
    ├── history.html       # 历史记录页面
    ├── login.html         # 登录页面
    └── register.html      # 注册页面
```

## 使用说明

1. **注册/登录**：首次使用请先注册账号
2. **输入小说**：在"作品标题"输入框填写小说名称，粘贴小说文本或上传 `.txt` 文件
3. **开始转换**：点击"转换为剧本 YAML"按钮
4. **查看结果**：在输出区域查看 YAML 格式剧本或剧本预览
5. **保存结果**：点击"复制"或"下载"保存结果
6. **查看历史**：点击导航栏"历史记录"查看过往转换记录

## YAML 输出格式

输出的剧本包含以下结构：
- `meta`: 作品元信息（标题、来源、场景数、生成时间）
- `characters`: 角色列表（角色ID、姓名、描述）
- `acts`: 幕结构（每幕包含多个场景）
- `scenes`: 场景详情（地点、时间、角色、对话、动作）

## API 配置说明

目前支持 DeepSeek API，配置方式：
- API Key: 在 [DeepSeek 控制台](https://platform.deepseek.com/) 获取
- 基础 URL: `https://api.deepseek.com/v1`
- 模型名称: `deepseek-chat`

## 许可证

MIT License