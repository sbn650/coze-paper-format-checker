from flask import Flask, request, jsonify
from docx import Document
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_paragraph_formatting(doc_path):
    """
    提取Word文档段落格式信息
    返回结构化数据
    """
    try:
        doc = Document(doc_path)
    except Exception as e:
        raise ValueError(f"Word文件读取失败: {str(e)}")

    paragraphs = []
    
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        
        # 跳过空段落
        if not text:
            continue

        # 获取字体信息（处理多个run的情况）
        font_info = {
            "font_name": "默认",
            "font_size_pt": None,
            "is_bold": False,
            "is_italic": False
        }
        
        if para.runs:
            # 优先使用第一个非空run的字体
            main_run = None
            for run in para.runs:
                if run.text.strip():
                    main_run = run
                    break
            
            if main_run:
                font = main_run.font
                font_info.update({
                    "font_name": font.name or "默认",
                    "font_size_pt": round(font.size.pt, 1) if font.size else None,
                    "is_bold": bool(main_run.bold),
                    "is_italic": bool(main_run.italic)
                })

        # 对齐方式映射
        align_map = {
            0: "左对齐",
            1: "居中", 
            2: "右对齐",
            3: "两端对齐",
            4: "分散对齐"
        }
        alignment = align_map.get(para.alignment, "未知")

        # 行距提取（转换为磅）
        line_spacing = None
        try:
            p_pr = para._p.get_or_add_pPr()
            spacing = p_pr.spacing_line
            if spacing is not None and spacing.val is not None:
                # 缇(twips)转磅(points): 1磅 = 20缇
                line_spacing = round(spacing.val / 20.0, 2)
        except Exception as e:
            print(f"行距提取失败: {e}")

        # 首行缩进（厘米）
        first_line_indent = None
        try:
            if para.first_line_indent:
                first_line_indent = round(para.first_line_indent.cm, 2)
        except:
            pass

        # 段前段后间距
        space_before = None
        space_after = None
        try:
            if para.paragraph_format.space_before:
                space_before = round(para.paragraph_format.space_before.pt, 2)
            if para.paragraph_format.space_after:
                space_after = round(para.paragraph_format.space_after.pt, 2)
        except:
            pass

        paragraphs.append({
            "index": i,
            "text_preview": text[:80] + ("..." if len(text) > 80 else ""),
            "full_text": text,
            "font_name": font_info["font_name"],
            "font_size_pt": font_info["font_size_pt"],
            "is_bold": font_info["is_bold"],
            "is_italic": font_info["is_italic"],
            "alignment": alignment,
            "line_spacing_pt": line_spacing,
            "first_line_indent_cm": first_line_indent,
            "space_before_pt": space_before,
            "space_after_pt": space_after
        })

    return paragraphs

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy", "service": "paper-format-extractor"})

@app.route('/extract-format', methods=['POST'])
def extract_format():
    """
    主要接口：提取两个Word文档的格式信息
    """
    try:
        # 检查必需的文件
        if 'template' not in request.files or 'user_paper' not in request.files:
            return jsonify({
                "error": "缺少必需文件",
                "message": "请同时上传 'template' 和 'user_paper' 文件",
                "status": "failed"
            }), 400

        template_file = request.files['template']
        user_file = request.files['user_paper']

        # 验证文件
        if template_file.filename == '' or user_file.filename == '':
            return jsonify({
                "error": "文件名为空",
                "status": "failed"
            }), 400

        if not (allowed_file(template_file.filename) and allowed_file(user_file.filename)):
            return jsonify({
                "error": "文件格式错误",
                "message": "仅支持 .docx 格式文件",
                "status": "failed"
            }), 400

        # 生成安全的文件名
        template_filename = secure_filename(template_file.filename)
        user_filename = secure_filename(user_file.filename)
        
        uid = str(uuid.uuid4())[:8]
        template_path = os.path.join(UPLOAD_FOLDER, f"template_{uid}_{template_filename}")
        user_path = os.path.join(UPLOAD_FOLDER, f"user_{uid}_{user_filename}")

        # 保存文件
        template_file.save(template_path)
        user_file.save(user_path)

        print(f"文件保存成功: {template_path}, {user_path}")

        # 提取格式信息
        template_data = extract_paragraph_formatting(template_path)
        user_data = extract_paragraph_formatting(user_path)

        # 清理临时文件（可选，生产环境建议启用）
        # os.remove(template_path)
        # os.remove(user_path)

        # 返回结果
        return jsonify({
            "template": template_data,
            "user_paper": user_data,
            "stats": {
                "template_paragraphs": len(template_data),
                "user_paragraphs": len(user_data),
                "template_filename": template_filename,
                "user_filename": user_filename
            },
            "status": "success",
            "message": "格式提取完成"
        })

    except ValueError as ve:
        return jsonify({
            "error": str(ve),
            "status": "failed"
        }), 400
    except Exception as e:
        print(f"服务器错误: {str(e)}")
        return jsonify({
            "error": "服务器内部错误",
            "details": str(e),
            "status": "failed"
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "error": "文件过大",
        "message": f"文件大小不能超过 {MAX_FILE_SIZE // (1024 * 1024)}MB",
        "status": "failed"
    }), 413

if __name__ == '__main__':
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)