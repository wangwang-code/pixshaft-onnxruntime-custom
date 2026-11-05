# pixshaft-onnxruntime-custom

为 [Pixiv-Shaft](https://github.com/CeuiLiSA/Pixiv-Shaft) 定制编译的轻量级 ONNX Runtime Android AAR。

## 🎯 核心优化与特性

1. **去除非必要架构**：仅保留生产机必备的 `arm64-v8a`，移除 `x86`, `x86_64`, `armeabi-v7a`。
2. **算子与类型裁剪**：基于 Pixiv-Shaft 离线漫画翻译的 3 个模型（气泡检测 + Manga-OCR 编解码器），按照原始计算图提取算子与类型（`--enable_reduced_operator_type_support`），剔除官方全量库中 80%+ 的无关算子内核。
3. **老用户存量模型 100% 兼容**：关闭图融合并保留原生 ONNX 图解析器，完整保留 LayerNorm (`ReduceMean`, `Pow`, `Sqrt` 等) 与 GELU (`Erf`) 基础算子，用户本地已下载的约 150MB `.onnx` 模型**无需重新下载或转换为 `.ort`**，无缝直接运行。
4. **标准 Maven 仓直连**：构建完成后自动将标准 Maven 结构与 POM 部署至本仓库的 `mvn-repo` 分支。

## 📦 如何在 Pixiv-Shaft 中使用

1. 在项目根目录的 `build.gradle` 的 `allprojects.repositories` 中添加本仓库的 Maven 源：
   ```groovy
   maven {
       url = 'https://raw.githubusercontent.com/wangwang-code/pixshaft-onnxruntime-custom/mvn-repo/'
       content { includeGroup 'com.microsoft.onnxruntime' }
   }
   ```
2. 在 `gradle/libs.versions.toml` 中使用标准依赖：
   ```toml
   [versions]
   onnxRuntime = "1.24.3-custom"

   [libraries]
   onnxRuntime = { module = "com.microsoft.onnxruntime:onnxruntime-android", version.ref = "onnxRuntime" }
   ```
3. 在 `app/build.gradle` 中恢复最干净的标准引入：
   ```groovy
   implementation libs.onnxRuntime
   ```
   无需写任何 `ivy`，无需写 `@aar`，体验与官方依赖完全一致。
