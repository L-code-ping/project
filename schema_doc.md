# 剧本 YAML Schema 设计说明

## 1. 设计目标
- 兼顾**可读性**与**机器可解析性**，方便编剧快速浏览和编辑。
- 覆盖剧本拍摄所需的核心要素：场景、角色、对白、动作指示。
- 支持多幕结构，适应长篇改编。

## 2. 整体结构
```yaml
meta:          # 元信息
characters:    # 角色库
acts:          # 幕列表
```

### 2.1 meta
- `title`：作品名，便于归档。
- `adapted_from`：记录改编来源，方便回溯。
- `total_scenes`：场次总数，便于快速了解规模。
- `generated_at`：生成时间戳，用于版本管理。

### 2.2 characters
独立于幕/场景的全局角色列表，每个角色有唯一 id。

**设计原因**：
- 避免在不同场次中重复定义角色信息。
- 用 ID 关联对话，支持角色改名时一键替换，降低人工编辑成本。

### 2.3 acts
采用“幕（act）→ 场（scene）”两级结构。

**设计原因**：
- 符合传统剧本格式，导演和编剧接受度高。
- 为多章节长篇改编提供清晰的段落划分。

### 2.4 scene 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| scene_id | int | 全局递增编号，唯一标识 |
| location | str | 具体地点，如“张伟的卧室”，避免模糊 |
| time | str | 时段（清晨/上午/下午/傍晚/深夜） |
| type | str | 内景/外景，与 location 逻辑一致 |
| description | str | 场景环境描写，帮助美术和置景 |
| characters_present | list[str] | 本场出场角色 ID，方便统筹 |
| dialogues | list | 对白序列 |
| actions | list[str] | 舞台动作指示 |
| notes | str | 编剧备注，保留创作空间 |

### 2.5 dialogue 字段说明
- `speaker`：角色 ID，方便程序化统计词频和对白占比。
- `emotion`：语气提示，可选，辅助表演指导。
- `line`：台词原文。

### 2.6 为什么用 YAML 而非 JSON
- YAML 支持注释（#），方便编剧添加批注。
- 缩进式语法更接近剧本阅读习惯，编辑门槛低。
- 业内部分剧本软件（如 Fountain 的变体）偏好 YAML 作为中间格式。

## 3. 设计权衡
- 保留 notes 字段：AI 生成结果可能有偏差，给人工修改留有余地。
- emotion 允许 null：强制 AI 推断可能出错，交由编剧补充更稳妥。
- actions 与 dialogues 分离：便于导演分别排演动作和对白。

## 4. 实践中的设计调整
基于三章小说文本的测试，发现：
- `emotion` 标注需要结合上下文推断，AI 标注“平静”过多时，人工可改为“克制”“隐忍”“宠溺”等更细腻的情感词。
- 角色ID关联的方式在处理多角色场景时优势明显——医院场景中有病人、护士、家属等多方，用ID避免了重复定义。
- `actions` 字段承载了大量原文的叙述性描写，是保证剧本不丢失原著细节的关键。

## 5. 输出示例
```yaml
meta:
  title: "深夜来电"
  adapted_from: "第1章至第3章"
  total_scenes: 6
  generated_at: "2026-06-07T12:00:00"

characters:
  - id: C01
    name: "陈屿"
    description: "年轻男子，关心林栀"
  - id: C02
    name: "林栀"
    description: "年轻女子，经历困难"

acts:
  - act_number: 1
    title: "第一幕"
    scenes:
      - scene_id: 1
        location: "陈屿家卧室"
        time: "凌晨两点"
        type: "内景"
        description: "昏暗的卧室，手机屏幕发出微弱的光"
        characters_present: ["C01"]
        dialogues:
          - speaker: "C01"
            emotion: "疑惑"
            line: "这么晚了，谁会打电话？"
        actions:
          - "陈屿被手机震动惊醒"
          - "他拿起手机看了看屏幕"
        notes: ""
```

## 6. 启动步骤

1. 在项目根目录创建 `.env` 文件，填入真实 API 密钥：
   ```
   OPENAI_API_KEY=你的API密钥
   OPENAI_BASE_URL=https://api.deepseek.com/v1
   MODEL_NAME=deepseek-chat
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 启动服务：
   ```bash
   python app.py
   ```

4. 浏览器打开 http://127.0.0.1:5000，粘贴小说文本即可转换。
