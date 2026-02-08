# NVIDIA ASR GUI - 语音转文字工具

一个功能强大的语音转文字 GUI 应用程序，支持多种语音识别模型和语言。

## 功能特性

- 🎤 **多种模型支持**：可选择 NVIDIA API 或本地 Whisper 模型
- 🌍 **多语言支持**：支持中文、英文、日语、韩语、法语、德语、西班牙语、意大利语、葡萄牙语、俄语等
- 🎯 **多种模型大小**：Whisper 模型支持 Tiny、Base、Small、Medium、Large 五种大小
- 📝 **智能断句**：自动按标点符号分割句子，每句一行
- 🔄 **自动格式转换**：支持多种音频格式，自动转换为 WAV 格式
- 💾 **自动保存**：转录结果自动保存为 TXT 文件
- 🔧 **调试信息**：提供详细的调试信息，方便排查问题

## 安装方法

### 1. 克隆或下载项目

```bash
cd /Users/lanma/Downloads/Program/NVIDIA\ ASR
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量（可选但推荐）

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的配置
# 注意：.env 文件已添加到 .gitignore，不会被提交到版本控制
```

### 4. 安装 ffmpeg（可选，用于音频格式转换）

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载并安装
```

## 使用方法

### 启动程序

```bash
python3 asr_gui.py
```

### 界面操作

1. **选择语音文件**：点击"浏览"按钮选择音频文件
2. **选择模型**：
   - **NVIDIA API**：使用 NVIDIA 云端 API，需要网络连接
   - **本地 Whisper**：使用本地 Whisper 模型，无需网络
3. **选择模型大小**（仅本地 Whisper）：
   - Tiny：最快，准确度较低
   - Base：平衡速度和准确度（推荐）
   - Small：准确度较高
   - Medium：准确度高
   - Large：最准确，速度较慢
4. **选择语言**：支持自动检测或指定语言
5. **点击"处理"**：开始语音转文字

### 支持的音频格式

- WAV
- MP3
- M4A
- FLAC
- OGG
- OPUS

## 模型对比

| 特性 | NVIDIA API | 本地 Whisper |
|------|-----------|-------------|
| 速度 | 快 | 取决于模型大小 |
| 准确性 | 高 | 高（Large 模型） |
| 网络要求 | 需要网络 | 不需要网络 |
| 隐私 | 数据上传到服务器 | 完全本地处理 |
| 成本 | 可能产生 API 费用 | 免费 |
| 首次使用 | 即时 | 需要下载模型 |

## 配置说明

### 环境变量配置（推荐）

程序支持通过 `.env` 文件配置敏感信息，避免将密钥硬编码在代码中。

#### 创建配置文件

1. 复制配置模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的配置：
```bash
# NVIDIA API 配置
NVIDIA_API_KEY=your-nvidia-api-key-here
NVIDIA_SERVER=grpc.nvcf.nvidia.com:443
NVIDIA_FUNCTION_ID=your-function-id-here

# Whisper 配置
WHISPER_MODEL_SIZE=base
WHISPER_CACHE_DIR=~/.cache/whisper

# 音频配置
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

# 语言配置
DEFAULT_LANGUAGE=multi

# 其他配置
ENABLE_DEBUG=false
AUTO_SAVE_RESULTS=true
```

#### 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|---------|
| NVIDIA_API_KEY | NVIDIA API 密钥 | - |
| NVIDIA_SERVER | NVIDIA 服务器地址 | grpc.nvcf.nvidia.com:443 |
| NVIDIA_FUNCTION_ID | NVIDIA 函数 ID | - |
| WHISPER_MODEL_SIZE | Whisper 模型大小 | base |
| WHISPER_CACHE_DIR | Whisper 模型缓存目录 | ~/.cache/whisper |
| AUDIO_SAMPLE_RATE | 音频采样率 | 16000 |
| AUDIO_CHANNELS | 音频通道数 | 1 |
| DEFAULT_LANGUAGE | 默认语言 | multi |
| ENABLE_DEBUG | 启用调试模式 | false |
| AUTO_SAVE_RESULTS | 自动保存结果 | true |

### NVIDIA API 配置

如果不想使用 `.env` 文件，也可以直接编辑 `asr_gui.py` 文件：

```python
self.api_key = "your-api-key"
self.server = "grpc.nvcf.nvidia.com:443"
self.function_id = "your-function-id"
```

### Whisper 模型缓存

Whisper 模型首次使用时会自动下载并缓存到：
- macOS: `~/.cache/whisper/`
- Linux: `~/.cache/whisper/`
- Windows: `C:\Users\<username>\.cache\whisper\`

## 常见问题

### 1. Whisper 模型下载失败

**问题**：出现 SSL 证书验证错误

**解决方案**：程序已自动处理 SSL 证书验证问题，无需手动干预。

### 2. 音频格式不支持

**问题**：提示文件格式不支持

**解决方案**：确保已安装 ffmpeg，程序会自动转换不支持的格式。

### 3. NVIDIA API 连接失败

**问题**：无法连接到 NVIDIA 服务器

**解决方案**：
- 检查网络连接
- 确认 API 密钥有效
- 尝试使用本地 Whisper 模型

### 4. 转录结果不准确

**解决方案**：
- 尝试更大的 Whisper 模型
- 确保音频质量良好
- 指定正确的语言而不是自动检测

## 项目结构

```
NVIDIA ASR/
├── asr_gui.py              # 主程序文件
├── requirements.txt         # Python 依赖
├── README.md              # 项目说明文档
├── .env.example           # 环境变量配置模板
├── .env                  # 环境变量配置文件（不提交到版本控制）
├── .gitignore           # Git 忽略配置
├── install.sh            # 自动安装脚本
└── python-clients/        # NVIDIA Riva 客户端库
    ├── riva/            # Riva 核心库
    ├── scripts/         # 示例脚本
    └── tests/          # 测试文件
```

## 技术栈

- **GUI 框架**：Tkinter
- **语音识别**：
  - NVIDIA Riva API
  - OpenAI Whisper
- **音频处理**：PyAudio, ffmpeg
- **网络通信**：gRPC
- **配置管理**：python-dotenv

## 许可证

本项目遵循相关开源许可证。NVIDIA Riva 客户端库遵循其各自的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.2.0 (2025-02-08)
- ✨ 新增 .env 环境变量配置支持
- ✨ 新增配置文件模板 (.env.example)
- 🔒 将敏感信息（API 密钥）移至 .env 文件
- 📝 更新文档，添加详细配置说明
- 🛡️ 更新 .gitignore，保护 .env 文件不被提交

### v1.1.0 (2025-02-08)
- ✨ 新增本地 Whisper 模型支持
- ✨ 新增多种模型大小选择
- ✨ 新增 SSL 证书验证自动处理
- 🐛 修复模型加载错误
- 🐛 修复音频格式转换问题

### v1.0.0 (2025-02-08)
- 🎉 初始版本发布
- ✨ 支持 NVIDIA API 语音识别
- ✨ 支持多语言转录
- ✨ 支持多种音频格式
