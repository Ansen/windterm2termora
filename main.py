import json
import uuid
import time
from typing import Dict, List

# 常量定义
WINDTTERM_SESSION_FILE = 'user.sessions'
TERMORA_EXPORTER_FILE = 'Termora.json'

# windterm user.sessions 文件并不存放密码, 这里设置一个默认密码，可为空
DEFAULT_SSH_PASSWORD = ""

# windterm identityFilePath 与 termora 密钥管理器中的 ID 的映射
# termora 密钥管理器中的 ID 从导出的 Termora.json 中获取
PUBLIC_KEY_MAP = {
    "windterm_identityFilePath": "termora_keyPairs_id"
}
# termora 密钥管理器中的 ID, 未从在 PUBLIC_KEY_MAP 中匹配上时使用
DEFAULT_SSH_KEY_ID = ""

# 不要动
GroupInfo = Dict[str, str]
SessionData = Dict[str, str]

def generate_uuid() -> str:
    """生成不带连字符的UUID"""
    return uuid.uuid4().hex

def load_json_file(file_path: str) -> dict:
    """加载并解析JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error loading {file_path}: {str(e)}")

def save_json_file(data: dict, file_path: str) -> None:
    """保存数据到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        raise RuntimeError(f"Error saving {file_path}: {str(e)}")

class GroupManager:
    """分组管理类"""
    def __init__(self):
        self.group_info: Dict[str, GroupInfo] = {}
        self.name_to_uuid: Dict[str, str] = {}

    def process_session_groups(self, sessions: List[SessionData]) -> None:
        """处理所有会话的分组结构"""
        for session in sessions:
            group_path = session.get("session.group", "")
            if not group_path:
                continue
            
            hierarchy = group_path.split('>')
            parent_uuid = ""
            
            for level, group_name in enumerate(hierarchy):
                if group_name not in self.name_to_uuid:
                    new_uuid = generate_uuid()
                    self.name_to_uuid[group_name] = new_uuid
                    self.group_info[group_name] = {
                        "uuid": new_uuid,
                        "parentId": parent_uuid
                    }
                parent_uuid = self.name_to_uuid[group_name]

def convert_session_to_host(session: SessionData, sort_timestamp: int) -> dict:
    """转换单个会话到Termora主机格式"""
    target_parts = session["session.target"].split('@')
    ssh_user = target_parts[0]
    ssh_host = target_parts[-1] if len(target_parts) > 1 else ""

    # 处理认证信息
    identity_keys = session.get("ssh.identityFilePath") or session.get("ssh.identityFilePath.windows") or ""
    auth_type = "PublicKey" if identity_keys else "Password"
    auth_value = PUBLIC_KEY_MAP.get(identity_keys, DEFAULT_SSH_KEY_ID) if auth_type == "PublicKey" else DEFAULT_SSH_PASSWORD

    host_data = {
        "id": session["session.uuid"].replace("-", ""),
        "name": session["session.label"],
        "protocol": session["session.protocol"],
        "host": ssh_host,
        "port": session["session.port"],
        "username": ssh_user,
        "authentication": {
            "type": auth_type,
            "password": auth_value
        },
        "sort": sort_timestamp,
        "createDate": sort_timestamp,
        "updateDate": sort_timestamp
    }

    if group_path := session.get("session.group"):
        group_name = group_path.split('>')[-1]
        host_data["parentId"] = GroupManager().name_to_uuid.get(group_name, "")

    return host_data

def main():
    try:
        # 初始化数据
        windterm_sessions = load_json_file(WINDTTERM_SESSION_FILE)
        termora_template = load_json_file(TERMORA_EXPORTER_FILE)
        
        # 处理分组
        group_manager = GroupManager()
        group_manager.process_session_groups(windterm_sessions)
        
        base_timestamp = int(time.time() * 1000)
        
        # 生成分组数据
        termora_groups = []
        for index, (group_name, info) in enumerate(group_manager.group_info.items()):
            termora_groups.append({
                "id": info["uuid"],
                "name": group_name,
                "protocol": "Folder",
                "sort": base_timestamp + index,
                "createDate": base_timestamp + index,
                "updateDate": base_timestamp + index,
                "parentId": info["parentId"]
            })
        
        # 生成主机数据
        host_records = []
        group_count = len(group_manager.group_info)
        for index, session in enumerate(windterm_sessions):
            sort_ts = base_timestamp + group_count + index
            host_records.append(convert_session_to_host(session, sort_ts))
        
        # 合并数据并保存
        termora_template["hosts"] = termora_groups + host_records
        save_json_file(termora_template, "Termora_Export.json")
        
    except Exception as e:
        print(f"Conversion failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()