"""
AI 小说转剧本工具 - Flask 后端
支持大模型 API 调用 + 用户认证
"""

import os
import re
import json
import yaml
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from openai import OpenAI
from models import db, User, ConversionHistory

# 显式加载 .env 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
print(f"正在加载 .env 文件: {env_path}")
load_dotenv(env_path, override=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# 注册认证蓝图
from auth import auth_bp, UserLogin
app.register_blueprint(auth_bp)

# 从环境变量读取
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("MODEL_NAME", "deepseek-chat")

# 打印配置
print("=" * 60)
print(f"当前模型: {MODEL}")
print(f"API 地址: {OPENAI_BASE_URL}")
if len(OPENAI_API_KEY) > 10:
    print(f"密钥前10位: {OPENAI_API_KEY[:10]}...")
else:
    print(f"密钥前10位: {OPENAI_API_KEY}")
print("=" * 60)

# 初始化 OpenAI 客户端
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 示例小说数据
SAMPLE_NOVEL = """
第一章 初遇

清晨的阳光透过咖啡馆的落地窗洒在木桌上，张伟推开玻璃门走了进来。风铃发出清脆的响声。

"请问，这里有人吗？"张伟问道。

坐在角落的李娜抬起头，看到张伟后露出了微笑。"没有，请坐。"

两人相视而笑，空气中弥漫着咖啡的香气。

第二章 对话

张伟点了一杯拿铁，然后看向李娜。"你也常来这里吗？"

"是的，这里的咖啡很不错。"李娜回答，"我叫李娜。"

"张伟。"他伸出手。

两人握了握手，开始了愉快的交谈。
"""


def validate_and_fix(screenplay):
    """后处理校验：确保关键字段完整"""
    if not screenplay.get('characters') or len(screenplay['characters']) == 0:
        screenplay['characters'] = [{
            'id': 'C01',
            'name': '待补充',
            'description': '角色信息待人工补充'
        }]

    char_ids = {c['id'] for c in screenplay.get('characters', [])}

    for act in screenplay.get('acts', []):
        for scene in act.get('scenes', []):
            for d in scene.get('dialogues', []):
                speaker = d.get('speaker', '')
                if speaker in [None, '未知', '', '待补充'] or speaker not in char_ids:
                    d['speaker'] = '待补充'

                emotion = d.get('emotion')
                if emotion and emotion.strip() == '':
                    d['emotion'] = None

            if not scene.get('description') or scene['description'].strip() == '':
                scene['description'] = '场景描述待补充'

            if not scene.get('characters_present') or len(scene['characters_present']) == 0:
                scene['characters_present'] = ['待补充']

    return screenplay


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return UserLogin(user)
    return None


def init_db():
    """初始化数据库"""
    with app.app_context():
        print("[INIT] 正在初始化数据库...")
        try:
            db.create_all()
            print("[INIT] 数据库表创建成功")
        except Exception as e:
            print(f"[INIT] 数据库创建失败: {e}")


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
@login_required
def convert():
    data = request.get_json()
    novel_text = data.get("text", "").strip()
    user_title = data.get("title", "").strip()
    
    if not novel_text:
        return jsonify({"error": "请输入小说文本"}), 400

    try:
        # ========== 第 1 步：提取角色 ==========
        char_prompt = """从以下小说文本中提取所有出现的有名有姓的角色，以及有独立对话的未命名角色（用特征命名，如"服务员"）。
返回一个 JSON 数组，每个元素格式为 {"id": "C01", "name": "角色名", "description": "简短描述"}。
只返回 JSON，不要任何其他文字。"""

        print("第1步：提取角色...")
        char_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": char_prompt},
                {"role": "user", "content": novel_text}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        char_raw = char_response.choices[0].message.content.strip()
        print(f"角色提取原始返回: {char_raw[:200]}")
        
        # 清洗可能的 markdown 标记
        if char_raw.startswith("```"):
            char_raw = char_raw.split("\n", 1)[1]
        if char_raw.endswith("```"):
            char_raw = char_raw.rsplit("\n", 1)[0]
        characters = json.loads(char_raw)
        print(f"提取到 {len(characters)} 个角色")

        # ========== 第 2 步：拆分场景并填充对白/动作 ==========
        scene_prompt = f"""你是一个剧本格式化工具。小说中已识别的角色如下：
{json.dumps(characters, ensure_ascii=False)}

请将小说文本转换为 YAML 格式的剧本场景列表。结构如下：
scenes:
  - scene_id: 1
    location: "具体地点"
    time: "时段（清晨/上午/下午/傍晚/深夜）"
    type: "内景"或"外景"
    description: "场景描述"
    characters_present: ["C01", "C02"]
    dialogues:
      - speaker: "C01"
        emotion: "平静/激动/悲伤/紧张/坚定/null"
        line: "对白内容"
    actions:
      - "动作描述"
    notes: ""

规则：
1. 对白必须严格从原文提取，不编造。
2. 动作从原文叙述中提取。
3. speaker 必须用上面的角色 ID。
4. 只输出 YAML 格式的 scenes 列表，不要任何其他文字。"""

        print("第2步：拆分场景...")
        scene_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": scene_prompt},
                {"role": "user", "content": novel_text}
            ],
            temperature=0.1,
            max_tokens=4096
        )
        scene_raw = scene_response.choices[0].message.content.strip()
        print(f"场景拆分原始返回: {scene_raw[:300]}")
        
        if scene_raw.startswith("```"):
            scene_raw = scene_raw.split("\n", 1)[1]
        if scene_raw.endswith("```"):
            scene_raw = scene_raw.rsplit("\n", 1)[0]
        scene_raw = scene_raw.replace('yaml', '', 1).strip()
        scenes_data = yaml.safe_load(scene_raw)
        print(f"提取到 {len(scenes_data.get('scenes', []))} 个场景")

        # ========== 第 3 步：组装最终结构 ==========
        final_output = {
            "meta": {
                "title": user_title if user_title else "未命名作品",
                "adapted_from": "用户提供文本",
                "total_scenes": len(scenes_data.get("scenes", [])),
                "generated_at": datetime.now().isoformat()
            },
            "characters": characters,
            "acts": [
                {
                    "act_number": 1,
                    "title": "第一幕",
                    "scenes": scenes_data.get("scenes", [])
                }
            ]
        }

        # 后处理校验
        final_output = validate_and_fix(final_output)
        
        output_yaml = yaml.dump(final_output, allow_unicode=True, sort_keys=False, default_flow_style=False)
        
        # 保存到数据库
        conversion = ConversionHistory(
            user_id=current_user.id,
            title=user_title or final_output.get("meta", {}).get("title", "未命名"),
            input_text=novel_text,
            output_yaml=output_yaml,
            output_parsed=json.dumps(final_output, ensure_ascii=False)
        )
        db.session.add(conversion)
        db.session.commit()
        
        print(f"[OK] 保存成功！用户ID: {current_user.id}, 标题: {conversion.title}, 记录ID: {conversion.id}")

        return jsonify({"yaml": output_yaml, "parsed": final_output})

    except json.JSONDecodeError as e:
        print(f"角色提取 JSON 解析失败: {str(e)}")
        return jsonify({"error": f"角色提取 JSON 解析失败: {str(e)}"}), 500
    except yaml.YAMLError as e:
        print(f"场景 YAML 解析失败: {str(e)}")
        return jsonify({"error": f"场景 YAML 解析失败: {str(e)}"}), 500
    except Exception as e:
        print(f"转换出错: {str(e)}")
        return jsonify({"error": f"转换出错: {str(e)}"}), 500


@app.route("/history")
@login_required
def history():
    convs = ConversionHistory.query.filter_by(user_id=current_user.id).order_by(ConversionHistory.created_at.desc()).all()
    return render_template("history.html", conversions=convs)


@app.route("/sample")
def sample():
    return jsonify({
        'text': SAMPLE_NOVEL,
        'title': '示例小说'
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
