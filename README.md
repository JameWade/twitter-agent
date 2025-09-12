# Twitter Agent - 智能推特机器人

模拟真实用户行为的智能Twitter机器人，像人一样使用Twitter：发推、回复、互动。

## 功能特性

### 🤖 核心功能
- **智能发推**：基于Monad数据生成专业推文
- **自动回复**：智能时间线监听和评论回复
- **真实行为**：模拟真实用户的使用习惯

### 🎯 智能特性
- AI内容生成（基于Gemini AI）
- 智能时间线监控
- 自动垃圾内容过滤
- 人性化活动间隔
- 真实用户行为模拟

## 文件结构

### 核心模块
- **`twitter_agent.py`** - 主程序，整合所有功能
- **`twitter_client.py`** - Twitter客户端统一管理
- **`research_module.py`** - 数据收集模块
- **`analysis_module.py`** - AI分析模块
- **`publish_module.py`** - 推文发布模块
- **`timeline_monitor.py`** - 时间线监控模块

### 启动脚本
- **`run_twitter_agent.py`** - 主启动脚本（推荐使用）

### 配置文件
- **`cookies.txt`** - Twitter账号信息（必须配置）
- **`monad_config.json`** - 项目配置
- **`requirements.txt`** - Python依赖包

### 输出文件
- **`posted_tweets.txt`** - 已发布推文记录
- **`commented_tweets.txt`** - 已评论推文记录
- **`tuiwen.txt`** - 生成的推文内容

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 创建必要文件

#### 方式1：使用环境变量（推荐）
1. 复制环境变量模板文件：
```bash
cp env_example.txt .env
```

2. 编辑 `.env` 文件，填入你的配置：
```
TWITTER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
TWITTER_AUTHORIZATION=Bearer YOUR_BEARER_TOKEN
TWITTER_COOKIE=YOUR_TWITTER_COOKIES
TWITTER_PROXY=socks5://proxy_if_needed
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

#### 方式2：使用配置文件
创建 `cookies.txt` 文件：
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Authorization: Bearer YOUR_BEARER_TOKEN
Cookie: YOUR_TWITTER_COOKIES
Proxy: socks5://proxy_if_needed
```

### 3. 获取Twitter账号信息
1. 登录你的Twitter账号
2. 打开浏览器开发者工具 (F12)
3. 切换到 Network 标签页
4. 刷新页面，找到任意一个请求
5. 复制请求头中的 `Authorization` 和 `Cookie` 值
6. 将值填入上述配置文件中

### 4. 获取Gemini API密钥
1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 创建新的API密钥
3. 将密钥填入环境变量或代码中

### 3. 运行程序

#### 启动程序
```bash
python run_twitter_agent.py
```

#### 程序功能
- **自动发推**：基于Monad生态调研内容生成并发布推文
- **时间线监控**：监控关注用户的时间线，自动回复相关推文
- **智能分析**：使用AI分析推文内容，生成有意义的回复
- **人性化行为**：模拟真实用户的使用习惯，避免被检测

#### 程序行为
- **发推频率**：每10-15分钟随机检查一次，50%概率发推
- **监控频率**：每1-3分钟检查一次时间线
- **发推间隔**：至少间隔1分钟才会发新推文
- **内容来源**：主要基于Twitter上的Monad相关讨论

#### 停止程序
按 `Ctrl+C` 停止程序运行

#### 输出文件
程序运行时会生成以下文件：
- `tuiwen.txt` - 记录所有发布的推文
- `commented_tweets.txt` - 记录所有回复的推文ID

## 使用说明

### 真实用户行为模拟
- **智能发推**：随机发推，基于Monad数据生成内容
- **自动回复**：定期检查时间线，智能回复相关推文
- **人性化间隔**：模拟真实用户的活动频率和习惯
- **智能决策**：根据时间、内容等因素决定是否发推或回复

### 工作流程
1. **初始化**：加载Twitter客户端和AI模型
2. **持续运行**：像真实用户一样持续使用Twitter
3. **智能决策**：根据时间和活动历史决定下一步行动
4. **内容生成**：使用AI生成高质量的推文内容
5. **自动互动**：智能回复和评论其他用户的推文

## 配置说明

- **AI模型**：Google Gemini 2.0 Flash
- **推文长度**：150-250字符
- **发帖间隔**：至少3分钟，随机决定
- **时间线检查**：每3-10分钟随机检查
- **评论策略**：智能过滤，人性化回复

## 注意事项

1. 必须正确配置 `cookies.txt` 中的Twitter账号信息
2. 首次使用建议先测试单次发推
3. 长期运行需要稳定的网络环境
4. 遵守Twitter使用规则，避免频繁操作
5. 建议使用代理服务器提高稳定性

## 技术架构

- **异步编程**：使用asyncio提高性能
- **模块化设计**：各功能独立，易于维护
- **统一管理**：客户端和配置统一管理
- **错误处理**：完善的异常处理机制
- **资源管理**：自动清理和资源释放
