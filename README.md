# 校园网自动连接系统使用说明

## 说明

   有时候把电脑挂在宿舍校园网过一段时间会自动断开，这个程序会每隔一段时间自动检测校园网的连接状态然后进行连接，使用异步等待的逻辑，不回占用太多资源，不想要logging可以ctrl+d logging然后把所有日志逻辑删除。

## 安装配置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置参数
编辑`setting.yaml`进行配置：

```yaml
# 配置信息 - 请修改为你的实际信息
校园网账号: "账号"           # 你的校园网账号
校园网密码: "密码"           # 你的校园网密码
clash路径: r"C:\Program Files\Clash Verge\clash-verge.exe"  # Clash安装路径
clash进程名称: ['clash-verge.exe']      # clash客户端名称
检测间隔: 600
```

### 3. 运行程序
```bash
python login.py
```

## 使用场景

### 场景1：有Clash工具的用户
1. 配置好用户名密码和Clash路径
2. 运行程序后会：
   - 每10分钟检测网络
   - 发现断网时自动关闭Clash
   - 执行校园网登录
   - 登录成功后重启Clash

### 场景2：没有Clash工具的用户
1. 设置`clash_path: None`
2. 程序会：
   - 每10分钟检测网络
   - 发现断网时直接执行校园网登录
   - 无需处理Clash相关操作

## 日志查看

程序运行时会显示详细的日志信息，包括：
- 网络检测状态
- Clash进程管理
- 登录过程和结果
- IP地址信息
- 错误信息和恢复情况

## 上游代码库

[WHUT-WLAN](https://github.com/FeliksLv01/WHUT-WLAN.git)
