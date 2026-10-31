# Shizuku Patched

为 [thedjchi/Shizuku](https://github.com/thedjchi/Shizuku) 应用补丁，通过手动触发 GitHub Actions 构建 APK 并发布到 GitHub Releases。

## 补丁

- [main 补丁](patches/main/0001-remove-entering-shell-message.patch)：删除 rish 标准输出中的 `Entering shell...` 提示。
- [API 补丁](patches/api/issue178-complete.patch)：修复 stderr 管道、混合 TTY 重定向、EOF 和 Binder 回复，等待输出排空及子进程退出。

## 手动构建发布

打开 **Actions → Build Shizuku (Patched) → Run workflow**：

| 输入 | 用途 |
| --- | --- |
| `shizuku_ref` | 上游分支、tag 或提交 SHA，默认 `master` |
| `tag_name` | Release tag；留空自动生成 |
| `release_name` | Release 标题，默认 `Shizuku (Patched)` |
| `prerelease` | 是否标记为预发布，默认否 |

构建产物包含 APK、`SHA256SUMS` 和构建信息；成功后创建或更新 Release。

## APK 签名

默认使用 [emacs-keystore](emacs-keystore)，无需配置 secrets。keystore 和 alias 密码均为 `emacs1`，alias 为 `Emacs keystore`。仅能覆盖安装使用相同签名的版本。

自定义签名：在 **Settings → Secrets and variables → Actions** 中同时配置前三项 secrets：

| Secret | 内容 |
| --- | --- |
| `KEYSTORE` | JKS 或 keystore 文件的 Base64 内容 |
| `KEYSTORE_PASSWORD` | keystore 密码 |
| `KEYSTORE_ALIAS` | 签名密钥 alias |
| `KEYSTORE_ALIAS_PASSWORD` | 可选；留空使用 `KEYSTORE_PASSWORD` |

## 本地检查补丁

```bash
git clone --recurse-submodules https://github.com/thedjchi/Shizuku.git _builder/Shizuku
bash scripts/apply-patches.sh _builder/Shizuku
```
