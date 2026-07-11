# 项目协作规范

## Git 提交信息

- 所有 Git commit message 必须使用中文描述。
- 提交信息格式必须为：`类型(内容): [emoji] 描述`。
- 必须根据改动性质选择合适的 Emoji，并将其放在冒号后的描述开头。
- `类型` 使用专业的 Conventional Commits 类型，例如 `feat`、`fix`、`docs`、`refactor`、`test`、`chore`。
- `内容` 应简洁说明主要改动范围，例如模块名、功能名或文件名。
- 提交信息保持单行，描述应准确、简洁。

示例：

```text
feat(ocr): 👏 新增验证码识别功能
fix(login): 🐛 修复登录票据跳转失败问题
docs(readme): 📝 更新部署说明
```
