# Shizuku Patched

参考 [wezterm-patched](https://github.com/kkkykin/wezterm-patched) 的构建仓库形式，在 GitHub Actions 中检出 [thedjchi/Shizuku](https://github.com/thedjchi/Shizuku)，应用本地补丁后构建 APK 并发布到本仓库的 GitHub Releases。

**仅支持手动触发**：没有 push、pull_request 或 schedule 构建。

## 补丁

- [patches/main/0001-remove-entering-shell-message.patch](patches/main/0001-remove-entering-shell-message.patch)：删除主库的 `System.out.println("Entering shell...");`，避免 rish 的标准输出混入提示语。
- [patches/api/pr534-with-stderr-drain.patch](patches/api/pr534-with-stderr-drain.patch)：原样保存提供的补丁，在 `api/` 子模块中修正 stderr 管道，并等待 stdout、stderr 都传输完毕后退出。

主库与 API 补丁分别在对应的 Git 仓库中应用。API 使用主库锁定的子模块提交；已应用的补丁会跳过，普通应用失败时尝试三方合并，冲突会中止构建。

## 手动构建发布

将本仓库提交并推送到 GitHub 的默认分支后，打开 **Actions → Build Shizuku (Patched) → Run workflow**：

| 输入 | 用途 |
| --- | --- |
| `shizuku_ref` | 上游分支、tag 或提交 SHA，默认 `master` |
| `tag_name` | Release tag；留空自动生成 |
| `release_name` | Release 标题，默认 `Shizuku (Patched)` |
| `prerelease` | 是否标记为预发布；仅改变 Release 标记 |

工作流使用 Java 21，安装上游要求的 Android SDK、Build Tools、NDK 及 CMake，再运行 `:manager:assembleRelease`。构建成功后上传 APK、`SHA256SUMS` 和构建信息到 Actions artifacts，并在本仓库创建或更新 Release。Release 说明包含主库与子模块提交、补丁应用结果、补丁及 APK 的 SHA256。

当前上游使用整数 `compileSdk = 37` 和 AGP 8.11。SDK 安装脚本校验 Google 平台压缩包的校验和，将 Android 37.0 安装为旧插件可识别的 `android-37` 目录及整数版本元数据。

## APK 签名

没有配置签名 secrets 时，工作流自动生成调试密钥，构建并发布可安装的 release APK。**每次生成的密钥不同**，因此不能直接覆盖安装其他签名的版本，也不能保证覆盖上一次构建；需要长期使用和覆盖升级时，请配置固定密钥。

在仓库 **Settings → Secrets and variables → Actions** 中设置：

| Secret | 内容 |
| --- | --- |
| `KEYSTORE` | JKS 或 keystore 文件的 Base64 内容 |
| `KEYSTORE_PASSWORD` | keystore 密码 |
| `KEYSTORE_ALIAS` | 签名密钥 alias |
| `KEYSTORE_ALIAS_PASSWORD` | 签名密钥密码 |

四项都配置后自动使用自定义签名；只配置部分会报错。签名文件只在 runner 中临时生成，构建结束后删除。上游 APK 的签名密钥不会随源码提供，使用自己的密钥不能覆盖安装上游签名的 APK。

## 本地检查补丁

无需编译即可验证补丁：

```bash
git clone --recurse-submodules https://github.com/thedjchi/Shizuku.git _builder/Shizuku
bash scripts/apply-patches.sh _builder/Shizuku
```

补丁按 `patches/main/` 和 `patches/api/` 下的文件名顺序应用，先 `*.patch` 后 `*.diff`。
