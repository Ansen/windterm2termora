import json
import uuid
import time

windTerm_session_file = 'user.sessions'
termora_expoter_file = 'Termora.json'

# windterm user.sessions 文件并不存放密码,
default_ssh_password = ""

# windterm identityFilePath 与 termora 密钥管理器中的 ID 的映射
# termora 密钥管理器中的 ID 从导出的 Termora.json 中获取
public_key_map = {
    "windterm_identityFilePath": "termora_keyPairs_id"
}
# termora 密钥管理器中的 ID, 未从在 public_key_map 中匹配上时使用
default_ssh_key_id = ""

# --- 不要动
# 目录名和uuid映射关系
group_map = {}
# 存储目录之间父与子关系, 带UUID
group_uuid_map = {}

def get_uuid():
    return uuid.uuid4().hex


def load_config_file(file: str):
    with open(file=file, mode='r', encoding="utf-8") as f:
        data = f.read()
    return data

def write_file(file, data):
    with open(file=file, mode="w", encoding="utf8") as f:
        f.write(data)

def get_group_name_uuid(name: str) -> str:
    _group_name = name.split(">")
    _group_name = _group_name[-1]

    return group_uuid_map.get(_group_name, "")

def build_group_map_from_windterm(sessions: list):
    for s in sessions:
        _group = s.get("session.group", None)
        if _group:
            # 使用 '>' 分隔符分割字符串
            groups = _group.split('>')
            for i in range(0, len(groups)):
                _group = groups[i]
                if not group_uuid_map.get(_group, False):
                    _uuid = get_uuid()
                    group_uuid_map[_group] = _uuid
                    if i > 0:
                        group_map[_group] = {
                            "uuid":_uuid,
                            "parentId": group_uuid_map.get(groups[i-1], "") 
                        }
                    else:
                        group_map[_group]= {
                            "uuid":_uuid,
                            "parentId":"" 
                        }
                        


def convert_to_termora_host(data: dict, offset: int) -> dict:
    unix_timestamp_ms = int(time.time() * 1000) + offset

    _identityFile = data.get("ssh.identityFilePath", "")
    _identityFileWindows = data.get("ssh.identityFilePath.windows", "")
    if _identityFile != "":
        auth_type = "PublicKey"
        auth_pwd = public_key_map.get(_identityFile, default_ssh_key_id)
    elif _identityFileWindows != "":
        auth_type = "PublicKey"
        auth_pwd = public_key_map.get(_identityFileWindows, default_ssh_key_id)
    else:
        auth_type = "Password"
        auth_pwd = default_ssh_password

    _target = data["session.target"]
    _target = _target.split('@')
    _ssh_user = _target[0]
    _ssh_host = _target[-1]
    _host_info = {
            "id": data["session.uuid"].replace("-", ""),
            "name": data["session.label"],
            "protocol": data["session.protocol"],
            "host": _ssh_host,
            "port": data["session.port"],
            "username": _ssh_user,
            "authentication": {
                "type": auth_type,
                "password": auth_pwd
            },
            "sort": unix_timestamp_ms,
            "createDate": unix_timestamp_ms,
            "updateDate": unix_timestamp_ms
        }

    if data["session.group"] != "":
        _host_info["parentId"] = get_group_name_uuid(name=data["session.group"])
    
    return _host_info

def main():
    windTerm_session = load_config_file(file=windTerm_session_file)
    windTerm_session = json.loads(windTerm_session)

    # 将 windterm 的分组转换成 termora 格式
    build_group_map_from_windterm(sessions=windTerm_session)

    # 将 windterm 的主机转换成 termora 格式
    _hosts = []
    _offset = 0
    for s in windTerm_session:
        _h = convert_to_termora_host(data=s, offset=_offset)
        _hosts.append(_h)
    
    # 生成 termora 的目录层级数据
    termora_groups = []
    _offset = 0
    for x in group_map:
        _unix_timestamp_ms = int(time.time() * 1000) + _offset
        _id = group_map[x].get("uuid", "")

        _g = {
            "id": _id,
            "name": x,
            "protocol": "Folder",
            "sort": _unix_timestamp_ms,
            "createDate": _unix_timestamp_ms,
            "updateDate": _unix_timestamp_ms
        }
        _p_id = group_map[x].get("parentId", "")
        if _p_id != "":
            _g["parentId"] = _p_id
        termora_groups.append(_g)
        _offset +=1

    # write_file(file="group_map.json", data=json.dumps(termora_groups, indent=4))

    termora_expoter = load_config_file(file=termora_expoter_file)
    termora_expoter = json.loads(termora_expoter)
    termora_groups.extend(_hosts)
    termora_expoter["hosts"] = termora_groups
    write_file(file="test.json", data=json.dumps(termora_expoter, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()