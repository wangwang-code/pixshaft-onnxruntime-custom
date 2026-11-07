# pixshaft-onnxruntime-custom

[![Maven Central](https://img.shields.io/maven-central/v/io.github.wangwang-code/onnxruntime-android-shaft)](https://central.sonatype.com/artifact/io.github.wangwang-code/onnxruntime-android-shaft)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

专为 [Pixiv-Shaft](https://github.com/CeuiLiSA/Pixiv-Shaft) 定制裁剪编译的超轻量、高性能 ONNX Runtime Android 运行库，已正式发布至 **Maven Central**。

---

## 🎯 核心优化与指标对比

| 指标 | 微软官方全量包 (`com.microsoft.onnxruntime`) | 初期裁剪包 | 最新极限深度优化版 (`ae68273`) | 优化幅度 (相对官方) |
| :--- | :--- | :--- | :--- | :--- |
| **AAR 文件体积** | **40.95 MB** | 4.56 MB | **2.96 MB (3,109,385 字节)** | **⬇️ 92.8%** |
| **`libonnxruntime.so` (未压缩)** | **~44.0 MB** | 11.5 MB | **6.50 MB (6,811,736 字节)** | **⬇️ 84.5%** |
| **`.text` 纯机器指令区** | ~30.0 MB | 7.12 MB | **4.10 MB (4,202,760 字节)** | **⬇️ 86.3%** |
| **`libonnxruntime4j_jni.so`** | ~160 KB | 120 KB | **108 KB (110,840 字节)** | **⬇️ 32.5%** |
| **支持 ABI 架构** | 4 大架构全量打包 | arm64-v8a | **arm64-v8a 专属** | 精准匹配生产机架构 |
| **Android 15 兼容性** | 未完全适配 16 KB | 16 KB 对齐 | **100% 16 KB 页对齐 (`0x4000`)** | 官方 CI 逐库静态审计通过 |
| **存量模型兼容性** | 兼容 | 兼容 | **100% 兼容**（原图 `.onnx` 零破坏加载） | 无需离线转 `.ort` |
| **NEON 浮点推理提速** | 默认基准 | 默认基准 | **提升超 5 倍** (`-fno-math-errno`) | 消除 errno 惩罚分支 |

---

## 🛠️ 技术关键点：算子并集与存量模型保障

Pixiv-Shaft 本地漫画离线翻译功能依赖 3 个模型（ComicTextDetector 文字检测模型 + Manga-OCR Encoder/Decoder，约 150MB `.onnx`）。

- **图优化与原图算子并集（Operator Union）**：
  若在模型生成阶段完全开启图优化，LayerNorm 会被融合成内部核，导致原图基础算子（`ReduceMean`、`Pow`、`Erf`）在配置中被裁掉；反之，若完全关闭图优化，运行时 ONNX Runtime 动态融合量化算子时又会缺少 `MatMulIntegerToFloat` 或 `LayerNormalization(1)` 融合核。
- **动态算子链精准闭合**：
  本仓库对未优化原图与运行时图优化器（`LayerNormFusion`、`DynamicQuantizeMatMul`）的生成图进行完整并集覆盖，固化于 [`required_operators.config`](./required_operators.config)，**使得存量用户的 150MB `.onnx` 原始模型能够零改动、零重新下载无缝平稳运行**。

---

## ⚡ 极限抽脂技术全景

在 100% 保持存量 `.onnx` 原始模型加载能力的前提下，实施了针对 ELF 各节区物理构成的深度治理：

```
[官方 ~44 MB 原版]
       │  --disable_ml_ops / 算子类型收窄 / ThinLTO
       ▼
[初期裁剪 ~11.5 MB]
       │  -D__ONNX_NO_DOC_STRINGS (剥离 322 KB 废弃文档)
       │  -Wl,--pack-dyn-relocs=android (重定位节区 605KB -> 87KB)
       ▼
[中期基线 ~9.17 MB]
       │  -Oz 全局极限尺寸优化 (.text 暴跌 42.4%)
       │  -Wl,--icf=all (全量同构机器代码折叠)
       │  Version-Script 隔离 (JNI 符号收网私有化)
       ▼
[最终极限 6.50 MB SO / 2.96 MB AAR] 🚀
```

1. **全局尺寸优先指令生成 (`-Oz`) 与循环展开遏制 (`-fno-unroll-loops`)**：
   在 ORT 核心与 vcpkg 第三方静态依赖库（Protobuf、RE2、ONNX 等）中全局注入 `-Oz`，遏制编译器对多维张量循环的过度展开与贪婪内联，纯机器指令区（`.text`）由 **7.12 MB 暴跌至 4.10 MB (-42.4%)**。
2. **全量代码折叠 (`-Wl,--icf=all`)**：
   利用 LLD 链接器识别并合并因 C++ 模板在不同算子类型实例化时产生的完全同构机器码。
3. **ONNX 废弃英文文档彻底剥离 (`-D__ONNX_NO_DOC_STRINGS`)**：
   绕过 vcpkg triplet 默认屏蔽，双向穿透注入剥离宏，彻底拔除 `.rodata` 节区中沉睡的 322 KB 英文算子说明与参数字符串。
4. **Android 原生重定位压缩 (`-Wl,--pack-dyn-relocs=android`)**：
   利用 Android 6.0+ 原生支持的 SLEB128 压缩算法对动态重定位表进行打包，`.rela.dyn` 节区由 605 KB 骤降至 **87 KB (-85.6%)**。
5. **JNI 动态导出符号收网隔离 (`Version Script`)**：
   通过专属 `jni_export.lds` 将非 JNI 的 C++ 内部辅助符号全部标记为 `local`，阻止符号污染与符号表膨胀，`libonnxruntime4j_jni.so` 精简至 **108 KB**。
6. **数学库分支切除与 NEON 提速 (`-fno-math-errno`)**：
   消除浮点数学运算对标准库全局 `errno` 的分支保护，使 Clang 能够将向量计算直接映射到移动端高效 NEON 硬件流水线，**实测推理速度暴增超 5 倍**。
7. **异常展开表深度削减 (`-fno-asynchronous-unwind-tables`)**：
   剥离不必要的指令级异步展开表，精简 `.eh_frame` 节区。
8. **传统 ML 算子域外科手术切除 (`--disable_ml_ops`)**：
   彻底剔除 `ai.onnx.ml` 命名空间下所有传统机器学习算子（SVM、随机森林、KNN、ZipMap 等）。
9. **无引用 C/C++ 头文件无损剥离 ([`strip_aar_headers.py`](./scripts/strip_aar_headers.py))**：
   针对 Java/Kotlin 宿主环境，利用底层 ZIP 物理重构技术，零重压缩剔除 AAR 内 890 KB 的冗余 `headers/` 目录。
10. **全链路 Android 15 16 KB 页面对齐**：
    显式注入 `-Wl,-z,max-page-size=16384`，CI 内置自动化 ELF 检查，确保所有 SO 最大 `PT_LOAD` 对齐跨度达标。

---

## 📱 真机全链路冒烟与性能验证

该版本已在以下 3 台物理真机上通过完整全链路冒烟测试（含 1024x1024 大图真实矩阵前向推理）：

| 测试机型 | SoC 平台 | 系统版本 | 16 KB 对齐兼容 | 1024x1024 推理耗时 | 全链路状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **vivo iQOO Neo9** (`V2361A`) | 骁龙 8 Gen 2 | **Android 15** | ✅ **PASS** | **3.69 秒** | ✅ **100% 通过** |
| **realme Q2 5G** (`RMX2117`) | 天玑 800U | Android 12 | ✅ **PASS** | **7.27 秒** | ✅ **100% 通过** |
| **vivo Y73s** (`V2048A`) | 天玑 800U | Android 11 | ✅ **PASS** | **7.77 秒** | ✅ **100% 通过** |

---

## 📦 如何在项目中引入

本库已发布至 **Maven Central**，直接在项目中引入即可：

### 1. `gradle/libs.versions.toml`

```toml
[versions]
onnxRuntime = "1.24.3-shaft-+"

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

## ⚡ CI/CD 双流彻底解耦与发布机制

1. **日常构建流 (`.github/workflows/build-aar.yml`)**：
   - 专职负责编译与产物输出，包含深度 ccache 持久化缓存；
   - 自动执行 16 KB 页面对齐审计；
   - 绝不自动发布，确保每次试验构建零污染。
2. **独立发布流 (`.github/workflows/publish-central.yml`)**：
   - 手动按需触发，直接拉取验证通过的 Actions 产物，30 秒内完成 Maven Central 桩包生成、GPG 签名与 Sonatype 自动化上传发布。
