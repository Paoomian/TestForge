import os
import json
from typing import Dict, Any, List


class DocumentParser:
    """文档解析器"""

    @staticmethod
    def parse_prd(file_path: str) -> Dict[str, Any]:
        """解析 PRD 文档

        支持格式：.docx, .pdf, .md

        Returns:
            {
                "title": "文档标题",
                "content": "文档内容（纯文本）",
                "sections": [{"title": "章节标题", "content": "章节内容"}]
            }
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.docx':
            return DocumentParser._parse_docx(file_path)
        elif ext == '.pdf':
            return DocumentParser._parse_pdf(file_path)
        elif ext == '.md':
            return DocumentParser._parse_markdown(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    @staticmethod
    def parse_swagger(file_path: str) -> Dict[str, Any]:
        """解析 Swagger/OpenAPI 文档

        支持格式：.json, .yaml

        Returns:
            {
                "info": {"title": "API 标题", "version": "版本", "description": "描述"},
                "endpoints": [{"path": "/api/users", "method": "GET", ...}]
            }
        """
        ext = os.path.splitext(file_path)[1].lower()

        with open(file_path, 'r', encoding='utf-8') as f:
            if ext == '.json':
                content = json.load(f)
            elif ext in ['.yaml', '.yml']:
                import yaml
                content = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的文件格式: {ext}")

        return DocumentParser._parse_swagger_content(content)

    @staticmethod
    def _parse_docx(file_path: str) -> Dict[str, Any]:
        """解析 Word 文档"""
        from docx import Document

        doc = Document(file_path)
        sections = []
        current_section = {"title": "", "content": ""}

        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                # 保存当前章节
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                # 开始新章节
                current_section = {
                    "title": para.text.strip(),
                    "content": ""
                }
            else:
                current_section["content"] += para.text + "\n"

        # 保存最后一个章节
        if current_section["content"].strip():
            sections.append(current_section)

        # 提取标题
        title = sections[0]["title"] if sections else os.path.basename(file_path)

        # 合并所有内容
        full_content = "\n\n".join([
            f"{s['title']}\n{s['content']}" if s['title'] else s['content']
            for s in sections
        ])

        return {
            "title": title,
            "content": full_content,
            "sections": sections
        }

    @staticmethod
    def _parse_pdf(file_path: str) -> Dict[str, Any]:
        """解析 PDF 文档"""
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        content = ""

        for page in reader.pages:
            content += page.extract_text() + "\n"

        return {
            "title": os.path.basename(file_path),
            "content": content.strip(),
            "sections": [{"title": "全文", "content": content.strip()}]
        }

    @staticmethod
    def _parse_markdown(file_path: str) -> Dict[str, Any]:
        """解析 Markdown 文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单按 # 标题分割
        sections = []
        current_section = {"title": "", "content": ""}

        for line in content.split('\n'):
            if line.startswith('# '):
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                current_section = {
                    "title": line[2:].strip(),
                    "content": ""
                }
            elif line.startswith('## '):
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                current_section = {
                    "title": line[3:].strip(),
                    "content": ""
                }
            else:
                current_section["content"] += line + "\n"

        if current_section["content"].strip():
            sections.append(current_section)

        title = sections[0]["title"] if sections else os.path.basename(file_path)

        return {
            "title": title,
            "content": content,
            "sections": sections
        }

    @staticmethod
    def _parse_swagger_content(content: Dict) -> Dict[str, Any]:
        """解析 Swagger 内容"""
        info = content.get('info', {})

        endpoints = []
        paths = content.get('paths', {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    # 提取参数
                    parameters = details.get('parameters', [])

                    # 提取请求体
                    request_body = details.get('requestBody', {})

                    # 提取响应
                    responses = details.get('responses', {})

                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': parameters,
                        'request_body': request_body,
                        'responses': responses,
                        'tags': details.get('tags', [])
                    }
                    endpoints.append(endpoint)

        return {
            'info': {
                'title': info.get('title', 'Unknown API'),
                'version': info.get('version', '1.0.0'),
                'description': info.get('description', '')
            },
            'endpoints': endpoints
        }

    @staticmethod
    def format_swagger_for_prompt(swagger_data: Dict[str, Any]) -> str:
        """将 Swagger 数据格式化为适合 Prompt 的文本"""
        lines = []
        info = swagger_data.get('info', {})
        lines.append(f"API: {info.get('title', 'Unknown')}")
        lines.append(f"版本: {info.get('version', '1.0.0')}")
        if info.get('description'):
            lines.append(f"描述: {info['description']}")
        lines.append("")

        for endpoint in swagger_data.get('endpoints', []):
            lines.append(f"### {endpoint['method']} {endpoint['path']}")
            if endpoint.get('summary'):
                lines.append(f"说明: {endpoint['summary']}")
            if endpoint.get('description'):
                lines.append(f"描述: {endpoint['description']}")

            # 参数
            if endpoint.get('parameters'):
                lines.append("参数:")
                for param in endpoint['parameters']:
                    param_type = param.get('schema', {}).get('type', 'string')
                    required = '必填' if param.get('required') else '可选'
                    lines.append(f"  - {param.get('name', '')} ({param_type}, {required}): {param.get('description', '')}")

            # 请求体
            if endpoint.get('request_body'):
                rb = endpoint['request_body']
                if 'content' in rb:
                    for content_type, content_data in rb['content'].items():
                        lines.append(f"请求体 ({content_type}):")
                        if 'schema' in content_data:
                            lines.append(f"  Schema: {json.dumps(content_data['schema'], ensure_ascii=False, indent=2)}")

            # 响应
            if endpoint.get('responses'):
                lines.append("响应:")
                for status, resp in endpoint['responses'].items():
                    desc = resp.get('description', '')
                    lines.append(f"  - {status}: {desc}")

            lines.append("")

        return "\n".join(lines)
