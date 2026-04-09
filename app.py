#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart-Monitor-Ops - AI 告警辅助诊断系统
接收 Alertmanager 告警，调用 DeepSeek 进行智能诊断
"""

import os
import json
import yaml
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# 配置日志
def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"alerts_{datetime.now().strftime('%Y%m%d')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

import sys
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
logger = setup_logging()


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_openai_client():
    """初始化 OpenAI 客户端"""
    import openai
    config = load_config()
    api_config = config.get("api", {})
    
    api_key = api_config.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
    base_url = api_config.get("base_url", "https://api.deepseek.com")
    model = api_config.get("model", "deepseek-chat")
    
    if not api_key:
        raise ValueError("API Key 未配置！请在 config.yaml 中设置或设置环境变量 DEEPSEEK_API_KEY")
    
    return openai.OpenAI(api_key=api_key, base_url=base_url), model


def build_diagnostic_prompt(alert):
    """构建诊断 Prompt"""
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    
    alertname = labels.get("alertname", "Unknown")
    description = annotations.get("description", "")
    summary = annotations.get("summary", "")
    severity = labels.get("severity", "warning")
    
    prompt = f"""你是一位资深运维工程师，擅长排查系统故障。

系统触发了告警：
- 告警名称: {alertname}
- 告警级别: {severity}
- 告警描述: {description}
- 摘要: {summary}

请按照以下格式给出诊断报告：

🔎 可能原因：
（列出 3-5 条最可能的原因，按可能性从高到低排序）

🔧 排查命令：
（给出具体的排查命令，最好是 Linux 命令）

📝 处理建议：
（给出具体可操作的处理步骤）

注意：只返回诊断内容，不要有额外的前言或总结。"""
    
    return prompt


def call_ai_diagnose(prompt):
    """调用 AI 进行诊断"""
    client, model = get_openai_client()
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024
    )
    
    return response.choices[0].message.content


def save_alert_history(alert, diagnosis):
    """保存诊断结果到历史记录"""
    config = load_config()
    if not config.get("alerts", {}).get("save_history", True):
        return
    
    history_dir = config.get("alerts", {}).get("history_dir", "alerts")
    history_path = os.path.join(os.path.dirname(__file__), history_dir)
    os.makedirs(history_path, exist_ok=True)
    
    alertname = alert.get("labels", {}).get("alertname", "unknown")
    filename = f"{alertname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "alert": alert,
        "diagnosis": diagnosis
    }
    
    with open(os.path.join(history_path, filename), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    
    logger.info(f"诊断记录已保存: {filename}")


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "service": "Smart-Monitor-Ops"})


@app.route("/alert", methods=["POST"])
def handle_alert():
    """接收 Alertmanager 告警"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        alerts = data.get("alerts", [])
        if not alerts:
            return jsonify({"error": "No alerts in payload"}), 400
        
        results = []
        for alert in alerts:
            # 跳过 resolved 状态的告警
            if alert.get("status") == "resolved":
                logger.info(f"告警已恢复: {alert.get('labels', {}).get('alertname')}")
                continue
            
            alertname = alert.get("labels", {}).get("alertname", "Unknown")
            logger.info(f"收到告警: {alertname}")
            
            # 构建诊断 Prompt
            prompt = build_diagnostic_prompt(alert)
            
            # 调用 AI 诊断
            try:
                diagnosis = call_ai_diagnose(prompt)
                logger.info(f"AI 诊断完成: {alertname}")
            except Exception as e:
                diagnosis = f"AI 诊断失败: {str(e)}"
                logger.error(f"诊断异常: {e}")
            
            # 保存历史记录
            save_alert_history(alert, diagnosis)
            
            # 构建响应
            result = {
                "alertname": alertname,
                "status": "diagnosed",
                "diagnosis": diagnosis
            }
            results.append(result)
            
            # 打印诊断结果
            print(f"\n🤖 AI 诊断报告 - {alertname}")
            print("=" * 50)
            print(diagnosis)
            print("=" * 50)
        
        return jsonify({
            "status": "success",
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"处理告警失败: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║       🤖 Smart-Monitor-Ops 智能告警诊断系统         ║
║     Prometheus + DeepSeek 告警自动分析诊断          ║
╚══════════════════════════════════════════════════╝
    """)
    print("🚀 服务启动: http://localhost:5000")
    print("📡 Webhook 端点: http://localhost:5000/alert")
    print("❤️ 健康检查: http://localhost:5000/health\n")
    
    app.run(host="0.0.0.0", port=5000, debug=False)