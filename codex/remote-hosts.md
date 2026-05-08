# Remote Hosts Registry

## Purpose
- 本文件记录长期使用的远程主机稳定元数据，避免把 `user/port/key/path` 散落在聊天历史里。
- 每条记录都应与 `~/.ssh/config` 中的 SSH alias 一一对应。
- 本文件不保存密码、passphrase、token 或私钥内容。
- 使用本文件前，必须先遵循 `~/.codex/remote-access.md` 的远程访问流程规则。

## Required Fields
- `alias`
- `hostname`
- `user`
- `port`
- `identity_file`
- `jump_host`
- `default_workdir`
- `data_roots`
- `services`
- `verify_command`
- `notes`

## Template
- alias: `example-host`
- hostname: `203.0.113.10`
- user: `ubuntu`
- port: `22`
- identity_file: `~/.ssh/id_rsa`
- jump_host: ``
- default_workdir: `/home/ubuntu`
- data_roots:
  - `/data/example`
- services:
  - `ssh`: `ssh example-host`
  - `http_api`: `https://example.internal/api`
- verify_command: `ssh example-host 'echo ok && pwd'`
- notes:
  - `~/.ssh/config` 中必须存在同名 alias
  - 若私钥带 passphrase，会话开始前先执行一次 `ssh-add ~/.ssh/id_rsa`

## Known Hosts
- alias: `mevscan-source`
- hostname: `43.140.220.20`
- user: `ubuntu`
- port: `6039`
- identity_file: `~/.ssh/id_rsa`
- jump_host: ``
- default_workdir: `/home/ubuntu`
- data_roots:
  - `/mnt/data/mevscan/runtime-data`
  - `/mnt/data/mevscan/runtime-data/reviewMEVs`
  - `/mnt/data/mevscan/runtime-data/calculatePNL`
- services:
  - `ssh`: `ssh mevscan-source`
  - `review_root`: `/mnt/data/mevscan/runtime-data/reviewMEVs`
  - `pnl_root`: `/mnt/data/mevscan/runtime-data/calculatePNL`
- verify_command: `ssh mevscan-source 'echo ok && ls /mnt/data/mevscan/runtime-data | head'`
- notes:
  - 原始源目录优先检查 `reviewMEVs/YYYYMMDD` 与 `calculatePNL/YYYYMMDD`
  - 若认证失败且 `ssh -vv mevscan-source` 显示 `Server accepts key`，先解锁 `~/.ssh/id_rsa`

- alias: `fp-remote`
- hostname: `170.106.67.239`
- user: `ubuntu`
- port: `22`
- identity_file: `~/.ssh/id_ed25519`
- jump_host: ``
- default_workdir: `/home/ubuntu/fp-detector`
- data_roots:
  - `/home/ubuntu/fp-detector`
  - `127.0.0.1:5432`
- services:
  - `ssh`: `ssh fp-remote`
  - `btp_parse_url`: `http://170.106.67.239:8444/v1/parse/tx`
  - `db_tunnel_alias`: `fp-remote-db-tunnel`
  - `db_remote_endpoint`: `127.0.0.1:5432`
  - `db_local_tunnel_endpoint`: `127.0.0.1:15432`
- verify_command: `ssh fp-remote 'echo ok && pwd && test -d /home/ubuntu/fp-detector && echo repo-ready'`
- notes:
  - `FP_BLOCKSEC_URL_TEMPLATE` 默认远端入口是 `http://170.106.67.239:8444/v1/parse/tx`
  - 远端 DB 访问优先通过 `ssh -N fp-remote-db-tunnel` 建本地 `15432 -> 127.0.0.1:5432` tunnel
  - 不在本文件保存 DB 用户名、密码或完整 DSN；凭据由 repo env 或本地 shell 提供
  - Top Union DB 场景仍优先使用仓库脚本 `scripts/run_top_union_ui_server.sh ensure`

- alias: `fp-remote-db-tunnel`
- hostname: `170.106.67.239`
- user: `ubuntu`
- port: `22`
- identity_file: `~/.ssh/id_ed25519`
- jump_host: ``
- default_workdir: `/home/ubuntu`
- data_roots:
  - `127.0.0.1:15432`
  - `127.0.0.1:5432`
- services:
  - `ssh`: `ssh -N fp-remote-db-tunnel`
  - `local_forward`: `127.0.0.1:15432 -> 127.0.0.1:5432`
  - `db_probe`: `psql 'postgresql://asf:asf@127.0.0.1:15432/asf' -c 'select 1'`
- verify_command: `ssh -N fp-remote-db-tunnel`
- notes:
  - 仅用于本地 DB tunnel，不作为远端 shell 工作入口
  - 优先复用现有 tunnel；若 repo 已通过 `scripts/run_top_union_ui_server.sh ensure` 建好 tunnel，不要重复起第二个
