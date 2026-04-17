# 贡献指南

感谢您对月光宝盒项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 1. 报告问题
- 在 Issues 页面提交 bug 报告或功能建议
- 请提供详细的问题描述、复现步骤和环境信息
- 如果有错误日志，请一并提供

### 2. 提交代码
1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 提交更改：遵循 [Conventional Commits](https://www.conventionalcommits.org/)
4. 推送到分支：`git push origin feat/your-feature`
5. 创建 Pull Request

### 3. 编写文档
- 修正拼写错误
- 补充使用示例
- 翻译文档
- 添加教程

## 开发环境

### 后端环境
```bash
# 1. 克隆项目
git clone https://github.com/[your-username]/moonlight-box.git
cd moonlight-box

# 2. 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 3. 安装依赖
pip install -r backend/requirements.txt

# 4. 启动后端
uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 前端环境
```bash
# 前端使用 Vue 3 CDN + Element Plus
# 无需安装，直接在浏览器访问 http://127.0.0.1:8001
```

## 代码规范

### Python
- 遵循 PEP 8 规范
- 使用类型注解
- 添加适当的 docstring
- 函数长度不超过 50 行

### Git 提交
使用 Conventional Commits 格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型说明：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 测试

请确保代码有相应的测试：
```bash
# 运行测试
pytest tests/

# 检查覆盖率
pytest tests/ --cov=app --cov-report=term-missing
```

## Pull Request 流程

1. 确保代码通过所有测试
2. 更新相关文档
3. 提交清晰的自描述提交信息
4. 等待代码审查
5. 根据反馈修改

## 行为准则

请遵守以下行为准则：
- 尊重他人意见
- 建设性讨论
- 帮助新贡献者
- 遵守开源协议

## 联系方式

如有问题，可以通过以下方式联系：
- Issues: [GitHub Issues](https://github.com/chenzaichuang1011-sketch/moonlight-box/issues)
- 邮件: [请填写您的邮箱]

感谢您的贡献！🎉