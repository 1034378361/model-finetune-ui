# 双加密格式支持 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在加密模式中支持两种BIN文件格式——AES加密（默认，当前已有）和十六进制混淆（大华兼容），用户通过UI选择；解密模式自动检测格式。

**Architecture:** 在 `EncryptionManager` 和 `DecryptionManager` 中各新增 hex-reverse 方法。UI侧边栏加密模式下新增 radio 选择加密方式，选择结果透传到加密调用。解密时通过文件内容特征自动判断格式。

**Tech Stack:** Python, Streamlit, cryptography (已有)

---

### Task 1: 加密模块 — 新增十六进制混淆加密方法

**Files:**
- Modify: `src/model_finetune_ui/utils/encryption.py`

**Step 1: 在 `EncryptionManager` 类中新增 `encryption_method` 属性**

在 `__init__` 中添加 `self.encryption_method = "aes"`，并在 `encrypt_and_save` 中根据该属性分发到不同加密路径。

**Step 2: 新增 `_hex_reverse_encrypt` 方法**

```python
def _hex_reverse_encrypt(self, model_result: dict[str, Any], output_dir: str) -> str | None:
    """使用十六进制倒序混淆方式保存数据（大华兼容格式）"""
    try:
        import json
        from datetime import datetime
        from pathlib import Path

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"ui_run_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)

        data_json = json.dumps(model_result, ensure_ascii=False)
        hex_string = data_json.encode("utf-8").hex()
        reversed_hex = hex_string[::-1]

        file_path = output_path / f"encrypted_result_{timestamp}.bin"
        with open(file_path, "wb") as f:
            f.write(reversed_hex.encode("utf-8"))

        logger.info(f"模型已保存（十六进制混淆格式）: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"十六进制混淆保存失败: {str(e)}")
        return None
```

**Step 3: 修改 `encrypt_and_save` 方法，根据 `encryption_method` 分发**

在现有 `encrypt_and_save` 方法中，验证通过后判断：
- `self.encryption_method == "hex_reverse"` → 调用 `_hex_reverse_encrypt`
- 否则 → 走现有 AES 加密路径

**Step 4: 运行现有加密相关测试确认无回归**

Run: `uv run pytest tests/ -v -k "encrypt or processor" --tb=short`
Expected: 全部 PASS（现有行为不变）

**Step 5: Commit**

```bash
git add src/model_finetune_ui/utils/encryption.py
git commit -m "feat: add hex-reverse obfuscation encryption method"
```

---

### Task 2: 解密模块 — 新增十六进制混淆解密 + 自动格式检测

**Files:**
- Modify: `src/model_finetune_ui/utils/decryption.py`

**Step 1: 新增 `_detect_bin_format` 静态方法**

检测逻辑：读取文件前 64 字节，尝试 UTF-8 解码，检查是否全为十六进制字符 `[0-9a-fA-F]`。
- 是 → `"hex_reverse"` 格式
- 否 → `"aes"` 格式

```python
@staticmethod
def _detect_bin_format(file_data: bytes) -> str:
    """检测BIN文件格式"""
    try:
        sample = file_data[:64].decode("utf-8")
        if all(c in "0123456789abcdefABCDEF" for c in sample):
            return "hex_reverse"
    except (UnicodeDecodeError, ValueError):
        pass
    return "aes"
```

**Step 2: 新增 `_decrypt_hex_reverse` 方法**

```python
def _decrypt_hex_reverse(self, file_data: bytes) -> dict[str, Any] | None:
    """解密十六进制倒序混淆格式的BIN文件"""
    try:
        reversed_hex = file_data.decode("utf-8")
        hex_string = reversed_hex[::-1]
        data_json = bytes.fromhex(hex_string).decode("utf-8")
        result = json.loads(data_json)
        logger.info("✅ 十六进制混淆格式解密成功")
        return result
    except Exception as e:
        logger.error(f"❌ 十六进制混淆解密失败: {str(e)}")
        return None
```

**Step 3: 修改 `decrypt_bin_file` 方法，在读取文件后先检测格式**

在步骤2（读取文件）之后，调用 `_detect_bin_format(file_data)`：
- `"hex_reverse"` → 调用 `_decrypt_hex_reverse(file_data)`
- `"aes"` → 走现有 AES 解密路径

**Step 4: 运行现有解密相关测试确认无回归**

Run: `uv run pytest tests/ -v -k "decrypt" --tb=short`
Expected: 全部 PASS

**Step 5: Commit**

```bash
git add src/model_finetune_ui/utils/decryption.py
git commit -m "feat: add hex-reverse decryption with auto-format detection"
```

---

### Task 3: UI — 侧边栏新增加密方式选择

**Files:**
- Modify: `src/model_finetune_ui/app.py`

**Step 1: 修改 `render_sidebar`，在加密模式下新增 radio 选择**

在 `output_dir` 输入框之后、`st.markdown("---")` 之前，添加：

```python
encryption_method = st.radio(
    "加密方式",
    options=["aes", "hex_reverse"],
    format_func=lambda x: "🔐 AES加密（默认）" if x == "aes" else "🔀 十六进制混淆（大华兼容）",
    index=0,
    help="AES加密：安全性高，兼容C++端解密\n十六进制混淆：兼容大华系统",
)
```

**Step 2: 修改 `render_sidebar` 返回值**

从 `return app_mode, model_type, output_dir` 改为 `return app_mode, model_type, output_dir, encryption_method`。

解密模式下 `encryption_method = "aes"`（不影响解密，解密自动检测）。

**Step 3: 修改 `run` 方法接收新返回值**

```python
app_mode, model_type, output_dir, encryption_method = self.render_sidebar()
```

传递给 `render_encrypt_mode(model_type, output_dir, encryption_method)`。

**Step 4: 修改 `render_encrypt_mode` 签名和调用链**

```python
def render_encrypt_mode(self, model_type, output_dir, encryption_method="aes"):
```

在调用 `process_uploaded_files` 前设置：
```python
self.encryptor.encryption_method = encryption_method
```

**Step 5: Commit**

```bash
git add src/model_finetune_ui/app.py
git commit -m "feat: add encryption method selector in sidebar UI"
```

---

### Task 4: 单元测试 — 十六进制混淆加密/解密

**Files:**
- Create: `tests/unit/test_hex_reverse.py`

**Step 1: 编写加密测试**

```python
"""十六进制混淆加密/解密单元测试"""

import json
import os

import pytest

from src.model_finetune_ui.utils.encryption import EncryptionManager
from src.model_finetune_ui.utils.decryption import DecryptionManager


class TestHexReverseEncryption:
    """十六进制混淆加密测试"""

    def test_hex_reverse_encrypt_type_0(self, temp_dir):
        """测试Type 0数据的十六进制混淆加密"""
        encryptor = EncryptionManager()
        encryptor.encryption_method = "hex_reverse"

        model_result = {
            "type": 0,
            "A": [-1.0] * 11,
            "Range": [0.0, 10.0] * 11,
        }

        result_path = encryptor.encrypt_and_save(model_result, str(temp_dir))
        assert result_path is not None
        assert os.path.exists(result_path)

        # 验证文件内容是纯十六进制文本
        with open(result_path, "rb") as f:
            content = f.read().decode("utf-8")
        assert all(c in "0123456789abcdef" for c in content)

    def test_hex_reverse_encrypt_type_1(self, temp_dir):
        """测试Type 1数据的十六进制混淆加密"""
        encryptor = EncryptionManager()
        encryptor.encryption_method = "hex_reverse"

        model_result = {
            "type": 1,
            "w": [0.1] * (26 * 11),
            "a": [0.2] * (26 * 11),
            "b": [0.3] * (11 * 26),
            "A": [-1.0] * 11,
            "Range": [0.0, 10.0] * 11,
        }

        result_path = encryptor.encrypt_and_save(model_result, str(temp_dir))
        assert result_path is not None

    def test_default_encryption_method_is_aes(self):
        """测试默认加密方式为AES"""
        encryptor = EncryptionManager()
        assert encryptor.encryption_method == "aes"
```

**Step 2: 编写解密测试**

```python
class TestHexReverseDecryption:
    """十六进制混淆解密测试"""

    def test_detect_hex_reverse_format(self):
        """测试格式检测 - 十六进制混淆"""
        hex_data = "abcdef0123456789" * 10
        result = DecryptionManager._detect_bin_format(hex_data.encode("utf-8"))
        assert result == "hex_reverse"

    def test_detect_aes_format(self):
        """测试格式检测 - AES"""
        binary_data = b"\x00\x01\x02\xff" * 16
        result = DecryptionManager._detect_bin_format(binary_data)
        assert result == "aes"

    def test_decrypt_hex_reverse_file(self, temp_dir):
        """测试解密十六进制混淆文件"""
        decryptor = DecryptionManager()

        # 手动创建一个hex-reverse格式的文件
        original_data = {
            "type": 0,
            "A": [-1.0] * 11,
            "Range": [0.0, 10.0] * 11,
        }
        data_json = json.dumps(original_data, ensure_ascii=False)
        hex_string = data_json.encode("utf-8").hex()
        reversed_hex = hex_string[::-1]

        test_file = temp_dir / "test_hex.bin"
        with open(test_file, "wb") as f:
            f.write(reversed_hex.encode("utf-8"))

        result = decryptor.decrypt_bin_file(str(test_file))
        assert result is not None
        assert result["type"] == 0
        assert result["A"] == [-1.0] * 11
```

**Step 3: 运行测试**

Run: `uv run pytest tests/unit/test_hex_reverse.py -v`
Expected: 全部 PASS

**Step 4: Commit**

```bash
git add tests/unit/test_hex_reverse.py
git commit -m "test: add hex-reverse encryption/decryption unit tests"
```

---

### Task 5: 集成测试 — 加密→解密往返验证

**Files:**
- Modify: `tests/integration/test_decrypt_workflow.py`

**Step 1: 新增往返测试**

在 `TestDecryptWorkflow` 类中添加：

```python
def test_hex_reverse_roundtrip(self, temp_dir):
    """测试十六进制混淆格式的加密→解密往返"""
    from src.model_finetune_ui.utils.encryption import EncryptionManager

    # 加密
    encryptor = EncryptionManager()
    encryptor.encryption_method = "hex_reverse"

    original = {
        "type": 0,
        "A": [-1.0, 0.5, 1.2, -0.3, 0.8, 1.5, -0.7, 0.9, 1.1, -0.4, 1.3],
        "Range": [0.5, 10.5, 2.0, 15.0, 1.0, 8.0, 3.0, 20.0, 0.8, 12.0,
                  2.5, 18.0, 1.5, 9.0, 4.0, 25.0, 0.3, 6.0, 3.5, 22.0, 1.8, 14.0],
    }

    encrypted_path = encryptor.encrypt_and_save(original, str(temp_dir))
    assert encrypted_path is not None

    # 解密（自动检测格式）
    decryptor = DecryptionManager()
    decrypted = decryptor.decrypt_bin_file(encrypted_path)

    assert decrypted is not None
    assert decrypted["type"] == original["type"]
    assert decrypted["A"] == original["A"]
    assert decrypted["Range"] == original["Range"]
```

**Step 2: 运行集成测试**

Run: `uv run pytest tests/integration/test_decrypt_workflow.py -v`
Expected: 全部 PASS

**Step 3: Commit**

```bash
git add tests/integration/test_decrypt_workflow.py
git commit -m "test: add hex-reverse roundtrip integration test"
```

---

### Task 6: 全量测试 + 最终验证

**Step 1: 运行全部测试**

Run: `uv run pytest -v`
Expected: 全部 PASS

**Step 2: 运行 lint**

Run: `uv run ruff check .`
Expected: 无错误

**Step 3: 最终 commit（如有遗漏修复）**

```bash
git add -A
git commit -m "chore: fix lint issues from dual encryption feature"
```
