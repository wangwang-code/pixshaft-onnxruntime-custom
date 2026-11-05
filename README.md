# pixshaft-onnxruntime-custom

为 [Pixiv-Shaft](https://github.com/CeuiLiSA/Pixiv-Shaft) 定制编译的轻量级 ONNX Runtime Android AAR。

## 🎯 核心优化与特性

1. **去除非必要架构**：仅保留生产机必备的 `arm64-v8a`，移除 `x86`, `x86_64`, `armeabi-v7a`。
2. **算子与类型裁剪**：基于 Pixiv-Shaft 当前离线漫画翻译用到的 3 个模型提取算子列表与类型缩减（`--enable_reduced_operator_type_support`），剔除官方全量库中 80%+ 的无关算子内核。
   - `comictextdetector.pt.onnx`（气泡/文本区域检测）
   - `encoder_model_quantized.onnx`（Manga-OCR 编码器）
   - `decoder_model_quantized.onnx`（Manga-OCR 解码器）
3. **老用户存量模型 100% 兼容**：**未开启** `--minimal_build`，完整保留原生 ONNX 图解析器。用户本地已下载的约 150MB `.onnx` 模型**无需重新下载或转换为 `.ort`**，无缝直接运行。
4. **云端全自动构建**：全部构建交由 GitHub Actions 容器环境，开发者本地无需配置任何 NDK/CMake，不污染 Pixiv-Shaft 主工程环境与发布列表。

## 📦 如何在 Pixiv-Shaft 中使用

1. 从本仓库的 **[Releases](../../releases)** 或 GitHub Actions Artifacts 下载最新的 `onnxruntime-android-custom.aar`。
2. 将其放入 Pixiv-Shaft 主工程的 `app/libs/onnxruntime-android-custom.aar`。
3. 在 `app/build.gradle` 中将依赖切换为本地 AAR：
   ```groovy
   // 替换原有的 implementation libs.onnxRuntime
   implementation files("libs/onnxruntime-android-custom.aar")
   ```
4. 代码无需做任何改动（`ai.onnxruntime.*` 包名和接口完全一致）。

## ⚙️ 手动触发新版本构建

在 GitHub Actions 页面选择 **Build Custom ONNX Runtime Android AAR** -> **Run workflow**：
- `ort_version`：指定 ONNX Runtime 上游版本（默认 `v1.24.3`）。
- `create_release`：构建成功后自动发布为 GitHub Release 并附带 AAR。
