#  Convert WindTerm user sessions to Termora

将 WindTerm 的 user.sessions 文件转换成 Termora 可导入的文件

## Usage

> WindTerm 的数据目录在: Session - Perferences - Profiles Directiory 
>  user.sessions 文件在: `.wind/profiles/default.v10/terminal` 目录中
> Termora 的 `导入` `导出` 在 `设置` - `同步` 中

1. 将 WindTerm 中用到的私钥导入到 Termora 中
2. 克隆本项目 `git clone https://github.com/Ansen/windterm2termora.git`
2. 导出 Termora 的配置文件为 Termora.json, 并**复制**一份到项目目录
3. **复制** WindTerm 数据目录的 user.sessions 到项目目录
4. 确保 Termora.json、user.sessions、main.py 三个文件在同一个目录
5. 根据注释修改 main.py 文件中的三个参数：DEFAULT_SSH_PASSWORD、PUBLIC_KEY_MAP、DEFAULT_SSH_KEY_ID
6. 使用 `python3 main.py` 运行函数，会生成 test.json
7. 关闭 Termora， 备份数据文件
8. 将 test.json 文件导入 Termora 中即可



> 鉴于脚本非常简单，使用中有任何问题， 请先问 AI
> 实在解决不了再提 issue

## Thanks

- [termora](https://github.com/TermoraDev/termora)
- [deepseek](https://www.deepseek.com)
- [DuckDuckGoAi](https://Duck.ai)