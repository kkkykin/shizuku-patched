# 补丁目录

`main/` 中的补丁相对于 Shizuku 主库根目录，`api/` 中的补丁相对于 API 子模块根目录。

- `main/0001-remove-entering-shell-message.patch`：只删除进入 shell 前写到 stdout 的提示。
- `api/pr534-with-stderr-drain.patch`：来自 `/tmp/shizuku-pr534-eHHoqc/pr534-with-stderr-drain.patch`，保留原始内容。

当前验证基线：

- Shizuku `master`：`15ade0e40042dc72f0e502d50b4cb16e3a19095e`。
- 主库锁定的 API：`37ebcd3e45edf1d68975c70dd199350b434161f7`。

补丁应用与重复应用检查在这些提交上验证；完整 Android 编译与 APK 运行验证由手动 Actions 构建及实机使用完成。
