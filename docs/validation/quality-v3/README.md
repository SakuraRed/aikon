# 单环境图像质量门禁

本轮落实用户已明确的CI纠正：只使用一个Ubuntu24.04基础环境，不再运行Windows/Linux矩阵。研发宿主的本地检查不是第二套CI，也不再做跨平台像素一致性作为质量结论。

最重要的状态区分：**检测器的正负控制通过，六张作品仍然被用户拒绝。** [判定记录](artwork-verdicts.json)绑定实际六份SVG的哈希，不能由自动门禁升级为用户接受。

## 当前确实检查了什么

| 检查 | 实际证据 | 尚不能证明 |
| --- | --- | --- |
| 胶囊眼形 | [轮廓及宽度剖面](../capsules-v3/README.md)：r1两眼通过，旧DeepSeek short/full四眼均更符合椭圆，失败；16解析正负控制符合预期 | 仰头正确、身份正确、99%相似 |
| 边缘像素 | [方法及真实注入图](../edges-v3/README.md)：AA/阶梯、异色边、材料交界、局部彩边和alpha缺口分开检查，13正负对照符合预期 | 所有尺寸通用、所有边缘差异都必然是污染 |
| 局部彩边 | 16像素短段污染未触发全局均值，但局部连通残差捕获；阈值在负例前由正例观察冻结 | 低于阈值的微弱或零散缺陷全都可检出 |
| 真实上色回归 | 8个已保存参考/坏例复跑，保留full圈注斑驳拒绝和short轻纹理尚未稳定区分的事实 | 新六图全部材料无噪声或自然光泽已成立 |
| SVG/像素基础合同 | 静态向量、正常渐变/AA、真实眼深度、透明度、缓存污染和两版差异的正负控制 | 仅有差异就等于正确short/full，文件名叫眼睛就形状正确 |

旧DeepSeek边缘诊断在顶部裁切处有4像素局部差异提示。它只反映native与超采样面积重建的差异，尚不能归因成真实杂色。该旧图仍为用户拒绝，不能借“未找到更多边缘问题”逆转判定。

## 执行范围

`tools/run_image_quality.py`只选择6个与当前质量验证相关的测试模块，不再默认运行全仓库功能测试，也不重绘全部历史头像。原版本管理、CLI等开发测试仍保留在仓库，未被删掉。

```text
python tools/run_image_quality.py --mode tests --output .local/quality
python tools/run_image_quality.py --mode audit --output .local/quality
python tools/run_image_quality.py --mode summary --output .local/quality --artifact-outcome not_attempted
```

每个worker单独50秒硬上限，保留进程树回收。安装也有明确时限，图像依赖沿用hash锁定版本。CI单job运行tests和audit，再尝试上传证据并发布日志/摘要；账号存储配额不足会明确记录上传失败，不把它伪装成成功。

## 防止过时的绿灯

阶段开始立即将旧结果标为running，绑定本次invocation、实际输入文件指纹和GitHub run/attempt。早期import异常、超时或输入变动都不能沿用上轮pass。摘要验证上下文及监督失败记录；6条拒绝记录必须恰好对应3个主体×2个profile的不同规范路径，不能用同一文件凑数。

独立审查发现并修复了：旧结果复用漏洞；实际边缘审计代码/fixtures未触发CI的路径遗漏；0.5单像素退化mask造成NaN的情况；拒绝作品记录覆盖不足。另有负控防止删除一个合法边缘正例后静默缩小测试范围。

## 本地实际结果

76项针对性测试通过，14.448秒；独立参考审计通过，11.989秒。原始记录见 [local-tests.json](local-tests.json)、[local-audit.json](local-audit.json) 和 [local-summary.json](local-summary.json)。实际图像/掩膜位于本地 `.local/quality-v3/final/`，可按以上入口重建；胶囊和边缘研究目录也保存了可直接查看的证据。

这些pass的含义是检查器对已知正负例给出预期结果。`artwork_acceptance`仍为`rejected_by_user`，`reference_similarity_99`以及仰头/身份仍为`not_assessed`。远端CI是否完成须以对应run为准，不能由workflow文件存在推断。

工程选择的实际Jev请求/响应见本目录 `decision-request.json` / `decision-result.json`；它支持单Ubuntu和区分检测器/作品状态的路线，不是图像成功率或用户授权。
