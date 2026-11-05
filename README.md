# pixshaft-onnxruntime-custom

[![Maven Central](https://img.shields.io/maven-central/v/io.github.wangwang-code/onnxruntime-android-shaft)](https://central.sonatype.com/artifact/io.github.wangwang-code/onnxruntime-android-shaft)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

专为 [Pixiv-Shaft](https://github.com/CeuiLiSA/Pixiv-Shaft) 定制裁剪编译的超轻量 ONNX Runtime Android 运行库，已正式发布至 **Maven Central**。

---

## 🎯 核心优化与指标

| 指标 | 微软官方全量包 (`com.microsoft.onnxruntime`) | Shaft 定制裁剪包 (`onnxruntime-android-shaft`) | 优化幅度 |
| :--- | :--- | :--- | :--- |
| **AAR 文件体积** | **40.95 MB** | **4.56 MB** | **⬇️ 88.9%** |
| **arm64 `libonnxruntime.so`** | **24.63 MB** | **11.5 MB** | **⬇️ 53.3%** |
| **支持 ABI 架构** | arm64-v8a, armeabi-v7a, x86, x86_64 | **arm64-v8a 专属** | 精准匹配生产机架构 |
| **算子与类型剪裁** | 全量 ONNX 算子（数千个内核） | **精简并集算子（涵盖原图与量化融合算子）** | 剥离无用代码 |
| **存量模型兼容性** | 兼容 | **100% 兼容**（无需转 `.ort`，无需重新下载） | 零破坏迁移 |
| **依赖仓库分发** | Maven Central | **Maven Central 官方源（全球 CDN + 镜像加速）** | 零 GitHub 压力 |

---

## 🛠️ 技术关键点：算子并集与存量模型保障

Pixiv-Shaft 本地漫画离线翻译功能依赖 3 个模型（文字检测模型 + Manga-OCR Encoder/Decoder，约 150MB `.onnx`）。

- **图融合与原图算子冲突根因**：开启算子裁剪转换时，若开启图优化，LayerNorm 会被融合成 `SkipLayerNormalization`，导致基础算子 `ReduceMean`、`Pow`、`Erf` 被误裁；若完全关闭优化，运行时 ONNX Runtime 动态融合量化算子时又会缺少 `MatMulIntegerToFloat` Contrib 内核。
- **并集固化（Operator Union）**：本仓库通过对未优化原图与运行时融合计算图进行全面并集分析，将包含 `ReduceMean`、`Erf`、`MatMulIntegerToFloat`、`DynamicQuantizeMatMul`、`SkipLayerNormalization` 的完整算子配置固化至 [`required_operators.config`](./required_operators.config)，**使得存量用户的 150MB `.onnx` 原始模型能够零改动、零重新下载无缝平稳运行**。

---

## 📦 如何在项目中引入

由于已正式发布至 **Maven Central**，无需在 `build.gradle` 中添加任何自定义 Maven 源（如 JitPack 或 GitHub raw），直接使用项目标配的 `mavenCentral()` 即可。

### 1. `gradle/libs.versions.toml`

```toml
[versions]
onnxRuntime = "1.24.3-shaft-53b648c"

[libraries]
onnxRuntime = { module = "io.github.wangwang-code:onnxruntime-android-shaft", version.ref = "onnxRuntime" }
```

### 2. `app/build.gradle`

```groovy
dependencies {
    implementation libs.onnxRuntime
}
```

---

## ⚡ 自动化构建与极速发布机制

- **全自动 CI**：基于 GitHub Actions + Sonatype Central Portal API，构建产物自动经 GPG 免密签名、POM 元数据封装并直传发布到 Maven Central。
- **极速发布（~30 秒）**：内置 `reuse_cached_aar` 产物复用逻辑，在非算子变动的发布（如更新版本号、重试部署等）时，直接复用已验证的 AAR 产物，跳过漫长的 C++ 编译，**30 秒内即可完成全球发版**。
- **版本格式与防缓存**：支持 `1.24.3-shaft-{commit_hash}` 动态版本号，每次代码或算子变动自动递增，Gradle 天然免疫缓存错乱。
