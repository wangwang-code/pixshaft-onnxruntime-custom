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

## ⚡ 全栈深度抽脂与 Android 15 合规加固

在 100% 保持存量 `.onnx` 原始模型加载能力的前提下，实施系统性抽脂优化：

1. **传统 ML 算子域外科手术切除 (`--disable_ml_ops`)**：
   彻底剔除 `ai.onnx.ml` 命名空间下所有传统机器学习算子（SVM、随机森林 TreeEnsemble、KNN、线性回归、ZipMap 等），消除纯死代码。
2. **稀疏张量与 Optional 类型引擎剥离 (`DISABLE_SPARSE_TENSORS` / `DISABLE_OPTIONAL_TYPE`)**：
   针对移动端漫画翻译纯密集张量（Dense Tensor）场景，彻底关闭无用的稀疏矩阵存储调度与 Optional 包装。
3. **移动端无用 ARM SVE 向量扩展切除 (`onnxruntime_USE_SVE=OFF`)**：
   切除移动端 Linux 用户态未开放的 SVE / SVE2 向量汇编内核，回退至成熟高能效的 NEON / XNNPACK 硬件流水线。
4. **Arm KleidiAI 冗余微内核剥离 (`--no_kleidiai`)**：
   针对移动端 Cortex-A 系列处理器，全面收敛至高能效的 XNNPACK / NEON 汇编硬件流水线，剥离桌面与服务器端的 KleidiAI SVE/SME 静态库。
5. **LLVM ThinLTO 全局跨模块死代码消除 (`--enable_lto`)**：
   在全程序 AST 级别跨编译单元消除从未被调用的底层重载与虚函数表。
6. **LLD 链接器相同代码安全折叠与展开抑制 (`-Wl,--icf=safe` / `-fno-unroll-loops`)**：
   折叠模板实例化机器码，并遏制 Clang 对张量多重循环的暴力展开。
7. **算子精度定点收敛 (`required_operators.config`)**：
   将 `ConvTranspose`、`Erf`、`LeakyRelu` 等算子输入严格锚定为 `float`，剔除 `double` 与 `half` 的多余模板展开。
8. **无引用 C/C++ 头文件无损剥离 ([`strip_aar_headers.py`](./scripts/strip_aar_headers.py))**：
   针对 Kotlin/Java JNI 纯净宿主环境，在打包期利用底层 ZIP 记录重构技术，零重压缩直接剔除 AAR 内 890 KB 的 `headers/` 目录。
9. **全链路 Android 15 16 KB 页面对齐与 CI 审计**：
   显式注入 `-Wl,-z,max-page-size=16384`，并在 CI 中内建自动化 ELF `p_align` 断言，确保所有原生动态库对齐跨度均为 `0x4000`。

---

## 📦 如何在项目中引入

由于已正式发布至 **Maven Central**，无需在 `build.gradle` 中添加任何自定义 Maven 源（如 JitPack 或 GitHub raw），直接使用项目标配的 `mavenCentral()` 即可。

### 1. `gradle/libs.versions.toml`

```toml
[versions]
# 使用 Gradle 动态版本语法，自动解析并追踪最新的 SHA 构建版本，无需硬编码特定的 commit hash
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

## ⚡ CI/CD 双流彻底解耦与极速发布机制

为了保护 Maven Central 上传额度并确保发布的 AAR 100% 经过真机与功能验证，本项目与 `ncnn-android-shaft` 保持统一的工程架构，实施双流彻底解耦：

1. **日常构建流 (`.github/workflows/build-aar.yml`)**：
   - **专职负责编译与产物输出**：按 `required_operators.config` 算子并集编译 arm64-v8a AAR，并输出 `onnxruntime-android-custom` Actions Artifact；
   - **深度 ccache 加速**：注入 `CCACHE_COMPILERCHECK=content`、`CCACHE_NOHASHDIR=1`、`CCACHE_BASEDIR` 与 `CCACHE_SLOPPINESS`，并在 `build_params` 注入 `--use_cache` 与 CMake 编译器启动器，彻底规避跨 Runner 绝对路径导致的缓存失效，使得重复增量构建时间大幅缩减；
   - **绝不自动上传**：杜绝每次试验性构建浪费 Maven Central 发布配额与版本号污染。

2. **独立发布流 (`.github/workflows/publish-central.yml`)**：
   - **手动按需触发 (`workflow_dispatch`)**：输入指定版本号（如 `1.24.3-shaft-xxxx` 或缺省 `auto`）；
   - **零等待发布**：自动拉取最新一次（或指定 Run ID）已验证成功的 AAR 产物，跳过漫长的 C++ 编译，在 30 秒内完成 POM 生成、JavaDoc/Sources 桩 Jar 封装、SHA1/MD5 校验和计算、GPG 免密签名与 Sonatype Central Portal API 上传。
