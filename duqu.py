import yaml
with open('setting.yaml', 'r', encoding='utf-8') as f:
    settings = yaml.safe_load(f)

username = settings.get('账号')
password = settings.get('密码')
clash_path = settings.get('clash路径')
print(username, password, clash_path)