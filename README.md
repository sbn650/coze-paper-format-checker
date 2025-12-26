# 📄 智能体论文格式提取器

一个用于提取论文格式信息的API服务，专为智能体工作流设计。

## ✨ 功能特性

- 📊 提取段落字体、字号、加粗、斜体信息
- 📐 分析对齐方式、行间距、首行缩进
- 📏 获取段前段后间距
- 🔄 支持模板与用户论文对比
- 🚀 一键部署到云平台

## 🛠️ API接口

### 健康检查


### 格式提取
POST /extract-format

Content-Type: multipart/form-data

参数:

template: Word模板文件(.docx)

user_paper: 用户论文文件(.docx)

### 响应示例
json

{

"template": [

{

"index": 0,

"text_preview": "摘要 本文提出了一种...",

"font_name": "黑体",

"font_size_pt": 16,

"alignment": "居中",

"line_spacing_pt": 28.35

}

],

"user_paper": [...],

"status": "success"

}

## 🚀 部署指南

### Railway部署（推荐）
1. Fork本仓库
2. 在[Railway](https://railway.app)创建项目
3. 连接GitHub仓库
4. 自动部署完成

### 本地运行
bash

pip install -r requirements.txt

python app.py

## 🔌 Coze集成

在Coze中创建自定义插件：
- URL: `你的域名/extract-format`
- Method: POST
- 参数: template(file), user_paper(file)

## 📄 许可证

MIT License
