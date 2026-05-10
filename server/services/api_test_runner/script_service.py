import json
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScriptResult:
    """脚本执行结果"""
    success: bool = True
    output: list[str] = field(default_factory=list)
    error: str | None = None
    variables: dict[str, str] = field(default_factory=dict)


class ScriptService:
    """JS脚本执行服务（PyMiniRacer沙箱）"""

    TIMEOUT = 5  # 秒

    def execute(self, script: str, context: dict[str, Any]) -> ScriptResult:
        """
        执行JS脚本
        context: {"variables": {...}, "response": {...}, "request": {...}}
        """
        if not script or not script.strip():
            return ScriptResult()

        result = ScriptResult()
        logs: list[str] = []
        variables = dict(context.get("variables", {}))

        try:
            from py_mini_racer import MiniRacer
        except ImportError:
            result.success = False
            result.error = "py-mini-racer 未安装，无法执行JS脚本"
            return result

        ctx = MiniRacer()

        # 注入 tf 对象
        tf_js = f"""
        var tf = {{
            variables: {json.dumps(variables, ensure_ascii=False)},
            getVariable: function(name) {{ return this.variables[name] || null; }},
            setVariable: function(name, value) {{ this.variables[name] = String(value); }},
            log: function(msg) {{ _logs.push(String(msg)); }}
        }};
        var _logs = [];
        var request = {json.dumps(context.get("request", {}), ensure_ascii=False)};
        var response = {json.dumps(context.get("response", {}), ensure_ascii=False)};
        """
        ctx.eval(tf_js)

        # 带超时执行
        execution_error = None

        def run():
            nonlocal execution_error
            try:
                ctx.eval(script)
            except Exception as e:
                execution_error = str(e)

        thread = threading.Thread(target=run)
        thread.start()
        thread.join(timeout=self.TIMEOUT)

        if thread.is_alive():
            result.success = False
            result.error = f"脚本执行超时（{self.TIMEOUT}秒）"
            return result

        if execution_error:
            result.success = False
            result.error = execution_error
            return result

        # 读取日志
        try:
            logs_result = ctx.eval("JSON.stringify(_logs)")
            if logs_result:
                result.output = json.loads(logs_result)
        except Exception:
            pass

        # 读取更新后的变量
        try:
            vars_result = ctx.eval("JSON.stringify(tf.variables)")
            if vars_result:
                result.variables = json.loads(vars_result)
        except Exception:
            pass

        return result
