#import "figures.typ"
#import "template.typ"
#show: template.init
#set document(
  author: "心悸媽咪",
  keywords: ("ECG", "Raspberry Pi 3B", "ESP32", "AF detect", "MLP", "Cat Boost", "Pan-Tompkins++"),
  title: [心悸寶貝--作品企劃書],
)

= Motivation and Objectives 
　　Cardiovascular diseases (CVDs) remain the leading cause of mortality worldwide, highlighting the critical need for effective continuous monitoring and early detection. Recent advances in wearable technologies have made electrocardiogram (ECG) monitoring increasingly accessible in daily life.

However, most existing wearable ECG systems are limited to short-duration recordings, typically around one minute, and provide only basic real-time analysis, such as heart rate estimation. While some devices support arrhythmia detection, their functionality is often primarily limited to detecting persistent atrial fibrillation (AF), without the capability to identify more complex or transient conditions.

Atrial fibrillation (AF) is commonly classified into paroxysmal, persistent, and permanent forms according to episode duration and termination behavior @markides2003atrial. Paroxysmal AF refers to episodes that terminate spontaneously, typically within several days, whereas persistent and permanent AF require clinical intervention or cannot be terminated. Due to its intermittent nature, paroxysmal AF is particularly challenging to detect using conventional short-duration monitoring systems, and such episodes are therefore frequently missed. This limitation is critical, as early detection of transient arrhythmias and comprehensive cardiovascular risk assessment are essential for timely medical intervention and long-term disease prevention.

Therefore, we propose an integrated framework that enables long-term ECG monitoring and incorporates two components: an atrial fibrillation detection module and a cardiovascular disease prediction model. The AF detection module focuses on identifying both paroxysmal and persistent atrial fibrillation from continuous ECG signals, while the cardiovascular disease prediction model provides a comprehensive assessment of cardiovascular conditions based on extracted features. Our proposed system offers a more complete solution for both real-time arrhythmia detection and cardiovascular risk evaluation.

= System Design
　　心血管疾病長期位居全球主要死因之一，然而多數相關疾病在早期階段缺乏明顯症狀，患者往 往在臨床症狀明顯或病情惡化後才就醫，錯失最佳介入時機。對於高齡者、心血管疾病高風險族群與術後追蹤患者而言，若能在日常生活中長時間、低負擔地進行 ECG 監測，將有助於提早發現異常與降低急性事件風險。現有解決方案大致可分為三類。第一類為醫療院所內 ECG 檢查，量測品質高，但成本較高且不利於長時間日常監測；第二類為 Holter monitor，雖可長時間量測，但設備取得與使用門檻較高；第三類為市售智慧穿戴式裝置，雖具方便性，但多偏向短時間量測、心率監測或有限事件偵測，缺少完整的特徵分析、心臟疾病風險評估與後續就醫輔助功能。

因此，本作品解決了以下問題：
+ 如何在低成本穿戴式架構下取得可用的 ECG 訊號。
+ 如何於邊緣運算裝置完成即時 ECG 訊號分析，不依賴大型雲端運算資源。
+ 如何將原始高維 ECG 訊號轉換為具生理意義且可解釋的健康資訊。
+ 如何讓量測結果不只停留於監測，而能進一步支援健康管理與就醫判斷。

= 設計理念與創新價值
　　本作品之設計理念不僅在於提供 ECG 量測，而是希望將原始心電訊號即時轉換為可解讀之健康風險資訊。考量日常穿戴裝置需具備低延遲、低功耗、隱私性與可攜性，本作品採用邊緣端即時分析架構，避免大量生理資料長時間上傳雲端所帶來之傳輸負擔與個資風險。

　　相較於現有產品，本作品的差異化重點如下：
+ 支援較長時間 ECG 監測，而非僅限於短時間量測或單次操作。
+ 同時提供心臟疾病風險評估與心房顫動 (AF) 偵測，功能面向較完整。
+ 整合靜態與運動狀態下之 ECG 特徵，使風險分析更貼近日常情境。
+ 提供 ECG 圖形匯出功能，便於異常發生時保存量測紀錄並作為就醫參考。
+ 採用輕量化自訓練 AI 模型，可於邊緣裝置執行，不需大型伺服器支援。

　　本作品之新穎性不在於單一感測元件或單一演算法，而在於完整的跨域整合：從生理訊號擷取、訊號處理、邊緣 AI 推論、風險資訊視覺化，到就醫輔助資料匯出，形成具實務價值的整體解決方案。

= 潛在市場、產業需求與應用價值
　　本系統對應的潛在市場包括高齡健康管理、心血管疾病患者長期追蹤、遠距照護、居家術後觀察與一般民眾之個人健康監測。其應用價值主要體現在以下幾方面：
+ 預防醫學：協助使用者更早察覺異常節律或心血管風險。
+ 遠距照護：提供結構化 ECG 特徵與風險資訊，減少單純口述症狀之不確定性。
+ 就醫輔助：異常時可匯出 ECG 圖形，供醫師觀察判讀。
+ 邊緣部署：不需高階雲端算力即可完成分析，具低成本落地潛力。

= 系統架構與整體實作規劃
　　本作品硬體架構由 AD8232 ECG 感測模組、ESP32 與 Raspberry Pi 3B 組成。AD8232 負責單導程 ECG 訊號擷取，ESP32 負責資料取樣與傳輸，Raspberry Pi 3B 則負責訊號處理、特徵萃取、AF 偵測、風險推論與結果整合。此架構可在維持系統完整性的前提下兼顧成本、可攜性與邊緣部署需求。

#figure(
  // figures.module_overview,
  image("pics/module_overview/module_overview.jpg"),
  caption: [作品模組全覽圖]
) <module_overview>

　　而軟體流程的部分可分為四個主要模組：
+ 訊號處理：基於 Pan-Tompkins++ 演算法實作 R-peak 偵測，並加入 ST segment 相關分析 @imtiaz2024pan。
+ 特徵萃取：由 R-peak 計算 MaxHR、Oldpeak、ST_Slope、RestingECG 等特徵，提供風險評估模型預測。
+ AF 偵測：以 RR interval 為基礎，使用 RdR map 與 non-empty cell 計數進行判斷。
+ 風險評估：以 CatBoost 為核心，根據使用者輸入資料是否完整，自動切換模型進行預測。

#figure(
  image("pics/system_flow.png"),
  caption: [系統運作流程圖]
) <system_flow>

　　在模型部署方面，本作品保留兩組 CatBoost 模型。8-feature 模型作為部署版本，適用於僅有基本資料與 ECG 特徵的情況；10-feature 模型則於使用者同時提供 Cholesterol 與 FastingBS 等額外健康資料時啟用，以獲得較高辨識效能。兩組模型大小約 650KB 等級，可於邊緣裝置進行推論。

= Feature Extraction

== Preprocessing and Filters

Before extracting features, raw ECG signals must undergo noise filtering to ensure the accuracy of subsequent feature calculations.
Our project initially utilized a 5-12 Hz filter to process the QRS segment. However, this frequency band over-suppressed the T-wave, causing the false removal of genuine ST depression or ST elevation features.
To address this, we designed an independent 0.5-35 Hz filtering interval specifically for the ST Slope calculation, preserving complete and genuine ST segment features.

== Feature Extraction Methods

Our processing pipeline primarily extracts four key features: Maximum Heart Rate, Oldpeak, ST Slope, and Resting Electrocardiogram (RestingECG). The R-peak measured by `Pan-Tompkins++` serves as the reference point for calculating all subsequent features (like heart rate and segment windows). The extraction mechanisms, challenges, and optimization processes are detailed below.

=== Maximum Heart Rate

#h(2em) *Definition*: The maximum heart rate achieved during the measurement period, typically yielding a numeric value between 60 and 202.

*Extraction Method*: By utilizing the `Pan-Tompkins++` algorithm, we were able to detect R-peaks, which are subsequently converted into the heart rate.

=== Oldpeak

#h(2em) *Definition*: Oldpeak represents the ST depression caused by activity in comparison to rest. A value > 0 may indicate angina, while a value < 0 is potentially related to myocardial infarction.
Oldpeak quantifies the absolute displacement of the ST segment relative to the electrically neutral PR baseline. In a healthy heart, the ST segment should be perfectly flush with the PR segment. When the heart muscle is stressed or deprived of oxygen (especially during the exercise phase of stress testing), the ST segment will deviate.

*Extraction Method*: It is calculated based on relative R-peak positions using the following formula:
$ "Oldpeak" = V_("ST level") - V_("PR baseline") $
Here, _PR baseline_ is the average potential between 200 ms and 120 ms prior to the R-peak, and _ST level_ is the average potential between 100 ms and 160 ms after the R-peak. 
This timing window is crucial for accurately measuring the ST segment's displacement, and is suggested by multiple medical literature sources. @hu2015morphological @zong2014real @campero2022interpretable

=== ST Slope

#h(2em) *Definition*: The slope of the peak exercise ST segment, classified into three categories: Up, Flat, or Down. While the Oldpeak measures the absolute drop or rise of the ST segment, the ST_Slope measures its morphological trajectory. How the ST segment behaves dynamically over time is a critical predictor of coronary artery disease.

*Algorithmic Execution*: Instead of taking a single average, the algorithm extracts all voltage data points within the defined ST Window and applies an Ordinary Least Squares linear regression to find the line of best fit:
$ V(t)=m t+b $
Here, t represents time, V(t) is the voltage, b is the y-intercept, and m is the computed slope.

*Diagnostic Classification*: We categorize the ST slope into three categories: Up (upsloping), Flat, or Down (downsloping). 
- _Upsloping_: $m > 0.5 V/s$. (Often seen in normal, healthy exercise responses, even if slight ST depression is present).
- _Downsloping_: $m < −0.5 V/s$. (A highly specific indicator of severe ischemic heart disease).
- _Flat_: $abs(m) <=0.5 V/s$. (Also a strong indicator of ischemia, as a healthy ST segment should naturally slope upward into the T-wave).

=== Resting Electrocardiogram (RestingECG)

#h(2em) *Definition*: RestingECG is categorized into Normal, ST (having ST-T wave abnormality, such as T-wave inversion or ST elevation/depression > 0.05 mV), and LVH (showing probable or definite left ventricular hypertrophy by Estes' criteria).

*T-wave Difficulties*: T-waves are low-frequency, low-amplitude signals that are highly susceptible to baseline wandering, which is a type of low-frequency noise primarily caused by the user's respiration and minor electrode movements.

*Solution*: 
+ Initial Attempt: To stabilize the T-wave for accurate inversion detection, we integrated a Wavelet Transform-based Baseline Wandering Removal algorithm (utilizing the open-source py-bwr library).
+ The Trade-off: While BWR successfully clarified the T-wave inversion morphology, testing revealed a critical flaw: the mathematical transformation aggressively warped the raw voltage levels, severely degrading the accuracy of ST elevation/depression measurements. Overall model accuracy dropped from 92.39% without BWR to 83.42% with global BWR.
+ Final Pipeline: To resolve this, the system employs a bifurcated processing strategy. Baseline correction is applied only in parallel streams specifically evaluating T-wave morphology, while the original minimally filtered signal (0.5–35 Hz) is strictly preserved for calculating absolute ST segment offsets.

#figure(
  image("pics/TWave.png"),
  caption: [The bifurcated processing strategy for T-wave morphology correction.],
) 

#h(2em) *LVH Difficulties*: And for LVH, since it requires precordial leads—specifically V1, V5, and V6, we implemented a practical software-based workaround. During the initial profile registration on our web interface, the system proactively prompts users to input their known medical history, including any prior LVH diagnoses. This approach ensures that the machine learning model still receives the complete data array required for a comprehensive risk assessment.

=== Validation: 
We validated the accuracy of the STE/STD feature by comparing it with the European ST-T Database. The accuracy of recognizing ST Elevation/Depression was found to be 99.16% and recall of ST Elevation/Depression was 91.6%.

#figure(
  image("pics/ST_CM.png", width: 70%),
  caption: [Confusion matrix for ST Elevation/Depression recognition.],
)

// Maybe also plot with annotations
#figure(
  image("pics/Plot_with_annotations.png"),
  caption: [Examples of ECG signal with features annotated.],
)

= 模型訓練流程與技術
　　本作品之心臟疾病風險評估模型開發流程包含：重建完整標註之公開心臟疾病資料集、進行 label encoding 與 mean imputation、執行 random oversampling、進行 80/20 holdout split、透過 cross validation、hyperparameter optimization 與 model comparison 選定最佳模型，最後完成 performance evaluation、model selection 與 threshold tuning，得到最終部屬的模型，此模型預測結果於公開心臟疾病資料集上可達約 96.6% accuracy 與 97.1% recall。相關方法與研究背景可參考 @hamid2025catboost 與 @wan2025review。

#figure(
  image("pics/model_training.png"),
  caption: [模型開發與訓練流程圖]
) <model_training>

= AF 偵測方法與驗證
　　AF 偵測部分參考公開文獻之 RR interval 方法，以 128-beat window 為基礎，將 RR 與 dRR 建立為 RdRmap，再以 25ms grid 統計 non-empty cells (NEC) 進行判斷。此方法不需大型深度學習模型即可完成節律異常辨識，具低計算量與邊緣部署優勢 @lian2011af。

#figure(
  image("pics/af_detect.png"),
  caption: [心房顫動 (AF) 偵測示意圖]
) <af_detect>

　　在驗證方面，AF 偵測部分參考公開文獻之 RR interval 方法，並於 MIT-BIH atrial fibrillation database 的 128-beat 驗證設定下達約 95.7% 準確率，完成文獻方法之重現與驗證 @lian2011af。上述結果顯示，本作品在維持邊緣部署可行性的同時，仍具備良好的節律異常辨識能力。

= 量化成果與效能驗證
　　本作品目前主要量化成果如下：
- 我們的風險預測 AI 模型於公開心臟疾病資料集上可達約 96.6% accuracy 與 97.1% recall。
- AF 偵測：在 MIT-BIH atrial fibrillation database 的 128-beat 驗證設定下達約 95.7% 準確率。
- 模型大小：約 650KB 等級，符合邊緣端部署需求。

= 成品展示
#figure(
  image("pics/frontend.png"),
  caption: [前端介面]
) <frontend>

= 與現有技術或市售產品之比較
　　相較於多數市售穿戴式裝置，本作品的優勢並非單一規格領先，而在於整體功能串接的完整性。重點差異如下：
+ 可進行較長時間 ECG 監測，而非僅限於短時間操作。
+ 提供 ECG 特徵分析、心臟疾病風險評估與心房顫動 (AF) 偵測，而不只是心率顯示。
+ 可於異常當下匯出 ECG 圖形，作為後續就醫輔助。
+ 採用邊緣端即時分析架構，兼顧低延遲與較高資料隱私性。

#figure(
  table(
    columns: (auto, 1fr, 1fr),
    align: (center, center, center),
    stroke: 0.5pt,
    fill: (_, row) => if row == 0 { luma(230) } else { none },
    [*比較項目*], [*本作品*], [*多數市售穿戴式裝置*],
    [ECG 量測型態], [可支援較長時間連續監測], [多以短時間主動量測為主],
    [分析內容], [ECG 特徵分析+風險評估+AF 偵測], [多以心率顯示或單一事件提醒為主],
    [使用方式], [穿戴式連續量測], [需手指持續接觸電極],
    [量測情境], [支援靜態/運動狀態], [僅支援靜態狀態],
    [運算架構], [邊緣端即時推論，降低傳輸與隱私風險], [多依產品設計而異，未必具完整在地推論能力]
  ),
  caption: [與市售產品之功能比較]
) <comparison>

= 場域應用與使用情境
　　本作品適合應用於居家健康管理、高齡照護、慢性病患者追蹤與術後健康觀察等場域。對一般使用者而言，系統可作為較長時間的日常心電監測與早期異常提醒工具；對照護者或醫療輔助人員而言，則可提供更具結構性之 ECG 特徵與風險資訊，作為後續觀察、追蹤或就醫判斷的參考。

在實際應用情境中，使用者可於日常生活中佩戴裝置進行 ECG 量測，系統於邊緣端即時完成訊號處理、特徵萃取與風險分析，並透過介面提供心率、ECG 波形、AF 偵測結果與心臟疾病風險提示。當系統偵測到異常節律或較高風險時，可提示使用者進一步觀察或及早就醫，提升健康管理之主動性與即時性。

此外，本作品亦提供 ECG 圖形匯出功能。當使用者於日常生活中感到不適，或系統偵測到異常節律與較高風險時，可即時保存並匯出當下之心電圖圖形與相關資訊，於後續就醫時提供醫師作為觀察與判讀之輔助參考，提升日常監測資料在實際醫療情境中的應用價值。

相較於僅能短時間量測的市售裝置，本作品更強調「連續監測 + 特徵分析 + 風險資訊」的整合能力；低成本、可攜性與非醫療場域使用之便利性。因此，本作品並非取代臨床診斷，而是作為前端輔助工具，協助使用者更早辨識心臟健康風險，並提升日常健康管理效率。

= 成本、可行性與整合難度
　　本作品採用市面可取得之模組進行整合，具備原型實作上的可行性。以現行原型估算，主要硬體成本集中於 ECG 感測模組、微控制器、邊緣運算設備與電源模組。由於本系統採用單導程 ECG 架構與輕量化模型，不需高階 GPU 或大型伺服器，即可完成系統運作，因此具備較低導入門檻。

然而，本作品的難點不在於單一硬體元件，而在於整體整合。感測器、訊號取樣、資料傳輸、邊緣運算、資料庫、前端顯示與就醫輔助匯出功能必須穩定串接，這也是本作品的重要技術價值之一。這種跨硬體、訊號處理與 AI 的整合難度，正符合跨域智慧系統競賽對整體完成度的期待。

= 技術限制、風險與可信度說明
　　為提高作品可信度，本作品亦主動說明現階段限制如下：
+ 目前主要使用單導程 ECG，與醫療級多導程系統相比，資訊量仍有限。
+ 心臟疾病風險評估模型主要基於公開資料集驗證，未來仍需更多真實使用場景驗證。
+ 心房顫動 (AF) 偵測目前以公開資料庫與原型資料進行驗證，未來仍可補充更大規模使用者測試。
+ LLM 健康建議若作為後續功能，僅應視為輔助性資訊，不應取代醫師診斷。
+ 本系統定位為健康管理與早期警示工具，而非醫療診斷設備。

= 未來發展
　　本作品目前已完成穿戴式 ECG 量測、邊緣端訊號分析、AF 偵測與心臟疾病風險評估等核心功能，後續可朝以下方向持續擴充與優化。

首先，在量測能力方面，可由目前單導程 ECG 擴展至更多導程或整合更多生理感測資訊，例如血氧、血壓、活動量與睡眠狀態，以提升風險評估之完整性。

其次，在模型與驗證方面，未來可進一步蒐集更多真實使用情境資料，強化模型在不同族群與日常環境下之泛化能力，並提升異常事件偵測之穩定性與可信度。

未來亦可朝更低功耗、更小型化與更高整合度之穿戴式系統發展，降低設備體積與使用負擔，提升長時間佩戴與實際落地之可行性。透過上述方向，本作品有機會由原型系統進一步發展為具實務應用價值之智慧健康產品。

= 結論
　　本作品「心悸寶貝」以單導程 ECG 感測、邊緣運算與輕量化 AI 為核心，建構一套可於日常生活中長時間運作之穿戴式心臟健康監測系統。相較於多數市售穿戴式裝置，本作品更強調「連續監測 + ECG 特徵分析 + 風險資訊 + ECG 匯出」的整合能力，並以具體量化結果驗證其可行性。

本作品不以取代臨床診斷為目標，而是定位為醫療前端輔助工具，協助使用者進行日常健康管理、早期異常預警與後續就醫準備。

#bibliography(
  "works.bib",
  style: "ieee",
  title: [十六、 參考文獻],
)
