# 📚 VLM Book Cover Extractor

基于视觉语言模型（VLM）的图书封面信息自动提取工具

> **Note**: 代码正在逐步整理完善中

---

## ✨ 项目简介

本项目利用视觉语言模型（Vision Language Model）自动识别并提取图书封面中的关键信息，包括书名、作者、出版社等元数据。基于 Qwen-VL 系列模型，通过兼容 OpenAI API 规范的接口调用，实现高效批量处理。

## 🗂️ 项目结构

```
vlm-book-cover-extractor/
├── main.py                    # 主程序入口
├── config/                    # 配置文件夹
│   └── prompts/               # 请求提示词
├── book_covers/               # 封面图片 & 处理记录
├── Evaluation_System/         # 评估系统
├── processing_errors.log      # 错误日志
└── README.md
```

## 🚀 快速开始

### 环境准备

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/vlm-book-cover-extractor.git
   cd vlm-book-cover-extractor
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置 API Key**
   
   本项目使用 Qwen 系列视觉语言模型。请前往 [阿里云百炼控制台](https://bailian.console.aliyun.com/) 申请 API Key：
   
   - 登录阿里云账号
   - 进入「大模型服务平台百炼」控制台
   - 在 API-KEY 管理中创建密钥
   
   获取后在环境变量中配置：
   ```bash
   export DASHSCOPE_API_KEY="your-api-key-here"
   ```

### 运行程序

```bash
python main.py
```

## 📋 功能特性

- ✅ 支持 OpenAI API 规范的 VLM 接口
- ✅ 自动错误重试机制
- ✅ 详细的错误日志记录（`processing_errors.log`）
- ✅ 批量处理图书封面图片
- ✅ 可自定义提示词配置

## 📁 数据集

`book_covers` 文件夹用于存放待处理的图书封面图片，同时也会保存处理记录。

> 📧 **完整数据集获取**：由于相关论文尚未发表，完整数据集将在论文见刊后开源。如需获取，请提交 [Issue](../../issues) 并留下您的邮箱。

## 🖥️ 本地部署

如需本地部署模型，推荐使用 [llama.cpp](https://github.com/ggerganov/llama.cpp) 进行推理加速。

### 基本步骤

1. 下载并编译 llama.cpp
2. 获取支持视觉的模型权重（如 LLaVA）
3. 配置 API 服务端点指向本地服务

## 🌐 人工评分系统

基于 Web 的人工评分系统正在整理代码及文档，在Evaluation_System目录下，目录下有完整的运行文档（2025/12/18更新）。

## 📝 配置说明

### 提示词配置

`config/` 文件夹下存放请求所需的提示词模板，可根据需求自定义修改。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

[Apache License 2.0](LICENSE)

## 📮 联系方式

如有问题或建议，请通过 [Issue](../../issues) 联系我们。

---

<p align="center">
  <sub>如果这个项目对您有帮助，请给一个 ⭐ Star</sub>
</p>
