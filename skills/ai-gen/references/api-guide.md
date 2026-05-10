# AI-Gen API 参考文档

Base URL: `https://llmapi.paratera.com/v1`
认证方式: `Authorization: Bearer sk-xxx`

---

## 模型能力矩阵

| 系列 | 文生图模型 | 文生视频模型 | API 端点族 |
|------|-----------|-------------|-----------|
| 豆包 Doubao | ❌ Seedream-3.0 已挂 | ✅ Doubao-Seedance-1.0-Pro | `/p001/` |
| GLM | ✅ GLM-CogView3-Flash | ❌ 无视频模型 | `/images/generations` |
| MiniMax | ❌ 无图片模型 | ✅ MiniMax-T2V-01-Directo | `/p004/` |

> 图片统一使用 GLM-CogView3-Flash（唯一可用图片模型）。视频可选豆包或 MiniMax。

---

## 1. 文生图 — GLM-CogView3-Flash (OpenAI 兼容)

所有图片模型共用此端点，与 provider 无关。

### Endpoint

```
POST /v1/images/generations
```

### Request

```json
{
    "model": "GLM-CogView3-Flash",
    "prompt": "A cute robot waving in a futuristic city",
    "n": 1,
    "size": "1024x1024"
}
```

**参数说明:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | 模型名，如 `GLM-CogView3-Flash` |
| prompt | string | 是 | 图片描述提示词 (英文效果更好) |
| n | int | 否 | 生成数量，默认 1 |
| size | string | 否 | 图片尺寸，默认 `1024x1024` |

**可选 size 值:** `1024x1024`, `1536x1024`, `1024x1536`

### Response

返回 base64 或 URL:

```json
{"data": [{"b64_json": "base64编码的图片数据"}]}
```

或

```json
{"data": [{"url": "https://example.com/image.jpg"}]}
```

---

## 2. 文生视频 — 豆包 Doubao (`/p001/` 族)

异步流程: **提交任务 → 轮询状态 → 下载视频**

### 2.1 提交任务

```
POST /v1/p001/contents/generations/tasks
```

```json
{
    "model": "Doubao-Seedance-1.0-Pro",
    "content": [
        {
            "type": "text",
            "text": "A robot walking through a neon-lit corridor --ratio 16:9"
        }
    ]
}
```

**content.text 字段说明:**
- prompt 和参数写在同一个 text 中
- `--ratio`: 宽高比 (16:9, 9:16, 1:1, adaptive)
- `--dur`: 时长秒数 (5, 10)

**Response:**

```json
{"id": "task_id_abc123", "status": "running"}
```

### 2.2 轮询任务状态

```
GET /v1/p001/contents/generations/tasks?filter={"task_ids":["task_id_abc123"]}
```

`filter` 是 JSON 字符串，包含 `task_ids` 数组。

**进行中:**

```json
{"data": [{"id": "task_id_abc123", "status": "running"}]}
```

**完成:**

```json
{
    "data": [{
        "id": "task_id_abc123",
        "status": "succeeded",
        "result": {"s3_url": "https://example.com/video.mp4"}
    }]
}
```

**失败:** `status: "failed"`

状态值: `running` → `succeeded` / `failed`

### 2.3 下载视频

直接 GET 下载 `result.s3_url`。

### 2.4 图生视频 (扩展)

```json
{
    "model": "Doubao-Seedance-1.0-Pro",
    "content": [
        {"type": "text", "text": "The robot starts moving --ratio adaptive --dur 5"},
        {"type": "image_url", "image_url": {"url": "https://example.com/first_frame.png"}}
    ]
}
```

- `image_url` 提供首帧图片
- ratio 使用 `adaptive` 自适应图片比例

---

## 3. 文生视频 — MiniMax (`/p004/` 族)

异步流程: **提交任务 → 轮询状态 → 获取下载链接 → 下载视频**

### 3.1 提交任务

```
POST /v1/p004/video_generation
```

```json
{
    "model": "MiniMax-T2V-01-Directo",
    "prompt": "A robot dancing in a neon-lit corridor"
}
```

**参数说明:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | `MiniMax-T2V-01-Directo` |
| prompt | string | 是 | 视频描述提示词 |

**Response:**

```json
{"task_id": "abc123", "status": "Preparing"}
```

### 3.2 轮询任务状态

```
GET /v1/p004/query/video_generation?task_id=abc123
```

**状态值:** `Preparing` → `Queueing` → `Processing` → `Success` / `Fail`

**完成 Response:**

```json
{
    "task_id": "abc123",
    "status": "Success",
    "file_id": "file_xyz789"
}
```

**失败 Response:**

```json
{
    "task_id": "abc123",
    "status": "Fail"
}
```

### 3.3 获取下载链接

```
GET /v1/p004/files/retrieve?file_id=file_xyz789
```

**Response:**

```json
{
    "file": {
        "download_url": "https://example.com/video.mp4"
    }
}
```

### 3.4 下载视频

直接 GET 下载 `file.download_url`。

---

## 限流与注意事项

- 文生图: 同步返回，约 10-30 秒
- 文生视频: 异步，通常 2-5 分钟
- 建议 API Key 轮换使用，避免单 key 限流
- prompt 建议使用英文，效果更好
- 豆包视频 dur 参数仅支持 5 和 10 秒
- MiniMax 视频不支持 ratio/dur 参数（由模型自动决定）
