# 🤖 Smart-Monitor-Ops

> 基于 Prometheus + DeepSeek 的 AI 告警辅助诊断系统

[English](./README.md) | 简体中文

---

## ✨ 功能特点

- 🔔 **Webhook 接收**：实时接收 Alertmanager 告警
- 🧠 **AI 智能诊断**：调用 DeepSeek 分析告警原因，提供排查建议
- 📱 **多渠道通知**：支持钉钉、企业微信、Slack 等
- 📊 **历史记录**：自动保存诊断结果到 `alerts/` 目录
- 🐳 **Docker 部署**：一键启动，无需复杂配置

---

## 📁 项目结构

```
Smart-Monitor-Ops/
├── app.py                    # 核心 Flask Webhook 服务
├── config.example.yaml       # 配置文件模板
├── requirements.txt          # Python 依赖
├── .gitignore
├── alerts/                   # 历史告警诊断记录
│   └── .gitkeep
├── scripts/                  # 部署脚本
│   └── docker-compose.yml
└── README.md
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- DeepSeek API Key

### 安装

```bash
git clone https://github.com/z2675039271-svg/Smart-Monitor-Ops.git
cd Smart-Monitor-Ops

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`：

```yaml
api:
  provider: "deepseek"
  api_key: "your-deepseek-key"
  base_url: "https://api.deepseek.com"
  model: "deepseek-chat"

notification:
  dingding:
    enabled: false
    webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
  webhook:
    enabled: false
    url: "http://your-webhook-url"

alerts:
  save_history: true
  history_dir: "alerts"
```

### 运行

```bash
python app.py
```

服务启动后，监听 `http://localhost:5000/alert`

---

## 🔧 Alertmanager 配置

在 Prometheus Alertmanager 配置中添加 webhook：

```yaml
receivers:
  - name: 'ai-diagnostic'
    webhook_configs:
      - url: 'http://your-server:5000/alert'
```

---

## 📱 告警示例

**原始告警：**
```
alertname: InstanceDown
description:Instance i-xxx has been down for more than 2 minutes
```

**AI 诊断结果：**
```
🔍 告警: InstanceDown
📋 描述: Instance i-xxx has been down for more than 2 minutes

🤖 AI 诊断报告：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔎 可能原因：
1. ECS 实例被手动重启或停止
2. 网络安全问题导致实例被安全组隔离
3. 阿里云控制台资源欠费导致实例被释放
4. 实例所在宿主机故障

🔧 排查命令：
1. 登录阿里云控制台 -> ECS -> 实例列表 -> 查看实例状态
2. 检查安全组规则：aliyun ecs DescribeSecurityGroups
3. 查看欠费通知：登录阿里云账号 -> 费用中心
4. 查看云监控事件：aliyun cms DescribeEventLog

📝 处理建议：
1. 优先登录控制台查看实例状态
2. 如果实例已停止，检查是否有维护操作
3. 检查告警时间前后的操作日志
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🐳 Docker 部署

```bash
cd scripts
docker-compose up -d
```

---

## 📄 License

MIT License

---

## 👤 作者

- GitHub: [@z2675039271-svg](https://github.com/z2675039271-svg)
- Email: z2675039271@gmail.com